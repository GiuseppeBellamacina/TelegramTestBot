import streamlit as st
import json
import requests
import os
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

load_dotenv(find_dotenv())

# Template del prompt predefinito
prompt_template = PromptTemplate.from_template(
            """Sei un assistente esperto e disponibile. Rispondi alla seguente domanda in modo chiaro, 
conciso e professionale. Se la domanda riguarda argomenti di studio, fornisci spiegazioni 
dettagliate ma comprensibili. Non scrivere formule in markdown.

Domanda: {question}

Risposta:"""
)

# Inizializza il modello ChatOpenAI
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7
)

# Crea la chain
chain = prompt_template | llm

# Configurazione pagina
st.set_page_config(
    page_title="Mappa Concettuale Navigabile",
    page_icon="🗺️",
    layout="wide"
)

# Funzione per caricare il JSON
@st.cache_data
def load_concept_map(json_path):
    """Carica la mappa concettuale dal file JSON"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Funzione per inviare messaggio al bot Telegram
def send_telegram_message(bot_token, chat_id, message):
    """Invia un messaggio al bot Telegram"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return True, "Messaggio inviato con successo!"
    except Exception as e:
        return False, f"Errore nell'invio: {str(e)}"

# Funzione per interrogare OpenAI
def ask_openai(question):
    """Interroga OpenAI con una domanda e ritorna la risposta"""
    try:
        # Esegui la query
        response = chain.invoke({"question": question})
        
        return True, response.content
    except Exception as e:
        return False, f"Errore nella chiamata a OpenAI: {str(e)}"

# Funzione per controllare se un nodo è una foglia
def is_leaf(node):
    """Verifica se un nodo è una foglia (non ha sotto-argomenti)"""
    if isinstance(node, dict):
        # Una foglia deve avere un campo 'message' e non avere 'children'
        return 'message' in node and 'children' not in node
    return False

# Funzione per ottenere i figli di un nodo
def get_children(node):
    """Ottiene i figli di un nodo"""
    if isinstance(node, dict) and 'children' in node:
        return node['children']
    return None

# Funzione per navigare nel dizionario annidato
def navigate_to_path(data, path):
    """Naviga nel dizionario seguendo il percorso specificato"""
    current = data
    for key in path:
        if isinstance(current, dict):
            if 'children' in current and key in current['children']:
                current = current['children'][key]
            else:
                return None
        else:
            return None
    return current

# Inizializza lo stato della sessione
if 'current_path' not in st.session_state:
    st.session_state.current_path = []
if 'message_sent' not in st.session_state:
    st.session_state.message_sent = False
if 'show_ai_modal' not in st.session_state:
    st.session_state.show_ai_modal = False

# Carica configurazione
try:
    concept_map = load_concept_map('concept_map.json')
except FileNotFoundError:
    st.error("⚠️ File 'concept_map.json' non trovato. Assicurati che esista nella directory del progetto.")
    st.stop()

# Carica token Telegram e OpenAI (da variabile d'ambiente o .env)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# Header
col_title, col_ai_button = st.columns([5, 1])
with col_title:
    st.title("🗺️ Mappa Concettuale Navigabile")
with col_ai_button:
    st.write("")  # Spacer per allineamento
    if st.button("🤖 Chiedi all'AI", use_container_width=True):
        st.session_state.show_ai_modal = True

st.markdown("---")

# Modal per domanda all'AI
if st.session_state.show_ai_modal:
    st.markdown("### 🤖 Chiedi all'Intelligenza Artificiale")
    
    if not OPENAI_API_KEY:
        st.warning("⚠️ Configura OPENAI_API_KEY nelle variabili d'ambiente per usare questa funzionalità.")
        st.info("Aggiungi al file `.env`:\n```\nOPENAI_API_KEY=sk-...\n```")
    else:
        with st.form("ai_question_form"):
            user_question = st.text_area(
                "Fai una domanda:",
                placeholder="Scrivi qui la tua domanda...",
                height=100
            )
            
            col1, col2, col3 = st.columns([1, 1, 3])
            with col1:
                submit = st.form_submit_button("📤 Invia", type="primary", use_container_width=True)
            with col2:
                cancel = st.form_submit_button("❌ Annulla", use_container_width=True)
            
            if submit and user_question.strip():
                with st.spinner("🤔 L'AI sta pensando..."):
                    success, ai_response = ask_openai(user_question)
                
                if success:
                    st.success("✅ Risposta ricevuta!")
                    st.markdown("**Risposta dell'AI:**")
                    st.info(ai_response)
                    
                    # Invia la risposta a Telegram
                    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                        formatted_message = f"❓ Domanda: {user_question}\n\n🤖 Risposta AI:\n{ai_response}"
                        telegram_success, telegram_msg = send_telegram_message(
                            TELEGRAM_BOT_TOKEN,
                            TELEGRAM_CHAT_ID,
                            formatted_message
                        )
                        if telegram_success:
                            st.success("📱 Risposta inviata anche a Telegram!")
                        else:
                            st.warning(f"⚠️ Risposta non inviata a Telegram: {telegram_msg}")
                    
                    st.session_state.show_ai_modal = False
                    st.rerun()
                else:
                    st.error(ai_response)
            
            elif submit and not user_question.strip():
                st.warning("⚠️ Scrivi una domanda prima di inviare.")
            
            if cancel:
                st.session_state.show_ai_modal = False
                st.rerun()
    
    st.markdown("---")

# Breadcrumb navigation
if st.session_state.current_path:
    breadcrumb = " > ".join(["🏠 Home"] + st.session_state.current_path)
    st.markdown(f"**Percorso:** {breadcrumb}")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("⬅️ Indietro"):
            st.session_state.current_path.pop()
            st.session_state.message_sent = False
            st.rerun()
else:
    st.markdown("**Percorso:** 🏠 Home")

st.markdown("---")

# Ottieni il nodo corrente
current_node = navigate_to_path(concept_map, st.session_state.current_path)

if current_node is None:
    st.error("Errore nella navigazione. Torno alla home.")
    st.session_state.current_path = []
    st.rerun()

# Visualizza il titolo del nodo corrente se disponibile
if isinstance(current_node, dict) and 'title' in current_node:
    st.header(current_node['title'])
    if 'description' in current_node:
        st.info(current_node['description'])

# Controlla se è una foglia
if is_leaf(current_node):
    st.success("📄 Hai raggiunto una foglia della mappa concettuale!")
    
    # Mostra il messaggio
    message = current_node.get('message', 'Nessun messaggio disponibile')
    st.markdown("### Messaggio da inviare:")
    st.code(message, language=None)
    
    # Pulsante per inviare il messaggio a Telegram
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        st.warning("⚠️ Configura TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID nelle variabili d'ambiente per abilitare l'invio.")
        st.info("Puoi creare un file `.env` con:\n```\nTELEGRAM_BOT_TOKEN=your_bot_token\nTELEGRAM_CHAT_ID=your_chat_id\n```")
    else:
        if st.button("📤 Invia messaggio a Telegram", type="primary", use_container_width=True):
            success, result_message = send_telegram_message(
                TELEGRAM_BOT_TOKEN,
                TELEGRAM_CHAT_ID,
                message
            )
            if success:
                st.success(result_message)
                st.balloons()
                st.session_state.message_sent = True
            else:
                st.error(result_message)
else:
    # Visualizza i sotto-argomenti disponibili
    children = get_children(current_node)
    
    if children:
        st.subheader("📚 Sotto-argomenti disponibili:")
        
        # Crea una griglia per i bottoni
        cols_per_row = 3
        child_items = list(children.items())
        
        for i in range(0, len(child_items), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, (key, value) in enumerate(child_items[i:i+cols_per_row]):
                with cols[j]:
                    # Determina l'icona in base al tipo di nodo
                    if is_leaf(value):
                        icon = "📄"
                        button_type = "secondary"
                    else:
                        icon = "📁"
                        button_type = "primary"
                    
                    # Ottieni il titolo se disponibile, altrimenti usa la chiave
                    display_name = value.get('title', key) if isinstance(value, dict) else key
                    
                    if st.button(f"{icon} {display_name}", key=f"btn_{key}", use_container_width=True):
                        st.session_state.current_path.append(key)
                        st.session_state.message_sent = False
                        st.rerun()
    else:
        st.warning("Nessun sotto-argomento disponibile.")

# Sidebar con informazioni
with st.sidebar:
    st.header("ℹ️ Informazioni")
    st.markdown("""
    ### Come usare:
    1. Naviga attraverso i sotto-argomenti cliccando sui pulsanti
    2. 📁 indica una categoria con sotto-argomenti
    3. 📄 indica una foglia con un messaggio
    4. Quando raggiungi una foglia, puoi inviare il messaggio a Telegram
    
    ### Configurazione Telegram:
    - Crea un bot con [@BotFather](https://t.me/BotFather)
    - Ottieni il token del bot
    - Ottieni il tuo chat_id (usa [@userinfobot](https://t.me/userinfobot))
    - Configura le variabili d'ambiente
    """)
    
    st.markdown("---")
    
    # Mostra statistiche
    def count_nodes(node):
        count = 0
        if isinstance(node, dict):
            if 'children' in node:
                for child in node['children'].values():
                    count += 1 + count_nodes(child)
        return count
    
    def count_leaves(node):
        if is_leaf(node):
            return 1
        count = 0
        if isinstance(node, dict) and 'children' in node:
            for child in node['children'].values():
                count += count_leaves(child)
        return count
    
    total_nodes = count_nodes(concept_map)
    total_leaves = count_leaves(concept_map)
    
    st.metric("Totale nodi", total_nodes)
    st.metric("Totale foglie", total_leaves)
    st.metric("Livello corrente", len(st.session_state.current_path))
