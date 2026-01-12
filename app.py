import streamlit as st
import pandas as pd
import datetime
import random
import requests
import json
import streamlit.components.v1 as components
import hashlib

# --- 1. 基本設定とエラー表示用関数 ---
st.set_page_config(page_title="お笑い英語マスター Pro", page_icon="📝")

def show_critical_error(msg):
    st.error(f"⚠️ アプリを起動できませんでした: {msg}")
    st.info("GitHubに 'words.csv' と 'neta.csv' が正しく保存されているか確認してください。")
    st.stop()

# --- 2. Firebase・Firestore設定 ---
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyB0Bd8aBmos2fHiD7XgH_S4yM5b__FHypI",
    "authDomain": "english-ap.firebaseapp.com",
    "projectId": "english-ap",
    "storageBucket": "english-ap.firebasestorage.app",
    "messagingSenderId": "167152900538",
    "appId": "1:167152900538:web:07a87314d3121c23eca583",
    "measurementId": "G-PEH3BVTK4H"
}

FIRESTORE_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_CONFIG['projectId']}/databases/(default)/documents/users"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_id(name, password):
    combined = f"{name}_{hash_password(password)}"
    return combined[:50]

# --- 3. 音声・ストレージ機能 ---
def text_to_speech(text):
    clean = str(text).replace("'", "")
    js = f"<script>var m=new SpeechSynthesisUtterance();m.text='{clean}';m.lang='en-US';window.speechSynthesis.speak(m);</script>"
    components.html(js, height=0)

def set_local_storage(u_id, u_name):
    js = f"<script>localStorage.setItem('eng_app_userid','{u_id}');localStorage.setItem('eng_app_name','{u_name}');</script>"
    components.html(js, height=0)

# --- 4. データ読み込み（真っ白防止の要） ---
@st.cache_data
def load_data():
    try:
        w = pd.read_csv('words.csv')
        n = pd.read_csv('neta.csv')
        if w.empty or n.empty:
            return None, "CSVファイルの中身が空です。"
        w['id'] = w['word'].astype(str) + "_" + w['meaning'].astype(str)
        return (w, n), None
    except FileNotFoundError:
        return None, "CSVファイル（words.csv または neta.csv）が見つかりません。"
    except Exception as e:
        return None, f"データの読み込み中にエラーが発生しました: {str(e)}"

DATA, ERROR_MSG = load_data()
if ERROR_MSG:
    show_critical_error(ERROR_MSG)

WORDS_DF, NETA_DF = DATA

# --- 5. Firestore連携 ---
def get_user_data(u_id):
    url = f"{FIRESTORE_URL}/{u_id}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            f = r.json().get("fields", {})
            return {
                "display_name": f.get("display_name", {}).get("stringValue", ""),
                "streak": int(f.get("streak", {}).get("integerValue", 0)),
                "last_clear": f.get
