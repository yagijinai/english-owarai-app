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

# Firebase設定
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
    st.session_state.tokkun_word = None # 特訓が必要な単語

# ==========================================
# 5. 画面：ログイン
# ==========================================
if st.session_state.phase == "login":
    st.title("English Master Pro")
    
    # ブラウザ記憶のチェック
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
        u_id = params["id"]
        u_nm = params["nm"]
        st.success("おかえりなさい！ **" + u_nm + "** さん")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔥 続きをする", use_container_width=True):
                data = get_remote_data(u_id)
                if data:
                    st.session_state.user_id = u_id
                    st.session_state.user_name = u_nm
                    st.session_state.streak = data["streak"]
                    st.session_state.last_clear = data["last_clear"]
                    st.session_state.learned_ids = data["learned_ids"]
                    st.session_state.phase = "init"
                    st.rerun()
        with c2:
            if st.button("👤 別の人でログイン", use_container_width=True):
                st.query_params.clear()
                components.html("<script>localStorage.clear();</script>", height=0)
                st.rerun()
    else:
        st.info("なまえとパスワードを決めて入力してね！")
        n_in = st.text_input("なまえ").strip()
        p_in = st.text_input("パスワード", type="password")
        if st.button("🚀 はじめる", use_container_width=True):
            if n_in and p_in:
                u_id = get_user_id(n_in, p_in)
                data = get_remote_data(u_id)
                if not data:
                    save_remote_data(u_id, n_in, 0, "", [])
                    data = {"name": n_in, "streak": 0, "last_clear": "", "learned_ids": []}
                st.session_state.user_id = u_id
                st.session_state.user_name = n_in
                st.session_state.streak = data["streak"]
                st.session_state.last_clear = data["last_clear"]
                st.session_state.learned_ids = data["learned_ids"]
                js_save = "<script>localStorage.setItem('eng_id','" + u_id + "');localStorage.setItem('eng_nm','" + n_in + "');</script>"
                components.html(js_save, height=0)
                st.query_params["id"] = u_id
                st.query_params["nm"] = n_in
                st.session_state.phase = "init"
                st.rerun()
    st.stop()

if LOAD_ERROR:
    st.error(LOAD_ERROR)
    st.stop()

# ==========================================
# 6. 画面：初期化（学習準備）
# ==========================================
if st.session_state.phase == "init":
    today = str(datetime.date.today())
    yst = str(datetime.date.today() - datetime.timedelta(days=1))
    if st.session_state.last_clear != yst and st.session_state.last_clear != today:
        st.session_state.streak = 0
    
    random.seed(int(today.replace("-", "")))
    
    # 未学習単語から3つ選ぶ
    not_learned = WORDS_DF[~WORDS_DF['id'].isin(st.session_state.learned_ids)]
    if len(not_learned) < 3:
        not_learned = WORDS_DF
    
    st.session_state.p_list = not_learned.sample(n=min(3, len(not_learned))).to_dict('records')
    # 復習用リスト
    st.session_state.r_list = WORDS_DF.sample(n=min(3, len(WORDS_DF))).to_dict('records')
    st.session_state.neta = NETA_DF.sample(n=1).iloc[0]
    st.session_state.idx = 0
    st.session_state.phase = "practice"
    st.rerun()

st.sidebar.write("👤 " + str(st.session_state.user_name))
st.sidebar.write("🔥 " + str(st.session_state.streak) + " 日目")

# ==========================================
# 7. 画面：練習（Step 1）
# ==========================================
if st.session_state.phase == "practice":
    word = st.session_state.p_list[st.session_state.idx]
    st.subheader("Step 1: 練習 (" + str(st.session_state.idx + 1) + "/3)")
    st.markdown("<h1 style='color:#FF4B4B; text-align:center;'>" + str(word['meaning']) + "</h1>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔊 音を聞く", use_container_width=True): text_to_speech(word['word'])
    with c2:
        if st.button("👀 見本を見る", use_container_width=True): st.session_state.show_hint = not st.session_state.show_hint
    
    if st.session_state.show_hint:
        st.info("こたえ: " + str(word['word']))
    
    st.write("下に3回同じ英単語を書いてね！")
    a1 = st.text_input("1回目", key="p1_" + str(st.session_state.idx)).strip().lower()
    a2 = st.text_input("2回目", key="p2_" + str(st.session_state.idx)).strip().lower()
    a3 = st.text_input("3回目", key="p3_" + str(st.session_state.idx)).strip().lower()
    
    target = str(word['word']).lower()
    if a1 == target and a2 == target and a3 == target:
        if st.button("できた！次の単語へ", use_container_width=True):
            if word['id'] not in st.session_state.learned_ids:
                st.session_state.learned_ids.append(word['id'])
            st.session_state.idx += 1
            st.session_state.show_hint = False
            if st.session_state.idx >= 3:
                st.session_state.idx = 0
                st.session_state.phase = "test"
            st.rerun()

# ==========================================
# 8. 画面：復
