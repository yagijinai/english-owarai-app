import streamlit as st
import pandas as pd
import datetime
import random
import requests
import json
import streamlit.components.v1 as components
import hashlib

# ==========================================
# 1. アプリ基本設定
# ==========================================
st.set_page_config(page_title="お笑い英語マスター Pro", page_icon="📝")

FIREBASE_CONFIG = {"projectId": "english-ap"}
FIRESTORE_URL = "https://firestore.googleapis.com/v1/projects/english-ap/databases/(default)/documents/users"

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def get_user_id(name, pw):
    combined = name + "_" + hash_password(pw)
    return combined[:50]

def text_to_speech(text):
    clean_text = str(text).replace("'", "")
    js_code = """
    <script>
    var msg = new SpeechSynthesisUtterance();
    msg.text = '""" + clean_text + """';
    msg.lang = 'en-US';
    window.speechSynthesis.speak(msg);
    </script>
    """
    components.html(js_code, height=0)

# ==========================================
# 2. データの読み込み
# ==========================================
@st.cache_data
def load_app_data():
    try:
        w_df = pd.read_csv('words.csv')
        n_df = pd.read_csv('neta.csv')
        if w_df.empty or n_df.empty:
            return None, None, "CSVファイルが空っぽです。"
        w_df['id'] = w_df['word'].astype(str) + "_" + w_df['meaning'].astype(str)
        return w_df, n_df, None
    except Exception as e:
        return None, None, "ファイルの読み込みに失敗しました: " + str(e)

WORDS_DF, NETA_DF, LOAD_ERROR = load_app_data()

# ==========================================
# 3. データベース（Firestore）操作
# ==========================================
def get_remote_data(uid):
    url = FIRESTORE_URL + "/" + uid
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            fields = res.json().get("fields", {})
            d_name = fields.get("display_name", {}).get("stringValue", "User")
            streak = int(fields.get("streak", {}).get("integerValue", 0))
            last_c = fields.get("last_clear", {}).get("stringValue", "")
            l_ids = []
            l_raw = fields.get("learned_ids", {}).get("arrayValue", {}).get("values", [])
            for v in l_raw:
                s = v.get("stringValue")
                if s: l_ids.append(s)
            return {"name": d_name, "streak": streak, "last_clear": last_c, "learned_ids": l_ids}
    except:
        pass
    return None

def save_remote_data(uid, name, streak, last, l_ids):
    url = FIRESTORE_URL + "/" + uid
    id_values = [{"stringValue": str(i)} for i in l_ids]
    payload = {
        "fields": {
            "display_name": {"stringValue": str(name)},
            "streak": {"integerValue": int(streak)},
            "last_clear": {"stringValue": str(last)},
            "learned_ids": {"arrayValue": {"values": id_values}}
        }
    }
    try:
        requests.patch(url, json=payload, timeout=5)
    except:
        pass

# ==========================================
# 4. セッション（記憶）の初期化
# ==========================================
if "phase" not in st.session_state:
    st.session_state.phase = "login"
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.streak = 0
    st.session_state.last_clear = ""
    st.session_state.learned_ids = []
    st.session_state.is_correct_feedback = False
    st.session_state.show_hint = False
    st.session_state.tokkun_word = None # 特訓中の単語

# ==========================================
# 5. 画面：ログイン
# ==========================================
if st.session_state.phase == "login":
    st.title("English Master Pro")
    if "checked_storage" not in st.session_state:
        components.html("""
            <script>
            var id = localStorage.getItem('eng_id');
            var nm = localStorage.getItem('eng_nm');
            if(id && nm && !window.location.hash.includes('id=')){
                parent.window.location.hash = 'id=' + id + '&nm=' + encodeURIComponent(nm);
            }
            </script>
        """, height=0)
        st.session_state.checked_storage = True

    params = st.query_params
    if "id" in params and "nm" in params:
        u_id, u_nm = params["id"], params["nm"]
        st.success("おかえりなさい！ **" + u_nm + "** さん")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔥 続きをする", use_container_width=True):
                data = get_remote_data(u_id)
                if data:
                    st.session_state.user_id, st.session_state.user_name = u_id, u_nm
                    st.session_state.streak, st.session_state.last_clear = data["streak"], data["last_clear"]
                    st.session_state.learned_ids = data["learned_ids"]
                    st.session_state.phase = "init"
                    st.rerun()
        with col2:
            if st.button("👤 別の人でログイン", use_container_width=True):
                st.query_params.clear()
                components.html("<script>localStorage.clear();</script>", height=0)
                st.rerun()
    else:
        n_in = st.text_input("なまえ").strip()
        p_in = st.text_input("パスワード", type="password")
        if st.button("🚀 はじめる", use_container_width=True):
            if n_in and p_in:
                u_id = get_user_id(n_in, p_in)
                data = get_remote_data(u_id)
                if not data:
                    save_remote_data(u_id, n_in, 0, "", [])
                    data = {"name": n_in, "streak": 0, "last_clear": "", "learned_ids": []}
                st.session_state.user_id, st.session_state.user_name = u_id, n_in
                st.session_state.streak, st.session_state.last_clear = data["streak"], data["last_clear"]
                st.session_state.learned_ids = data["learned_ids"]
                components.html("<script>localStorage.setItem('eng_id','" + u_id + "');localStorage.setItem('eng_nm','" + n_in + "');</script>", height=0)
                st.query_params["id"], st.query_params["nm"] = u_id, n_in
                st.session_state.phase = "init"
                st.rerun()
    st.stop()

if LOAD_ERROR:
    st.error(LOAD_ERROR)
    st.stop()

# ==========================================
# 6. 画面：初期化 (init)
# ==========================================
if st.session_state.phase == "init":
    today = str(datetime.date.today())
    yst = str(datetime.date.today() - datetime.timedelta(days=1))
    if st.session_state.last_clear != yst and st.session_state.last_clear != today:
        st.session_state.streak = 0
    random.seed(int(today.replace("-", "")))
    not_learned = WORDS_DF[~WORDS_DF['id'].isin(st.session_state.learned
