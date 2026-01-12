import streamlit as st
import pandas as pd
import datetime
import random
import requests
import json
import streamlit.components.v1 as components
import hashlib

# --- Firebase 設定 ---
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyB0Bd8aBmos2fHiD7XgH_S4yM5b__FHypI",
    "authDomain": "english-ap.firebaseapp.com",
    "projectId": "english-ap",
    "storageBucket": "english-ap.firebasestorage.app",
    "messagingSenderId": "167152900538",
    "appId": "1:167152900538:web:07a87314d3121c23eca583",
    "measurementId": "G-PEH3BVTK4H"
}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_id(name, password):
    combined = name + "_" + hash_password(password)
    return combined[:50]

FIRESTORE_BASE_URL = "https://firestore.googleapis.com/v1/projects/" + FIREBASE_CONFIG['projectId'] + "/databases/(default)/documents/users"

# --- 便利機能 ---
def text_to_speech(text):
    clean_text = str(text).replace("'", "\\'")
    js_code = "<script>var msg = new SpeechSynthesisUtterance(); msg.text = '" + clean_text + "'; msg.lang = 'en-US'; window.speechSynthesis.speak(msg);</script>"
    components.html(js_code, height=0)

def set_local_storage(user_id, display_name):
    js_code = "<script>localStorage.setItem('eng_app_userid', '" + str(user_id) + "'); localStorage.setItem('eng_app_name', '" + str(display_name) + "');</script>"
    components.html(js_code, height=0)

@st.cache_data
def load_data():
    try:
        w_df = pd.read_csv('words.csv')
        n_df = pd.read_csv('neta.csv')
        w_df['id'] = w_df['word'].astype(str) + "_" + w_df['meaning'].astype(str)
        return w_df, n_df
    except Exception as e:
        st.error("データの読み込みに失敗しました。ファイルがあるか確認してください。")
        st.stop()

WORDS_DF, NETA_DF = load_data()

def get_user_data_by_id(user_id):
    url = FIRESTORE_BASE_URL + "/" + str(user_id)
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            f = res.json().get("fields", {})
            return {
                "display_name": f.get("display_name", {}).get("stringValue", ""),
                "streak": int(f.get("streak", {}).get("integerValue", 0)),
                "last_clear": f.get("last_clear", {}).get("stringValue", ""),
                "learned_ids": [v.get("stringValue") for v in f.get("learned_ids", {}).get("arrayValue", {}).get("values", [])]
            }
    except:
        pass
    return None

def save_user_data_by_id(user_id, display_name, streak, last_clear, learned_ids):
    url = FIRESTORE_BASE_URL + "/" + str(user_id)
    data = {
        "fields": {
            "display_name": {"stringValue": str(display_name)},
            "streak": {"integerValue": int(streak)},
            "last_clear": {"stringValue": str(last_clear)},
            "learned_ids": {"arrayValue": {"values": [{"stringValue": str(i)} for i in learned_ids]}}
        }
    }
    requests.patch(url, params={"updateMask.fieldPaths": ["display_name", "streak", "last_clear", "learned_ids"]}, json=data)

# --- 画面構成設定 ---
st.set_page_config(page_title="お笑い英語マスター Pro", page_icon="📝")

# セッション状態の初期化
if "user_id" not in st.session_state: st.session_state.user_id = None
if "phase" not in st.session_state: st.session_state.phase = "login"
if "wrong_word_id" not in st.session_state: st.session_state.wrong_word_id = None

# --- 1. ログイン画面 ---
if st.session_state.user_id is None:
    st.markdown("<h1 style='text-align:center; color:#1E88E5;'>English Master Pro</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>～ お笑い芸人と学ぶ、最強の英単語アプリ ～</p>", unsafe_allow_
