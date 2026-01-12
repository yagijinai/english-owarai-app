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

FIRESTORE_BASE_URL = "https://firestore.googleapis.com/v1/projects/" + FIREBASE_CONFIG['projectId'] + "/databases/(default)/documents/users"

# --- 音声再生・保存機能 ---
def text_to_speech(text):
    t = str(text).replace("'", "\\'")
    js = "<script>var m=new SpeechSynthesisUtterance();m.text='" + t + "';m.lang='en-US';window.speechSynthesis.speak(m);</script>"
    components.html(js, height=0)

def set_local_storage(user_id, display_name):
    js = "<script>localStorage.setItem('eng_app_userid','" + str(user_id) + "');localStorage.setItem('eng_app_name','" + str(display_name) + "');</script>"
    components.html(js, height=0)

@st.cache_data
def load_data():
    try:
        w = pd.read_csv('words.csv')
        n = pd.read_csv('neta.csv')
        w['id'] = w['word'].astype(str) + "_" + w['meaning'].astype(str)
        return w, n
    except Exception as e:
        st.error("CSVデータの読み込みに失敗しました。")
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

# --- 画面構成 ---
st.set_page_config(page_title="お笑い英語マスター Pro", page_icon="📝")

# セッション状態の完全な初期化
if "user_id" not in st.session_state: st.session_state.user_id = None
if "phase" not in st.session_state: st.session_state.phase = "login"
if "wrong_word_id" not in st.session_state: st.session_state.wrong_word_id = None

# --- フェーズ1: ログイン ---
if st.session_state.user_id is None:
    st.markdown("<h1 style='text-align:center; color:#1E88E5;'>English Master Pro</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>～ お笑い芸人と学ぶ、最強の英単語アプリ ～</p>", unsafe_allow_html=True)

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
        st.success("おかえりなさい！ " + str(u_name) + " さん")
        if st.button("🔥 続きから勉強をはじめる", use_container_width=True):
            data = get_user_data_by_id(u_id)
            if data:
                st.session_state.user_id = u_id
                st.session_state.user_name = u_name
                st.session_state.streak = data["streak"]
                st.session_state.last_clear = data["last_clear"]
                st.session_state.learned_ids = data["learned_ids"]
                st.session_state.phase = "init"
                st.rerun()
        if st.button("👤 別の名前でログイン"):
            st.query_params.clear()
            components.html("<script>localStorage.clear();</script>", height=0)
            st.rerun()
    else:
        n_in = st.text_input("名前").strip()
        p_in = st.text_input("パスワード", type="password")
        if st.button("🚀 ログイン / 新規登録", use_container_width=True):
            if n_in and p_in:
                u_id = get_user_id(n_in, p_in)
                data = get_user_data_by_id(u_id)
                if not data:
                    save_user_data_by_id(u_id, n_in, 0, "", [])
                    data = {"display_name": n_in, "streak": 0, "last_clear": "", "learned_ids": []}
                st.session_state.user_id = u_id
                st.session_state.user_name = n_in
                st.session_state.streak = data["streak"]
                st.session_state.last_clear = data["last_clear"]
                st.session_state.learned_ids = data["learned_ids"]
                set_local_storage(u_id, n_in)
                st.query_params["id"], st.query_params["nm"] = u_id, n_in
                st.session_state.phase = "init"
                st.rerun()
    st.stop()

# --- フェーズ2: データ準備 ---
if st.session_state.phase == "
