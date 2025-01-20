import spacy
import streamlit as st
from typing import List, Dict, Tuple
import subprocess
import sys
from ai_checker import AIChecker
import re

@st.cache_resource
def load_model():
    """Ładuje model spaCy"""
    try:
        return spacy.load("pl_core_news_sm")
    except OSError:
        # Instalujemy model jeśli nie jest zainstalowany
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "pl_core_news_sm"])
        return spacy.load("pl_core_news_sm")

def find_phrases(text: str, phrases: List[str], nlp) -> Tuple[List[Dict[str, str]], Dict[str, int]]:
    """
    Znajduje frazy w tekście używając SpaCy i GPT-4-mini.
    Łączy wyniki z obu źródeł i usuwa duplikaty.
    
    Returns:
        Tuple[List[Dict[str, str]], Dict[str, int]]:
            (Lista unikalnych wariantów, Statystyki)
    """
    # Inicjalizacja AI Checker
    ai_checker = AIChecker()
    
    # Lista wszystkich znalezionych wariantów
    all_variants = []
    
    # Statystyki
    stats = {
        "total": 0,
        "dokładne": 0,
        "odmiana": 0,
        "rozdzielone": 0,
        "przestawione": 0,
        "rozszerzone": 0,
        "lematyzacja": 0
    }
    
    # Zbiór do śledzenia unikalnych fragmentów
    unique_fragments = set()
    
    # Dla każdej frazy
    for phrase in phrases:
        # 1. Szukamy przez SpaCy (lematyzacja)
        doc = nlp(text.lower())
        phrase_doc = nlp(phrase.lower())
        
        for sent in doc.sents:
            for token in sent:
                if token.lemma_ == phrase_doc[0].lemma_ or token.text == phrase_doc[0].text:
                    match = True
                    matched_tokens = [token]
                    
                    for i, phrase_token in enumerate(phrase_doc[1:], 1):
                        if token.i + i >= len(doc):
                            match = False
                            break
                            
                        next_token = doc[token.i + i]
                        if (next_token.lemma_ != phrase_token.lemma_ and 
                            next_token.text != phrase_token.text):
                            if (next_token.is_punct and token.i + i + 1 < len(doc)):
                                next_token = doc[token.i + i + 1]
                                if (next_token.lemma_ == phrase_token.lemma_ or 
                                    next_token.text == phrase_token.text):
                                    matched_tokens.append(next_token)
                                    continue
                            match = False
                            break
                        matched_tokens.append(next_token)
                    
                    if match:
                        fragment = text[matched_tokens[0].idx:matched_tokens[-1].idx + len(matched_tokens[-1])]
                        if fragment not in unique_fragments:
                            unique_fragments.add(fragment)
                            all_variants.append({
                                "fraza_bazowa": phrase,
                                "znaleziony_fragment": fragment,
                                "typ": "lematyzacja",
                                "źródło": "SpaCy"
                            })
                            stats["lematyzacja"] += 1
                            stats["total"] += 1
        
        # 2. Szukamy przez GPT-4-mini
        found, gpt_variants, gpt_stats = ai_checker.check_phrase_with_gpt4mini(text, phrase)
        
        # Dodajemy tylko unikalne warianty z GPT
        for variant in gpt_variants:
            fragment = variant["fragment"]
            if fragment not in unique_fragments:
                unique_fragments.add(fragment)
                typ = variant["typ"].lower()  # Normalizujemy typ do małych liter
                all_variants.append({
                    "fraza_bazowa": phrase,
                    "znaleziony_fragment": fragment,
                    "typ": typ,
                    "źródło": "GPT-4-mini"
                })
                stats[typ] += 1
                stats["total"] += 1
    
    return all_variants, stats

def generate_statistics(all_variants: List[Dict[str, str]], stats: Dict[str, int]) -> Dict:
    """Generuje statystyki z wyników."""
    return stats

def highlight_text(text: str, variants: List[Dict[str, str]]) -> str:
    """Podświetla znalezione frazy w tekście."""
    # Sortujemy warianty od najdłuższych do najkrótszych
    sorted_variants = sorted(variants, key=lambda x: len(x["znaleziony_fragment"]), reverse=True)
    
    # Tworzymy kopię tekstu do modyfikacji
    highlighted_text = text
    
    # Podświetlamy każdy wariant
    for variant in sorted_variants:
        fragment = variant["znaleziony_fragment"]
        highlighted = f'<mark style="background-color: #FFE4B5">{fragment}</mark>'
        highlighted_text = highlighted_text.replace(fragment, highlighted)
    
    # Zamieniamy znaki nowej linii na <br> dla HTML
    highlighted_text = highlighted_text.replace("\n", "<br>")
    
    return f'<div style="white-space: pre-wrap;">{highlighted_text}</div>'

