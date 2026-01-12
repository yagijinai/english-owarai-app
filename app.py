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
    combined = f"{name}_{hash_password(password)}"
    return combined[:50]

FIRESTORE_BASE_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_CONFIG['projectId']}/databases/(default)/documents/users"

# --- 便利機能 ---
def text_to_speech(text):
    js_code = f"<script>var msg = new SpeechSynthesisUtterance(); msg.text = '{text}'; msg.lang = 'en-US'; window.speechSynthesis.speak(msg);</script>"
    components.html(js_code, height=0)

def set_local_storage(user_id, display_name):
    # ブラウザにユーザー情報を刻み込むJavaScript
    js_code = f"""
    <script>
    localStorage.setItem('eng_app_userid', '{user_id}');
    localStorage.setItem('eng_app_name', '{display_name}');
    </script>
    """
    components.html(js_code, height=0)

@st.cache_data
def load_data():
    try:
        words_df = pd.read_csv('words.csv')
        neta_df = pd.read_csv('neta.csv')
        words_df['id'] = words_df['word'] + "_" + words_df['meaning']
        return words_df, neta_df
    except:
        st.error("csvが見つかりません。")
        st.stop()

WORDS_DF, NETA_DF = load_data()

def get_user_data_by_id(user_id):
    url = f"{FIRESTORE_BASE_URL}/{user_id}"
    res = requests.get(url)
    if res.status_code == 200:
        f = res.json().get("fields", {})
        return {
            "display_name": f.get("display_name", {}).get("stringValue", ""),
            "streak": int(f.get("streak", {}).get("integerValue", 0)),
            "last_clear": f.get("last_clear", {}).get("stringValue", ""),
            "learned_ids": [v.get("stringValue") for v in f.get("learned_ids", {}).get("arrayValue", {}).get("values", [])]
        }
    return None

def save_user_data_by_id(user_id, display_name, streak, last_clear, learned_ids):
    url = f"{FIRESTORE_BASE_URL}/{user_id}"
    data = {
        "fields": {
            "display_name": {"stringValue": display_name},
            "streak": {"integerValue": streak},
            "last_clear": {"stringValue": last_clear},
            "learned_ids": {"arrayValue": {"values": [{"stringValue": i} for i in learned_ids]}}
        }
    }
    requests.patch(url, params={"updateMask.fieldPaths": ["display_name", "streak", "last_clear", "learned_ids"]}, json=data)

# --- ログイン・起動画面 ---
st.set_page_config(page_title="お笑い英語マスター Pro", page_icon="📝")

if "wrong_word_id" not in st.session_state:
    st.session_state.wrong_word_id = None

if "user_id" not in st.session_state:
    st.markdown("""<style>
    .main-title { font-size: 50px; color: #1E88E5; text-align: center; font-weight: bold; margin-bottom: 0px; }
    .sub-title { font-size: 18px; text-align: center; color: #555; margin-bottom: 40px; }
    div.stButton > button:first-child { width: 100%; height: 80px; font-size: 24px; font-weight: bold; border-radius: 15px; background-color: #f0f2f6; border: 2px solid #1E88E5; }
    </style>""", unsafe_allow_html=True)
    
    st.markdown('<div class="main-title">English Master Pro</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">～ お笑い芸人と学ぶ、最強の英単語アプリ ～</div>', unsafe_allow_html=True)

    # ブラウザの保存情報をURLハッシュに書き出すJS
    if "check_js" not in st.session_state:
        components.html("""
            <script>
            var id = localStorage.getItem('eng_app_userid');
            var nm = localStorage.getItem('eng_app_name');
            if(id && nm) {
                parent.window.location.hash = 'id=' + id + '&nm=' + encodeURIComponent(nm);
            } else {
                parent.window.location.hash = 'new';
            }
            </script>
        """, height=0)
        st.session_state.check_js = True

    q = st.query_params
    
    # URLに情報がある（保存情報が見つかった）場合
    if "id" in q and "nm" in q:
        u_id, u_name = q["id"], q["nm"]
        st.markdown(f"<h2 style='text-align: center;'>おかえり！ {u_name} さん</h2>", unsafe_allow_html=True)
        if st.button("🔥 続きから勉強をはじめる"):
            data = get_user_data_by_id(u_id)
            if data:
                st.session_state.user_id, st.session_state.user_name = u_id, u_name
                st.session_state.streak, st.session_state.last_clear = data["streak"], data["last_clear"]
                st.session_state.learned_ids = data["learned_ids"]
                st.rerun()
            else:
                st.error("データが見つかりませんでした。新しくログインしてください。")
                st.query_params.clear()
                st.rerun()
        
        st.write("")
        if st.button("👤 別のなまえでログインする"):
            st.query_params.clear()
            components.html("<script>localStorage.clear();</script>", height=0)
            st.rerun()
            
    # 情報がない場合
    else:
        st.info("名前とパスワードを入力してね！")
        n_input = st.text_input("なまえ").strip()
        p_input = st.text_input("パスワード", type="password")
        if st.button("🚀 ログイン / 新規登録"):
            if n_input and p_input:
                u_id = get_user_id(n_input, p_input)
                data = get_user_data_by_id(u_id)
                if not data:
                    data = {"display_name": n_input, "streak": 0, "last_clear": "", "learned_ids": []}
                    save_user_data_by_id(u_id, n_input, 0, "", [])
                st.session_state.user_id, st.session_state.user_name = u_id, n_input
                st.session_state.streak, st.session_state.last_clear = data["streak"], data["last_clear"]
                st.session_state.learned_ids = data["learned_ids"]
                set_local_storage(u_id, n_input)
                st.rerun()
    st.stop()

# --- 学習ロジック (ここから下は変更なし)
