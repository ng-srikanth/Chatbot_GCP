import streamlit as st
import os
import time
import json
import requests


from google.cloud import firestore
from langchain_google_firestore import FirestoreChatMessageHistory
from google.oauth2 import service_account
from dotenv import load_dotenv

load_dotenv()
auth_dict = json.loads(os.environ["GCP_AUTH"])

credentials = service_account.Credentials.from_service_account_info(auth_dict)
PROJECT_ID = os.environ["PROJECT_ID"]
client = firestore.Client(
    project= PROJECT_ID,
    database="(default)",
    credentials= credentials
)
def send_request(payload):
    try:
        query_url = os.environ["API_URL"]
        response = requests.post(query_url, json=payload)
        response_data = response.json()
        return response_data
    except Exception as e:
        print("error : ", e)
        return {"error": "Internal server error"}
def get_sessions(firestore_client):
    collection_name= "ChatHistory"
    return [x.id for x in firestore_client.collection(collection_name).list_documents()]
def get_session_history(session_id, firestore_client):
    return FirestoreChatMessageHistory(session_id= session_id, client=firestore_client)


def get_chat_history(session):
   
    if session:
        history = get_session_history(session, client)
        
        
        if history.messages == []:
            history.add_ai_message("How may I assist you today?")

        for msg in history.messages:
            st.chat_message(msg.type).write(msg.content)
    if prompt := st.chat_input():
        st.chat_message("human").write(prompt)
        with st.chat_message("ai"):
            type_message = st.empty()
            type_message.write("typing...")
            message_placeholder = st.empty()
            payload = {"question": prompt, "session_id": session}
            response = send_request(payload)
            body = response["body"]
            stream = ""
            type_message.empty()
            for i in body:
                stream += i
                time.sleep(0.002)
                message_placeholder.markdown(stream + " ", unsafe_allow_html=True)
            message_placeholder.markdown(stream, unsafe_allow_html=True)
with st.sidebar:
    sessions = get_sessions(client)
    st.sidebar.write("**Start New session**")
    new_session = st.sidebar.chat_input("New session name")
    seleceted_session = st.sidebar.selectbox("**Session Id**", sessions, index=None)
    if "session" not in st.session_state:
        st.session_state["session"] = None

    if new_session:
        st.session_state["session"] = new_session
    elif seleceted_session:
        st.session_state["session"] = seleceted_session
    st.sidebar.write(f"current session:  **{st.session_state.session}**")
get_chat_history(st.session_state["session"])