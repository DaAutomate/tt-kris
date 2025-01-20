import os
from typing import List, Dict, Tuple
import requests
import re
import json
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

class AIChecker:
    """Klasa do sprawdzania fraz używając GPT-4-mini"""
    
    def __init__(self):
        """Inicjalizuje checker z kluczem API"""
        # Klucz API będzie pobierany z session_state
        self.api_key = st.session_state.openai_api_key if 'openai_api_key' in st.session_state else None

    def create_search_prompt(self, text: str, phrase: str) -> str:
        return f"""ZADANIE: Znajdź w tekście WSZYSTKIE rzeczywiste wystąpienia frazy "{phrase}".
WAŻNE: Zwracaj TYLKO te fragmenty, które NAPRAWDĘ występują w tekście - NIE WYMYŚLAJ żadnych przykładów!

TEKST DO PRZEANALIZOWANIA:
{text}

INSTRUKCJE:
1. Przeanalizuj tekst i znajdź WSZYSTKIE wystąpienia frazy lub jej wariantów
2. Każdy znaleziony fragment MUSI być dokładnym cytatem z tekstu
3. Dla każdego znalezionego fragmentu określ typ:
   - dokładne (identyczne jak wzór)
   - odmiana (inna forma gramatyczna)
   - rozdzielone (przerwane znakami lub słowami)
   - przestawione (zmieniona kolejność)
   - rozszerzone (z dodatkowymi słowami)

WYMAGANY FORMAT ODPOWIEDZI:

ZNALEZIONE FRAGMENTY:
1. "dokładny_cytat_z_tekstu" (typ: dokładne)
[kolejne znalezione fragmenty...]

STATYSTYKI ZNALEZIONYCH WYSTĄPIEŃ:
Łącznie znaleziono: [liczba wszystkich znalezionych]
W tym:
- dokładne: [liczba]
- odmiana: [liczba]
- rozdzielone: [liczba]
- przestawione: [liczba]
- rozszerzone: [liczba]

KRYTYCZNIE WAŻNE:
- Podawaj TYLKO fragmenty, które FAKTYCZNIE znalazłeś w tekście
- Każdy fragment musi być możliwy do znalezienia w tekście poprzez ctrl+f
- Statystyki muszą odpowiadać RZECZYWISTEJ liczbie znalezionych wystąpień
- NIE WYMYŚLAJ żadnych wariantów - raportuj tylko to co znalazłeś"""

    def check_phrase_with_gpt4mini(self, text: str, phrase: str) -> Tuple[bool, List[Dict[str, str]], Dict[str, int]]:
        """
        Sprawdza frazę używając GPT-4-mini.
        """
        try:
            # Sprawdzamy czy mamy klucz API
            if not st.session_state.get('openai_api_key'):
                st.error("Wprowadź i zapisz klucz API w panelu konfiguracji!")
                return False, [], {}

            # Tworzymy prompt
            prompt = self.create_search_prompt(text, phrase)
            
            # Wywołujemy API OpenAI
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {st.session_state.openai_api_key}"
                },
                json={
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }
            )
            
            # Sprawdzamy błędy autoryzacji
            if response.status_code == 401:
                st.error("❌ Nieprawidłowy klucz API! Sprawdź czy wprowadziłeś poprawny klucz.")
                return False, [], {}
            
            # Sprawdzamy inne błędy
            response.raise_for_status()
            
            # Parsujemy odpowiedź
            response_data = response.json()
            if 'choices' not in response_data or not response_data['choices']:
                return False, [], {}
                
            # Pobieramy tekst odpowiedzi
            response_text = response_data['choices'][0]['message']['content']
            
            # Parsujemy odpowiedź
            variants = []
            stats = {
                "dokładne": 0,
                "odmiana": 0,
                "rozdzielone": 0,
                "przestawione": 0,
                "rozszerzone": 0,
                "total": 0
            }
            
            current_section = None
            
            for line in response_text.split("\n"):
                if not line:
                    continue
                
                if "ZNALEZIONE FRAGMENTY:" in line:
                    current_section = "variants"
                    continue
                elif "STATYSTYKI ZNALEZIONYCH WYSTĄPIEŃ:" in line:
                    current_section = "stats"
                    continue
                
                if current_section == "variants":
                    # Szukamy linii z wariantem
                    match = re.search(r'"([^"]+)"\s*\(typ:\s*(\w+)\)', line)
                    if match:
                        fragment, typ = match.groups()
                        variants.append({
                            "fragment": fragment,
                            "typ": typ.lower()
                        })
                
                elif current_section == "stats":
                    # Szukamy linii ze statystykami
                    match = re.search(r'([^:]+):\s*(\d+)', line)
                    if match:
                        key, value = match.groups()
                        key = key.strip().lower()
                        value = int(value.strip().split()[0])  # Bierzemy tylko liczbę
                        
                        if "łącznie znaleziono" in key:
                            stats["total"] = value
                        elif "dokładne" in key:
                            stats["dokładne"] = value
                        elif "odmiana" in key:
                            stats["odmiana"] = value
                        elif "rozdzielone" in key:
                            stats["rozdzielone"] = value
                        elif "przestawione" in key:
                            stats["przestawione"] = value
                        elif "rozszerzone" in key:
                            stats["rozszerzone"] = value
            
            return True, variants, stats
            
        except Exception as e:
            print(f"Błąd podczas analizy: {str(e)}")
            return False, [], {}

    def find_all_variants(self, text: str, phrases: List[str]) -> Tuple[Dict[str, List[Dict[str, str]]], Dict[str, Dict[str, int]]]:
        """
        Znajduje wszystkie warianty fraz w tekście.
        
        Args:
            text: Tekst do przeanalizowania
            phrases: Lista fraz do znalezienia
            
        Returns:
            Tuple[Dict[str, List[Dict[str, str]]], Dict[str, Dict[str, int]]]:
                (Warianty fraz, Statystyki dla każdej frazy)
        """
        results = {}
        stats = {}
        
        for phrase in phrases:
            found, variants, phrase_stats = self.check_phrase_with_gpt4mini(text, phrase)
            if found:
                results[phrase] = variants
                stats[phrase] = phrase_stats
                    
        return results, stats
