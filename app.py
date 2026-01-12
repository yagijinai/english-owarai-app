import streamlit as st
import pandas as pd
import datetime
import random
import requests
import json
import streamlit.components.v1 as components
import hashlib

# ==========================================
# 1. アプリ設定と基本機能
# ==========================================
st.set_page_config(page_title="お笑い英語マスター Pro", page_icon="📝")

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
            return None, None, "CSVファイルの中身が空です。"
        w_df['id'] = w_df['word'].astype(str) + "_" + w_df['meaning'].astype(str)
        return w_df, n_df, None
    except Exception as e:
        return None, None, "ファイルの読み込みエラー: " + str(e)

WORDS_DF, NETA_DF, LOAD_ERROR = load_app_data()

# ==========================================
# 3. データベース操作 (Firestore)
# ==========================================
def get_remote_data(uid):
    url = FIRESTORE_URL + "/" + uid
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            f = res.json().get("fields", {})
            d_name = f.get("display_name", {}).get("stringValue", "User")
            streak = int(f.get("streak", {}).get("integerValue", 0))
            last_c = f.get("last_clear", {}).get("stringValue", "")
            l_ids = []
            l_raw = f.get("learned_ids", {}).get("arrayValue", {}).get("values", [])
            for v in l_raw:
                s = v.get("stringValue")
                if s: l_ids.append(s)
            return {"name": d_name, "streak": streak, "last_clear": last_c, "learned_ids": l_ids}
    except:
        pass
    return None

def save_remote_data(uid, name, streak, last, l_ids):
    url = FIRESTORE_URL + "/" + uid
    id_values = []
    for i in l_ids:
        id_values.append({"stringValue": str(i)})
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
# 4. セッション（状態管理）の初期化
# ==========================================
if "phase" not in st.session_state:
    st.session_state.phase = "login"
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.streak = 0
    st.session_state.last_clear = ""
    st.session_state.learned_ids = []
    st.session_state.idx = 0
    st.session_state.p_list = []
    st.session_state.r_list = []
    st.session_state.is_correct_feedback = False
    st.session_state.show_hint = False
    st.session_state.tokkun_word = None

# ==========================================
# 5. 画面：ログイン
# ==========================================
if st.session_state.phase == "login":
    st.title("English Master Pro")
    
    # ブラウザ保存からの自動復帰用
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
        st.success(u_nm + " さん、おかえりなさい！")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔥 学習をはじめる", use_container_width=True):
                data = get_remote_data(u_id)
                if data:
                    st.session_state.user_id, st.session_state.user_name = u_id, u_nm
                    st.session_state.streak, st.session_state.last_clear = data["streak"], data["last_clear"]
                    st.session_state.learned_ids = data["learned_ids"]
                    st.session_state.phase = "init"
                    st.rerun()
        with c2:
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
                data = get_remote_data(u_id) or {"name": n_in, "streak": 0, "last_clear": "", "learned_ids": []}
                st.session_state.user_id, st.session_state.user_name = u_id, n_in
                st.session_state.streak, st.session_state.last_clear = data["streak"], data["last_clear"]
                st.session_state.learned_ids = data["learned_ids"]
                components.html("<script>localStorage.setItem('eng_id','"+u_id+"');localStorage.setItem('eng_nm','"+n_in+"');</script>", height=0)
                st.query_params["id"], st.query_params["nm"] = u_id, n_in
                st.session_state.phase = "init"
                st.rerun()
    st.stop()

if LOAD_ERROR:
    st.error(LOAD_ERROR)
    st.stop()

# ==========================================
# 6. 画面：データ初期化 (init)
# ==========================================
if st.session_state.phase == "init":
    today = str(datetime.date.today())
    yst = str(datetime.date.today() - datetime.timedelta(days=1))
    if st.session_state.last_clear != yst and st.session_state.last_clear != today:
        st.session_state.streak = 0
    
    random.seed(int(today.replace("-", "")))
    # 練習用（未学習から3つ）
    not_learned = WORDS_DF[~WORDS_DF['id'].isin(st.session_state.learned_ids)]
    if len(not_learned) < 3: not_learned = WORDS_DF
    st.session_state.p_list = not_learned.sample(n=min(3, len(not_learned))).to_dict('records')
    # テスト用（全データから3つ）
    st.session_state.r_list = WORDS_DF.sample(n=min(3, len(WORDS_DF))).to_dict('records')
    st.session_state.
