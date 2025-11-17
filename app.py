import json
import os
from time import sleep
from typing import List, Tuple

import requests
import streamlit as st
from dotenv import find_dotenv, load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

# ============================================================================
# CONFIGURAZIONE E MODELLI
# ============================================================================

load_dotenv(find_dotenv())

class MessageResponse(BaseModel):
    """Risposta del modello OpenAI con messaggi suddivisi"""
    messages: List[str]


# ============================================================================
# CACHE E RISORSE
# ============================================================================

@st.cache_resource
def get_llm_chain():
    """Crea e cache la chain LLM per evitare ricaricamenti"""
    prompt_template = PromptTemplate.from_template(
        """Sei un assistente esperto e disponibile. Rispondi alla seguente domanda in modo chiaro, 
conciso e professionale. Se la domanda riguarda argomenti di studio, fornisci spiegazioni 
dettagliate ma comprensibili. Non scrivere formule in markdown. Se il messaggio di risposta è
troppo lungo, suddividilo in più messaggi di massimo 120 caratteri ciascuno. Non fare messaggi eccessivamente corti se
decidi di suddividerlo e cerca di non fare più di 5 messaggi in totale. Se puoi mandare un solo messaggio fallo.

Domanda: {question}

Risposta:"""
    )
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    return prompt_template | llm.with_structured_output(MessageResponse)


@st.cache_data
def load_concept_map(json_path: str):
    """Carica la mappa concettuale dal file JSON"""
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================================
# FUNZIONI TELEGRAM
# ============================================================================

def send_telegram_message(bot_token: str, chat_id: str, message: str) -> Tuple[bool, str]:
    """Invia un messaggio al bot Telegram"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return True, "Messaggio inviato con successo!"
    except Exception as e:
        return False, f"Errore nell'invio: {str(e)}"


def send_multiple_telegram_messages(bot_token: str, chat_id: str, messages: List[str]) -> Tuple[bool, str]:
    """Invia più messaggi in sequenza al bot Telegram"""
    failed_messages = []

    for i, message in enumerate(messages):
        success, error_msg = send_telegram_message(bot_token, chat_id, message)
        sleep(0.5)  # Pausa per evitare rate limiting
        if not success:
            failed_messages.append((i + 1, error_msg))

    if not failed_messages:
        return True, f"Tutti i {len(messages)} messaggi inviati con successo!"
    else:
        error_details = "; ".join([f"Msg {num}: {err}" for num, err in failed_messages])
        return False, f"Errori nell'invio: {error_details}"


# ============================================================================
# FUNZIONI OPENAI
# ============================================================================

def ask_openai(question: str) -> Tuple[bool, List[str] | str]:
    """Interroga OpenAI con una domanda e ritorna la risposta"""
    try:
        chain = get_llm_chain()
        response: MessageResponse = chain.invoke({"question": question})  # type: ignore
        return True, response.messages
    except Exception as e:
        return False, f"Errore nella chiamata a OpenAI: {str(e)}"


# ============================================================================
# FUNZIONI NAVIGAZIONE MAPPA CONCETTUALE
# ============================================================================

def is_leaf(node) -> bool:
    """Verifica se un nodo è una foglia (non ha sotto-argomenti)"""
    if isinstance(node, dict):
        return "message" in node and "children" not in node
    return False


def get_children(node):
    """Ottiene i figli di un nodo"""
    if isinstance(node, dict) and "children" in node:
        return node["children"]
    return None


def navigate_to_path(data, path: List[str]):
    """Naviga nel dizionario seguendo il percorso specificato"""
    current = data
    for key in path:
        if isinstance(current, dict):
            if "children" in current and key in current["children"]:
                current = current["children"][key]
            else:
                return None
        else:
            return None
    return current


def count_nodes(node) -> int:
    """Conta il numero totale di nodi nella mappa"""
    count = 0
    if isinstance(node, dict):
        if "children" in node:
            for child in node["children"].values():
                count += 1 + count_nodes(child)
    return count


def count_leaves(node) -> int:
    """Conta il numero di foglie nella mappa"""
    if is_leaf(node):
        return 1
    count = 0
    if isinstance(node, dict) and "children" in node:
        for child in node["children"].values():
            count += count_leaves(child)
    return count


# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_ai_modal(openai_api_key: str, telegram_bot_token: str, telegram_chat_id: str):
    """Renderizza il modal per le domande all'AI"""
    st.markdown("### 🤖 Chiedi all'Intelligenza Artificiale")

    if not openai_api_key:
        st.warning("⚠️ Configura OPENAI_API_KEY nelle variabili d'ambiente per usare questa funzionalità.")
        st.info("Aggiungi al file `.env`:\n```\nOPENAI_API_KEY=sk-...\n```")
        return

    with st.form("ai_question_form"):
        user_question = st.text_area(
            "Fai una domanda:",
            placeholder="Scrivi qui la tua domanda...",
            height=100,
        )

        col1, col2, _ = st.columns([1, 1, 3])
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

                # Visualizza i messaggi
                if isinstance(ai_response, list):
                    for i, msg in enumerate(ai_response, 1):
                        if len(ai_response) > 1:
                            st.info(f"**Parte {i}/{len(ai_response)}:** {msg}")
                        else:
                            st.info(msg)
                else:
                    st.info(ai_response)

                # Invia a Telegram se configurato
                if telegram_bot_token and telegram_chat_id and isinstance(ai_response, list):
                    messages_to_send = [f"❓ Domanda: {user_question}"]

                    if len(ai_response) == 1:
                        messages_to_send.append(f"🤖 Risposta AI:\n{ai_response[0]}")
                    else:
                        for i, msg in enumerate(ai_response, 1):
                            messages_to_send.append(f"🤖 Risposta AI (parte {i}/{len(ai_response)}):\n{msg}")

                    telegram_success, telegram_msg = send_multiple_telegram_messages(
                        telegram_bot_token, telegram_chat_id, messages_to_send
                    )

                    if telegram_success:
                        st.success(f"📱 {telegram_msg}")
                    else:
                        st.warning(f"⚠️ {telegram_msg}")

                st.session_state.show_ai_modal = False
                st.rerun()
            else:
                st.error(ai_response)

        elif submit and not user_question.strip():
            st.warning("⚠️ Scrivi una domanda prima di inviare.")

        if cancel:
            st.session_state.show_ai_modal = False
            st.rerun()


def render_leaf_node(node, telegram_bot_token: str, telegram_chat_id: str):
    """Renderizza una foglia della mappa concettuale"""
    st.success("📄 Hai raggiunto una foglia della mappa concettuale!")

    message = node.get("message", "Nessun messaggio disponibile")
    st.markdown("### Messaggio da inviare:")
    st.code(message, language=None)

    if not telegram_bot_token or not telegram_chat_id:
        st.warning("⚠️ Configura TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID nelle variabili d'ambiente per abilitare l'invio.")
        st.info("Puoi creare un file `.env` con:\n```\nTELEGRAM_BOT_TOKEN=your_bot_token\nTELEGRAM_CHAT_ID=your_chat_id\n```")
    else:
        if st.button("📤 Invia messaggio a Telegram", type="primary", use_container_width=True):
            success, result_message = send_telegram_message(telegram_bot_token, telegram_chat_id, message)
            if success:
                st.success(result_message)
                st.balloons()
                st.session_state.message_sent = True
            else:
                st.error(result_message)


def render_category_node(children):
    """Renderizza un nodo categoria con i suoi figli"""
    st.subheader("📚 Sotto-argomenti disponibili:")

    cols_per_row = 3
    child_items = list(children.items())

    for i in range(0, len(child_items), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, (key, value) in enumerate(child_items[i : i + cols_per_row]):
            with cols[j]:
                icon = "📄" if is_leaf(value) else "📁"
                display_name = value.get("title", key) if isinstance(value, dict) else key

                if st.button(f"{icon} {display_name}", key=f"btn_{key}", use_container_width=True):
                    st.session_state.current_path.append(key)
                    st.session_state.message_sent = False
                    st.rerun()


def render_sidebar(concept_map):
    """Renderizza la sidebar con informazioni e statistiche"""
    with st.sidebar:
        st.header("ℹ️ Informazioni")
        st.markdown(
            """
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
        """
        )

        st.markdown("---")

        total_nodes = count_nodes(concept_map)
        total_leaves = count_leaves(concept_map)

        st.metric("Totale nodi", total_nodes)
        st.metric("Totale foglie", total_leaves)
        st.metric("Livello corrente", len(st.session_state.current_path))


# ============================================================================
# APPLICAZIONE PRINCIPALE
# ============================================================================

def main():
    """Funzione principale dell'applicazione"""
    # Configurazione pagina
    st.set_page_config(
        page_title="Mappa Concettuale Navigabile", 
        page_icon="🗺️", 
        layout="wide"
    )

    # Inizializza stato sessione
    if "current_path" not in st.session_state:
        st.session_state.current_path = []
    if "message_sent" not in st.session_state:
        st.session_state.message_sent = False
    if "show_ai_modal" not in st.session_state:
        st.session_state.show_ai_modal = False

    # Carica configurazione
    try:
        concept_map = load_concept_map("concept_map.json")
    except FileNotFoundError:
        st.error("⚠️ File 'concept_map.json' non trovato. Assicurati che esista nella directory del progetto.")
        st.stop()

    # Variabili d'ambiente
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    # Header
    col_title, col_ai_button = st.columns([5, 1])
    with col_title:
        st.title("🗺️ Mappa Concettuale Navigabile")
    with col_ai_button:
        st.write("")
        if st.button("🤖 Chiedi all'AI", use_container_width=True):
            st.session_state.show_ai_modal = True

    st.markdown("---")

    # Modal AI
    if st.session_state.show_ai_modal:
        render_ai_modal(OPENAI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        st.markdown("---")

    # Breadcrumb navigation
    if st.session_state.current_path:
        breadcrumb = " > ".join(["🏠 Home"] + st.session_state.current_path)
        st.markdown(f"**Percorso:** {breadcrumb}")

        col1, _ = st.columns([1, 5])
        with col1:
            if st.button("⬅️ Indietro"):
                st.session_state.current_path.pop()
                st.session_state.message_sent = False
                st.rerun()
    else:
        st.markdown("**Percorso:** 🏠 Home")

    st.markdown("---")

    # Navigazione
    current_node = navigate_to_path(concept_map, st.session_state.current_path)

    if current_node is None:
        st.error("Errore nella navigazione. Torno alla home.")
        st.session_state.current_path = []
        st.rerun()

    # Visualizza titolo e descrizione
    if isinstance(current_node, dict) and "title" in current_node:
        st.header(current_node["title"])
        if "description" in current_node:
            st.info(current_node["description"])

    # Renderizza nodo
    if is_leaf(current_node):
        render_leaf_node(current_node, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    else:
        children = get_children(current_node)
        if children:
            render_category_node(children)
        else:
            st.warning("Nessun sotto-argomento disponibile.")

    # Sidebar
    render_sidebar(concept_map)


if __name__ == "__main__":
    main()
