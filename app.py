import streamlit as st
import pandas as pd
import datetime
import random
import requests
import json
import streamlit.components.v1 as components
import hashlib

# --- 1. Firebase・基本設定 ---
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyB0Bd8aBmos2fHiD7XgH_S4yM5b__FHypI",
    "authDomain": "english-ap.firebaseapp.com",
    "projectId": "english-ap",
    "storageBucket": "english-ap.firebasestorage.app",
    "messagingSenderId": "167152900538",
    "appId": "1:167152900538:web:07a87314d3121c23eca583",
    "measurementId": "G-PEH3BVTK4H"
}

FIRESTORE_URL = "https://firestore.googleapis.com/v1/projects/" + FIREBASE_CONFIG['projectId'] + "/databases/(default)/documents/users"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_id(name, password):
    combined = str(name) + "_" + hash_password(password)
    return combined[:50]

# --- 2. 便利機能 ---
def text_to_speech(text):
    clean = str(text).replace("'", "")
    js = "<script>var m=new SpeechSynthesisUtterance();m.text='" + clean + "';m.lang='en-US';window.speechSynthesis.speak(m);</script>"
    components.html(js, height=0)

def set_local_storage(u_id, u_name):
    js = "<script>localStorage.setItem('eng_app_userid','" + str(u_id) + "');localStorage.setItem('eng_app_name','" + str(u_name) + "');</script>"
    components.html(js, height=0)

@st.cache_data
def load_data():
    try:
        w = pd.read_csv('words.csv')
        n = pd.read_csv('neta.csv')
        w['id'] = w['word'].astype(str) + "_" + w['meaning'].astype(str)
        return w, n
    except Exception as e:
        st.error("CSVファイルの読み込みエラー。ファイルを確認してください。")
        st.stop()

WORDS_DF, NETA_DF = load_data()

# --- 3. Firestore連携 ---
def get_user_data(u_id):
    url = FIRESTORE_URL + "/" + str(u_id)
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            f = r.json().get("fields", {})
            return {
                "display_name": f.get("display_name", {}).get("stringValue", ""),
                "streak": int(f.get("streak", {}).get("integerValue", 0)),
                "last_clear": f.get("last_clear", {}).get("stringValue", ""),
                "learned_ids": [v.get("stringValue") for v in f.get("learned_ids", {}).get("arrayValue", {}).get("values", [])]
            }
    except: pass
    return None

def save_user_data(u_id, name, streak, last, l_ids):
    url = FIRESTORE_URL + "/" + str(u_id)
    data = {
        "fields": {
            "display_name": {"stringValue": str(name)},
            "streak": {"integerValue": int(streak)},
            "last_clear": {"stringValue": str(last)},
            "learned_ids": {"arrayValue": {"values": [{"stringValue": str(i)} for i in l_ids]}}
        }
    }
    requests.patch(url, params={"updateMask.fieldPaths": ["display_name", "streak", "last_clear", "learned_ids"]}, json=data)

# --- 4. 画面制御 ---
st.set_page_config(page_title="お笑い英語マスター Pro", page_icon="📝")

# セッション変数の初期化
keys = ["user_id", "user_name", "streak", "last_clear", "learned_ids", "phase", "idx", "p_list", "r_list", "neta", "wrong_id", "show_hint", "is_correct_feedback"]
for k in keys:
    if k not in st.session_state:
        if k == "phase": st.session_state[k] = "login"
        elif k in ["learned_ids", "p_list", "r_list"]: st.session_state[k] = []
        elif k in ["streak", "idx"]: st.session_state[k] = 0
        elif k in ["show_hint", "is_correct_feedback"]: st.session_state[k] = False
        else: st.session_state[k] = None

# --- 5. ログイン画面 ---
if st.session_state.user_id is None:
    st.title("English Master Pro")
    
    if "check_js" not in st.session_state:
        components.html("""<script>
            var id=localStorage.getItem('eng_app_userid');
            var nm=localStorage.getItem('eng_app_name');
            if(id && nm && !window.location.hash.includes('id=')){
                parent.window.location.hash = 'id='+id+'&nm='+encodeURIComponent(nm);
            }
            </script>""", height=0)
        st.session_state.check_js = True

    q = st.query_params
    if "id" in q and "nm" in q:
        u_id, u_name = q["id"], q["nm"]
        st.success("おかえりなさい、 " + str(u_name) + " さん！")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔥 続きから勉強をはじめる", use_container_width=True):
                d = get_user_data(u_id)
                if d:
                    st.session_state.user_id, st.session_state.user_name = u_id, u_name
                    st.session_state.streak, st.session_state.last_clear = d["streak
