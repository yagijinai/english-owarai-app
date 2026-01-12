import streamlit as st
import pandas as pd
import datetime
import random
import requests
import json
import streamlit.components.v1 as components
import hashlib

# ==========================================
# 1. 基本設定（アプリの土台）
# ==========================================
st.set_page_config(page_title="お笑い英語マスター Pro", page_icon="📝")

# --- Firebase 設定 ---
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyB0Bd8aBmos2fHiD7XgH_S4yM5b__FHypI",
    "authDomain": "english-ap.firebaseapp.com",
    "projectId": "english-ap",
    "storageBucket": "english-ap.firebasestorage.app",
    "messagingSenderId": "167152900538",
    "appId": "1:167152900538:web:07a87314d3121c23eca583"
}

FIRESTORE_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_CONFIG['projectId']}/databases/(default)/documents/users"

# --- パスワード暗号化 ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_id(name, password):
    combined = f"{name}_{hash_password(password)}"
    return combined[:50]

# --- 音声再生 ---
def text_to_speech(text):
    clean = str(text).replace("'", "")
    js = f"<script>var m=new SpeechSynthesisUtterance();m.text='{clean}';m.lang='en-US';window.speechSynthesis.speak(m);</script>"
    components.html(js, height=0)

# ==========================================
# 2. データ読み込み（真っ白防止機能付）
# ==========================================
@st.cache_data
def load_csv_data():
    try:
        w = pd.read_csv('words.csv')
        n = pd.read_csv('neta.csv')
        if w.empty or n.empty:
            return None, None, "CSVファイルが空です。"
        w['id'] = w['word'].astype(str) + "_" + w['meaning'].astype(str)
        return w, n, None
    except Exception as e:
        return None, None, f"ファイル読み込みエラー: {str(e)}"

WORDS_DF, NETA_DF, LOAD_ERROR = load_csv_data()

if LOAD_ERROR:
    st.error(f"⚠️ 起動エラー: {LOAD_ERROR}")
    st.info("GitHubに 'words.csv' と 'neta.csv' があるか確認してください。")
    st.stop()

# ==========================================
# 3. Firestore (データベース) 連携
# ==========================================
def get_user_data(u_id):
    url = f"{FIRESTORE_URL}/{u_id}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            f = r.json().get("fields", {})
            # 1つずつ丁寧に取り出す（エラー防止）
            d_name = f.get("display_name", {}).get("stringValue", "User")
            streak = int(f.get("streak", {}).get("integerValue", 0))
            last_c = f.get("last_clear", {}).get("stringValue", "")
            l_ids_raw = f.get("learned_ids", {}).get("arrayValue", {}).get("values", [])
            l_ids = [v.get("stringValue") for v in l_ids_raw if v.get("stringValue")]
            return {"display_name": d_name, "streak": streak, "last_clear": last_c, "learned_ids": l_ids}
    except:
        pass
    return None

def save_user_data(u_id, name, streak, last, l_ids):
    url = f"{FIRESTORE_URL}/{u_id}"
    # 安全なデータ構造
    values = [{"stringValue": str(i)} for i in l_ids]
    data = {
        "fields": {
            "display_name": {"stringValue": str(name)},
            "streak": {"integerValue": int(streak)},
            "last_clear": {"stringValue": str(last)},
            "learned_ids": {"arrayValue": {"values": values}}
        }
    }
    try:
        requests.patch(url, json=data, timeout=5)
    except:
        pass

# ==========================================
# 4. セッション状態の初期化
# ==========================================
if "phase" not in st.session_state:
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.streak = 0
    st.session_state.last_clear = ""
    st.session_state.learned_ids = []
    st.session_state.phase = "login"
    st.session_state.idx = 0
    st.session_state.p_list = []
    st.session_state.r_list = []
    st.session_state.neta = None
    st.session_state.wrong_id = None
    st.session_state.show_hint = False
    st.session_state.is_correct_feedback = False

# ==========================================
# 5. 画面：ログイン
# ==========================================
if st.session_state.phase == "login":
    st.title("English Master Pro")
    st.write("～ お笑い芸人と学ぶ英単語アプリ ～")
    
    n_in = st.text_input("なまえ").strip()
    p_in = st.text_input("パスワード", type="password")
    
    if st.button("🚀 ログイン / 新規登録", use_container_width=True):
        if n_in and p_in:
            u_id = get_user_id(n_in, p_in)
            d = get_user_data(u_id)
            if not d:
                save_user_data(u_id, n_in, 0, "", [])
                d = {"display_name": n_in, "streak": 0, "last_clear": "", "learned_ids": []}
            
            st.session_state.user_id = u_id
            st.session_state.user_name = n_in
            st.session_state.streak = d["streak"]
            st.session_state.last_clear = d["last_clear"]
            st.session_state.learned_ids = d["learned_ids"]
            st.session_state.phase = "init"
            st.rerun()
