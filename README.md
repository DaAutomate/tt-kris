# Lematyzator Tekstów z Historią

Narzędzie do lematyzacji tekstów i wyszukiwania fraz kluczowych z funkcją historii, stworzone w Streamlit.

## Funkcje

- ✨ Wczytywanie tekstu z pliku lub przez input
- 🔍 Wyszukiwanie fraz kluczowych z uwzględnieniem odmiany
- 📊 Wizualizacja wyników w formie wykresów
- 💾 Historia wyszukiwań
- 📥 Eksport wyników do CSV i JSON
- 🎨 Podświetlanie znalezionych fraz w tekście

## Instalacja

1. Zainstaluj wymagane pakiety:
```bash
pip install -r requirements.txt
```

2. Zainstaluj model języka polskiego dla spaCy:
```bash
python -m spacy download pl_core_news_sm
```

## Uruchomienie

```bash
streamlit run app.py
```

## Struktura projektu

- `app.py` - główna aplikacja Streamlit
- `lemmatizer.py` - funkcje do lematyzacji i wyszukiwania
- `requirements.txt` - wymagane pakiety
- `history.csv` - plik z historią wyszukiwań (tworzony automatycznie)

## Użycie

1. Wprowadź tekst do analizy (wklej lub wczytaj z pliku)
2. Wprowadź frazy kluczowe (jedna fraza na linię)
3. Kliknij "Analizuj"
4. Przeglądaj wyniki w formie:
   - Tabeli z liczbą wystąpień
   - Wykresu słupkowego
   - Podświetlonego tekstu
5. Eksportuj wyniki do CSV lub JSON
6. Przeglądaj historię analiz w zakładce "Historia"

## Wymagania systemowe

- Python 3.8+
- Streamlit 1.29+
- spaCy 3.7+
- Pandas 2.1+
- Plotly 5.18+
