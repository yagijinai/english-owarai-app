import streamlit as st
import pandas as pd
import datetime
import random
import requests
import json
import streamlit.components.v1 as components
import hashlib
import time

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
    combined = str(name) + "_" + hash_password(password)
    return combined[:50]

FIRESTORE_URL = "https://firestore.googleapis.com/v1/projects/" + FIREBASE_CONFIG['projectId'] + "/databases/(default)/documents/users"

# --- 便利機能 ---
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
        st.error("CSVファイルの読み込み中にエラーが発生しました。ファイル名が正しいか確認してください。")
        st.stop()

WORDS_DF, NETA_DF = load_data()

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
    except:
        pass
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

# --- アプリ設定 ---
st.set_page_config(page_title="お笑い英語マスター Pro", page_icon="📝")

if "user_id" not in st.session_state: st.session_state.user_id = None
if "phase" not in st.session_state: st.session_state.phase = "login"
if "wrong_id" not in st.session_state: st.session_state.wrong_id = None
if "show_hint" not in st.session_state: st.session_state.show_hint = False

# --- 画面1: ログイン ---
if st.session_state.user_id is None:
    st.title("English Master Pro")
    st.write("～ お笑い芸人と学ぶ、最強の英単語アプリ ～")

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
    # 自動ログイン情報がある場合の「二択」画面
    if "id" in q and "nm" in q:
        u_id, u_name = q["id"], q["nm"]
        st.success("おかえりなさい！ " + str(u_name) + " さん")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔥 続きから勉強をはじめる", use_container_width=True):
                d = get_user_data(u_id)
                if d:
                    st.session_state.user_id, st.session_state.user_name = u_id, u_name
                    st.session_state.streak, st.session_state.last_clear = d["streak"], d["last_clear"]
                    st.session_state.learned_ids = d["learned_ids"]
                    st.session_state.phase = "init"
                    st.rerun()
        with col2:
            if st.button("👤 他の名前でログイン", use_container_width=True):
                st.query_params.clear()
                components.html("<script>localStorage.clear();</script>", height=0)
                st.rerun()
    # 新規・手動ログイン画面
    else:
        n_in = st.text_input("なまえ").strip()
        p_in = st.text_input("パスワード", type="password")
        if st.button("🚀 ログイン / 新規登録", use_container_width=True):
            if n_in and p_in:
                u_id = get_user_id(n_in, p_in)
                d = get_user_data(u_id)
                if not d:
                    save_user_data(u_id, n_in, 0, "", [])
                    d = {"display_name": n_in, "streak": 0, "last_clear": "", "learned_ids": []}
                st.session_state.user_id, st.session_state.user_name = u_id, n_in
                st.session_state.streak, st.session_state.last_clear = d["streak"], d["last_clear"]
                st.session_state.learned_ids = d["learned_ids"]
                set_local_storage(u_id, n_in)
                st.query_params["id"], st.query_params["nm"] = u_id, n_in
                st.session_state.phase = "init"
                st.rerun()
    st.stop()

# --- 画面2: 初期化 ---
if st.session_state.phase == "init":
    today = str(datetime.date.today())
    yst = str(datetime.date.today() - datetime.timedelta(days=1))
    if
