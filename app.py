import streamlit as st
import pandas as pd
import datetime
import random
import requests
import json
import streamlit.components.v1 as components
import hashlib

# ==========================================
# 1. 基本設定とFirebase連携
# ==========================================
st.set_page_config(page_title="お笑い英語マスター Pro", page_icon="📝")

FIREBASE_CONFIG = {
    "apiKey": "AIzaSyB0Bd8aBmos2fHiD7XgH_S4yM5b__FHypI",
    "authDomain": "english-ap.firebaseapp.com",
    "projectId": "english-ap",
    "storageBucket": "english-ap.firebasestorage.app",
    "messagingSenderId": "167152900538",
    "appId": "1:167152900538:web:07a87314d3121c23eca583"
}

FIRESTORE_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_CONFIG['projectId']}/databases/(default)/documents/users"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_id(name, password):
    combined = f"{name}_{hash_password(password)}"
    return combined[:50]

def text_to_speech(text):
    clean = str(text).replace("'", "")
    js = f"<script>var m=new SpeechSynthesisUtterance();m.text='{clean}';m.lang='en-US';window.speechSynthesis.speak(m);</script>"
    components.html(js, height=0)

# ==========================================
# 2. データ読み込み（安全性重視）
# ==========================================
@st.cache_data
def load_csv_data():
    try:
        w = pd.read_csv('words.csv')
        n = pd.read_csv('neta.csv')
        if w.empty or n.empty:
            return None, None, "CSVの中身が空です。"
        w['id'] = w['word'].astype(str) + "_" + w['meaning'].astype(str)
        return w, n, None
    except Exception as e:
        return None, None, f"読み込み失敗: {str(e)}"

WORDS_DF, NETA_DF, LOAD_ERROR = load_csv_data()

if LOAD_ERROR:
    st.error(f"⚠️ エラー: {LOAD_ERROR}")
    st.stop()

# ==========================================
# 3. データベース（Firestore）操作
# ==========================================
def fetch_user_data(u_id):
    url = f"{FIRESTORE_URL}/{u_id}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            f = r.json().get("fields", {})
            return {
                "display_name": f.get("display_name", {}).get("stringValue", ""),
                "streak": int(f.get("streak", {}).get("integerValue", 0)),
                "last_clear": f.get("last_clear", {}).get("stringValue", ""),
                "learned_ids": [v.get("stringValue") for v in f.get("learned_ids", {}).get("arrayValue", {}).get("values", []) if v.get("stringValue")]
            }
    except: pass
    return None

def save_user_data(u_id, name, streak, last, l_ids):
    url = f"{FIRESTORE_URL}/{u_id}"
    data = {
        "fields": {
            "display_name": {"stringValue": str(name)},
            "streak": {"integerValue": int(streak)},
            "last_clear": {"stringValue": str(last)},
            "learned_ids": {"arrayValue": {"values": [{"stringValue": str(i)} for i in l_ids]}}
        }
    }
    requests.patch(url, json=data, timeout=5)

# ==========================================
# 4. セッション初期化
# ==========================================
if "phase" not in st.session_state:
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.phase = "login"
    st.session_state.is_correct_feedback = False
    st.session_state.show_hint = False

# ==========================================
# 5. 【修正版】ログイン画面（二択）
# ==========================================
if st.session_state.phase == "login":
    st.title("English Master Pro")
    
    # ブラウザのメモリから名前を取得するJS
    if "checked_storage" not in st.session_state:
        components.html("""<script>
            var id=localStorage.getItem('eng_app_userid');
            var nm=localStorage.getItem('eng_app_name');
            if(id && nm && !window.location.hash.includes('id=')){
                parent.window.location.hash = 'id='+id+'&nm='+encodeURIComponent(nm);
            }
            </script>""", height=0)
        st.session_state.checked_storage = True

    q = st.query_params
    
    # パターンA: 以前のログイン情報が残っている場合
    if "id" in q and "nm" in q:
        u_id, u_name = q["id"], q["nm"]
        st.success(f"前回保存されたユーザー: **{u_name}**")
        st.write("どちらにしますか？")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔥 続きをする", use_container_width=True):
                d = fetch_user_data(u_id)
                if d:
                    st.session_state.user_id = u_id
                    st.session_state.user_name = u_name
                    st.session_state.streak = d["streak"]
                    st.session_state.last_clear = d["last_clear"]
                    st.session_state.learned_ids = d["learned_ids"]
                    st.session_state.phase = "init"
                    st.rerun()
                else:
                    st.error("データが見つかりませんでした。新しくログインしてください。")
        with col2:
            if st.button("👤 新しくログインする", use_container_width=True):
                st.query_params.clear()
                components.html("<script>localStorage.clear();</script>", height=0)
                st.rerun()
                
    # パターンB: 新規、または「新しくログイン」を選んだ場合
    else:
        st.info("お名前とパスワードを入力してください")
        n_in = st.text_input("なまえ").strip()
        p_in = st.text_input("パスワード", type="password")
        if st.button("🚀 ログイン / 登録", use_container_width=True):
            if n_in and p_in:
                u_id = get_user_id(n_in, p_in)
                d = fetch_user_data(u_id)
                if not d:
                    save_user_data(u_id, n_in, 0, "", [])
                    d = {"display_name": n_in, "streak": 0, "last_clear": "", "learned_ids": []}
                
                st.session_state.user_id = u_id
                st.session_state.user_name = n_in
                st.session_state.streak = d["streak"]
                st.session_state.last_clear = d["last_clear"]
                st.session_state.learned_ids = d["learned_ids"]
                
                # ブラウザに保存
                components.html(f"<script>localStorage.setItem('eng_app_userid','{u_id}');localStorage.setItem('eng_app_name','{n_in}');</script>", height=0)
                st.query_params["id"] = u_id
                st.query_params["nm"] = n_in
                st.session_state.phase = "init"
                st.rerun()
    st.stop()

# ==========================================
# 6. 以降の学習
