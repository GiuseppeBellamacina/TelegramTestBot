# 🗺️ Mappa Concettuale Navigabile con Bot Telegram

Applicazione web realizzata con Streamlit per visualizzare e navigare una mappa concettuale strutturata gerarchicamente. Quando si raggiunge una "foglia" della mappa, è possibile inviare un messaggio predefinito a un bot Telegram.

## 📋 Caratteristiche

- ✨ Interfaccia intuitiva con Streamlit
- 🌳 Navigazione gerarchica della mappa concettuale
- 📊 Visualizzazione chiara di categorie e foglie
- 🔙 Breadcrumb navigation per tornare indietro
- 📤 Invio messaggi automatico a bot Telegram
- 🤖 Integrazione con OpenAI per domande all'intelligenza artificiale
- 📈 Statistiche sulla struttura della mappa
- 🎨 Icone distintive per categorie (📁) e foglie (📄)

## 🚀 Installazione

### 1. Clona o scarica il progetto

```bash
cd cheating
```

### 2. Installa le dipendenze

```bash
pip install -r requirements.txt
```

### 3. Configura il Bot Telegram

#### a) Crea un bot Telegram

1. Apri Telegram e cerca [@BotFather](https://t.me/BotFather)
2. Invia il comando `/newbot`
3. Segui le istruzioni per scegliere nome e username del bot
4. Salva il **token** che riceverai (formato: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

#### b) Ottieni il tuo Chat ID

1. Cerca [@userinfobot](https://t.me/userinfobot) su Telegram
2. Avvia una conversazione
3. Il bot ti mostrerà il tuo **Chat ID** (es: `123456789`)

#### c) Configura i secrets

Crea un file `.streamlit/secrets.toml` nella root del progetto:

```bash
mkdir .streamlit
```

Crea il file `.streamlit/secrets.toml` con i tuoi valori:

```toml
TELEGRAM_BOT_TOKEN = "il_tuo_token_del_bot"
TELEGRAM_CHAT_ID = "il_tuo_chat_id"
OPENAI_API_KEY = "sk-proj-la_tua_api_key_openai"
```

> **Nota**: Il file funziona anche con variabili d'ambiente (`.env`) come fallback.

### 4. Configura OpenAI (opzionale)

Se vuoi usare la funzionalità di domande all'AI:

1. Crea un account su [OpenAI Platform](https://platform.openai.com/)
2. Genera una API Key dalla sezione [API Keys](https://platform.openai.com/api-keys)
3. Aggiungi la chiave al file `.env` come mostrato sopra

### 5. Personalizza la mappa concettuale

Modifica il file `concept_map.json` secondo la tua struttura. Il formato è il seguente:

```json
{
  "title": "Titolo Principale",
  "description": "Descrizione opzionale",
  "children": {
    "categoria1": {
      "title": "Nome Categoria 1",
      "description": "Descrizione categoria",
      "children": {
        "foglia1": {
          "title": "Nome Foglia",
          "description": "Descrizione foglia",
          "message": "Messaggio da inviare a Telegram quando si raggiunge questa foglia"
        }
      }
    }
  }
}
```

**Regole importanti:**

- Un nodo con `"children"` è una categoria (visualizzata con 📁)
- Un nodo con `"message"` e senza `"children"` è una foglia (visualizzata con 📄)
- Solo le foglie possono inviare messaggi a Telegram

## 🎯 Esecuzione

Avvia l'applicazione con:

```bash
streamlit run app.py
```

L'applicazione si aprirà automaticamente nel browser all'indirizzo `http://localhost:8501`

## 📖 Come Usare

1. **Navigazione**: Clicca sui pulsanti per navigare attraverso la struttura

   - 📁 = Categoria con sotto-argomenti
   - 📄 = Foglia con messaggio da inviare

2. **Breadcrumb**: Usa la barra in alto per vedere il percorso corrente

3. **Torna indietro**: Usa il pulsante "⬅️ Indietro" per tornare al livello precedente

4. **Invio messaggio**: Quando raggiungi una foglia:

   - Visualizzi il messaggio che verrà inviato
   - Clicca "📤 Invia messaggio a Telegram" per inviarlo al bot

5. **Chiedi all'AI** (🤖 pulsante in alto a destra):

   - Disponibile da qualsiasi schermata
   - Scrivi una domanda nella casella di testo
   - L'AI (ChatGPT) elabora la risposta usando un prompt predefinito
   - La risposta viene mostrata e inviata automaticamente al bot Telegram

6. **Sidebar**: Mostra statistiche sulla mappa e istruzioni

## 🔧 Struttura del Progetto

```
cheating/
├── app.py                 # Applicazione Streamlit principale
├── concept_map.json       # Mappa concettuale (modificabile)
├── requirements.txt       # Dipendenze Python
├── .env.example          # Template per configurazione
├── .env                  # Configurazione Telegram (da creare)
├── .gitignore           # File da ignorare in git
└── README.md            # Questo file
```

## 🛠️ Tecnologie Utilizzate

- **Streamlit**: Framework per l'interfaccia web
- **Requests**: Libreria per chiamate HTTP (API Telegram)
- **Python-dotenv**: Gestione variabili d'ambiente
- **LangChain**: Framework per applicazioni AI
- **OpenAI**: API per ChatGPT

## 📝 Personalizzazione Avanzata

### Modificare l'aspetto

Puoi personalizzare i colori e lo stile modificando la configurazione di Streamlit in `app.py`:

```python
st.set_page_config(
    page_title="Tuo Titolo",
    page_icon="🎓",  # Cambia emoji
    layout="wide"
)
```

### Aggiungere nuovi campi al JSON

Puoi estendere il JSON con campi personalizzati e visualizzarli nell'app modificando `app.py`.

### Personalizzare il prompt dell'AI

Il prompt per OpenAI è definito nel codice sorgente in `app.py`. Cerca la funzione `ask_openai` e modifica il `PromptTemplate.from_template()` per cambiare il comportamento dell'AI.

## ❓ Risoluzione Problemi

### Il messaggio non viene inviato

- Verifica che il token del bot sia corretto
- Assicurati di aver avviato una conversazione con il bot su Telegram
- Controlla che il Chat ID sia corretto

### L'AI non risponde

- Verifica che l'API Key di OpenAI sia corretta e valida
- Controlla di avere crediti disponibili sul tuo account OpenAI
- Verifica la connessione internet

### Errore nel caricamento del JSON

- Verifica che `concept_map.json` sia valido (usa un validatore JSON online)
- Controlla che la struttura segua le regole (foglie con `message`, categorie con `children`)

### L'app non si avvia

- Verifica di aver installato tutte le dipendenze: `pip install -r requirements.txt`
- Controlla la versione di Python (consigliata: 3.8+)

## 📄 Licenza

Progetto libero per uso personale ed educativo.

## 🤝 Contributi

Sentiti libero di modificare e migliorare il progetto secondo le tue esigenze!
