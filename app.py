import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import time
import json
import requests
from datetime import datetime
import re

from lemmatizer import load_model, find_phrases, highlight_text, generate_statistics

# Konfiguracja strony
st.set_page_config(
    page_title="Lematyzator tekstów",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Customowy CSS
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .stats-box {
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 10px;
        border: 1px solid #e0e0e0;
    }
    .legend {
        padding: 10px;
        margin-bottom: 10px;
        border-radius: 5px;
    }
    .legend-container {
        display: flex;
        gap: 10px;
        margin-bottom: 10px;
        align-items: center;
    }
    </style>
    """, unsafe_allow_html=True)

# Inicjalizacja modelu
nlp = load_model()

def save_to_history(text: str, phrases: list, all_variants: list, stats: dict):
    """Zapisuje wyniki do historii"""
    history_file = "history.csv"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    new_record = {
        "timestamp": timestamp,
        "tekst_oryginalny": text[:100] + "..." if len(text) > 100 else text,
        "frazy_kluczowe": ", ".join(phrases),
        "wyniki": json.dumps(all_variants, ensure_ascii=False),
        "statystyki": json.dumps(stats, ensure_ascii=False)
    }
    
    if os.path.exists(history_file):
        df = pd.read_csv(history_file)
        df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
    else:
        df = pd.DataFrame([new_record])
    
    df.to_csv(history_file, index=False)

def main():
    st.title("Lematyzator tekstów z historią")

    # Inicjalizacja session state dla API key
    if 'openai_api_key' not in st.session_state:
        st.session_state['openai_api_key'] = ""

    # Sekcja konfiguracji API key
    with st.sidebar:
        st.header("Konfiguracja")
        
        # Pole do wprowadzenia klucza API
        api_key = st.text_input(
            "OpenAI API Key",
            value=st.session_state['openai_api_key'],
            type="password",
            help="Wprowadź swój klucz API z OpenAI"
        )
        
        # Przycisk do zapisania klucza
        if st.button("Zapisz klucz API"):
            if api_key:
                st.session_state['openai_api_key'] = api_key
                st.success("Klucz API został zapisany!")
            else:
                st.error("Wprowadź klucz API!")
        
        # Informacja o statusie klucza API
        if st.session_state['openai_api_key']:
            st.success("Klucz API jest skonfigurowany")
        else:
            st.warning("Wprowadź klucz API aby korzystać z analizy tekstu")
    
    # Główne zakładki aplikacji
    tab1, tab2 = st.tabs(["Analiza tekstu", "Historia"])
    
    with tab1:
        # Sprawdź czy klucz API jest skonfigurowany
        if not st.session_state['openai_api_key']:
            st.error("Wprowadź klucz API w panelu konfiguracji aby rozpocząć analizę!")
            return
            
        col1, col2 = st.columns([2, 1])
        
        with col1:
            text_input = st.text_area(
                "Wprowadź tekst do analizy",
                height=200,
                placeholder="Wklej tutaj swój tekst..."
            )
            
            uploaded_file = st.file_uploader(
                "Lub wczytaj plik tekstowy",
                type=["txt"]
            )
            
        with col2:
            phrases_input = st.text_area(
                "Wprowadź frazy kluczowe (jedna fraza na linię)",
                height=150,
                placeholder="np.:\nsztuczna inteligencja\nanaliza danych"
            )
            
            phrases_file = st.file_uploader(
                "Lub wczytaj plik z frazami",
                type=["txt"]
            )

        if uploaded_file:
            text_input = uploaded_file.getvalue().decode('utf-8')
        
        if phrases_file:
            phrases_input = phrases_file.getvalue().decode('utf-8')

        phrases = [p.strip() for p in phrases_input.split("\n") if p.strip()]
        
        if st.button("Analizuj", type="primary", use_container_width=True):
            if text_input and phrases:
                with st.spinner("Trwa analiza..."):
                    # Krok 1: Analiza tekstu i znalezienie wszystkich wariantów
                    all_variants, stats = find_phrases(text_input, phrases, nlp)
                    
                    # Zapisanie do historii
                    save_to_history(text_input, phrases, all_variants, stats)
                    
                    st.success("Analiza zakończona!")
                    
                    # Krok 2: Wyświetlanie tabeli z wariantami
                    st.subheader("Znalezione warianty fraz")
                    
                    # Tworzymy DataFrame ze wszystkimi wariantami
                    df_variants = pd.DataFrame(all_variants)
                    df_variants = df_variants.rename(columns={
                        "fraza_bazowa": "Fraza bazowa",
                        "znaleziony_fragment": "Znaleziony wariant",
                        "typ": "Typ dopasowania",
                        "źródło": "Źródło"
                    })
                    
                    # Sortujemy według frazy bazowej i typu
                    df_variants = df_variants.sort_values(["Fraza bazowa", "Typ dopasowania"])
                    
                    # Wyświetlamy tabelę
                    st.dataframe(df_variants, use_container_width=True)
                    
                    # Czekamy 5 sekund
                    with st.spinner("Przygotowywanie kolorowania..."):
                        time.sleep(5)
                    
                    # Krok 3: Kolorowanie wszystkich znalezionych wariantów
                    st.subheader("Tekst z podświetlonymi frazami")
                    st.markdown("""
                        <div class="legend-container">
                            <span class="legend" style="background-color: #FFE4B5">Znalezione warianty</span>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Kolorujemy wszystkie znalezione warianty
                    highlighted_text = highlight_text(text_input, all_variants)
                    st.markdown(highlighted_text, unsafe_allow_html=True)
                    
                    # Statystyki
                    st.subheader("Statystyki")
                    
                    # Tworzymy 2 kolumny na statystyki
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Wykres kołowy typów dopasowań
                        types_data = {
                            "dokładne": stats["dokładne"],
                            "odmiana": stats["odmiana"],
                            "rozdzielone": stats["rozdzielone"],
                            "przestawione": stats["przestawione"],
                            "rozszerzone": stats["rozszerzone"],
                            "lematyzacja": stats["lematyzacja"]
                        }
                        
                        fig = go.Figure(data=[go.Pie(
                            labels=list(types_data.keys()),
                            values=list(types_data.values()),
                            hole=.3
                        )])
                        fig.update_layout(title="Typy dopasowań")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Szczegółowe statystyki w formie tabeli
                        st.markdown(
                            f"""<div class="stats-box">
                            <h3>Szczegółowe statystyki</h3>
                            <p>Łącznie znalezionych wariantów: {stats["total"]}</p>
                            <p>W tym:</p>
                            <ul>
                                <li>Dokładne dopasowania: {stats["dokładne"]}</li>
                                <li>Odmiany: {stats["odmiana"]}</li>
                                <li>Rozdzielone: {stats["rozdzielone"]}</li>
                                <li>Przestawione: {stats["przestawione"]}</li>
                                <li>Rozszerzone: {stats["rozszerzone"]}</li>
                                <li>Przez lematyzację: {stats["lematyzacja"]}</li>
                            </ul>
                            </div>""",
                            unsafe_allow_html=True
                        )

    with tab2:
        st.subheader("Historia analiz")
        if os.path.exists("history.csv"):
            history_df = pd.read_csv("history.csv")
            
            # Filtry
            col1, col2 = st.columns(2)
            with col1:
                date_filter = st.date_input(
                    "Filtruj po dacie",
                    value=None
                )
            with col2:
                phrase_filter = st.text_input(
                    "Filtruj po frazie",
                    placeholder="Wpisz frazę..."
                )
            
            # Aplikowanie filtrów
            if date_filter:
                history_df['date'] = pd.to_datetime(history_df['timestamp']).dt.date
                history_df = history_df[history_df['date'] == date_filter]
            
            if phrase_filter:
                history_df = history_df[
                    history_df['frazy_kluczowe'].str.contains(
                        phrase_filter,
                        case=False,
                        na=False
                    )
                ]
            
            # Wyświetlanie historii
            if not history_df.empty:
                st.dataframe(
                    history_df.sort_values("timestamp", ascending=False),
                    use_container_width=True,
                    hide_index=True
                )
                
                # Eksport historii
                st.download_button(
                    "Pobierz całą historię (CSV)",
                    history_df.to_csv(index=False).encode('utf-8'),
                    "historia_analiz.csv",
                    "text/csv"
                )
            else:
                st.info("Brak wyników dla wybranych filtrów")
        else:
            st.info("Historia jest pusta")

if __name__ == "__main__":
    main()

