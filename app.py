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
        # csvの列名が正しいかチェック
        if 'word' not in w.columns or 'meaning' not in w.columns:
            st.error("words.csvに 'word' または 'meaning' 列が見当たりません。")
            st.stop()
        w['id'] = w['word'].astype(str) + "_" + w['meaning'].astype(str)
        return w, n
    except Exception as e:
        st.error("CSVファイルの読み込み中にエラーが発生しました: " + str(e))
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

# --- アプリ基本設定 ---
st.set_page_config(page_title="お笑い英語マスター Pro", page_icon="📝")

if "user_id" not in st.session_state: st.session_state.user_id = None
if "phase" not in st.session_state: st.session_state.phase = "login"
if "wrong_id" not in st.session_state: st.session_state.wrong_id = None

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
    if "id" in q and "nm" in q:
        u_id, u_name = q["id"], q["nm"]
        st.success("おかえりなさい！ " + str(u_name) + " さん")
        if st.button("🔥 続きから勉強をはじめる", use_container_width=True):
            d = get_user_data(u_id)
            if d:
                st.session_state.user_id = u_id
                st.session_state.user_name = u_name
                st.session_state.streak = d["streak"]
                st.session_state.last_clear = d["last_clear"]
                st.session_state.learned_ids = d["learned_ids"]
                st.session_state.phase = "init"
                st.rerun()
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
                st.session_state.user_id = u_id
                st.session_state.user_name = n_in
                st.session_state.streak = d["streak"]
                st.session_state.last_clear = d["last_clear"]
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
    if st.session_state.last_clear != yst and st.session_state.last_clear != today:
        st.session_state.streak = 0
    
    random.seed(int(today.replace("-", "")))
    # 学年(grade)が1のものを抽出。もしcsvにgrade列がない場合は全件から選ぶ。
    if 'grade' in WORDS_DF.columns:
        pool = WORDS_DF[WORDS_DF['grade'] == 1].copy()
    else:
        pool = WORDS_DF.copy()

    unlearned = pool[~pool['id'].isin(st.session_state.learned_ids)]
    target = unlearned if len(unlearned) >= 3 else pool
    
    st.session_state.p_list = target.sample(n=min(3, len(target))).to_dict('records')
    st.session_state.r_list = WORDS_DF.sample(n=min(3, len(WORDS_DF))).to_dict('records')
    st.session_state.neta = NETA_DF.sample(n=1).iloc[0]
    st.session_state.idx = 0
    st.session_state.phase = "practice"
    st.rerun()

# --- 共通サイドバー ---
st.sidebar.write("👤 " + str(st.session_state.user_name))
st.sidebar.write("🔥 " + str(st.session_state.streak) + " 日連続")

# --- 画面3: 練習 ---
if st.session_state.phase == "practice":
    idx = st.session_state.idx
    word = st.session_state.p_list[idx]
    st.subheader("Step 1: 練習 (" + str(idx+1) + "/3)")
    st.markdown("<h1 style='color:#FF4B4B; text-align:center;'>" + str(word['meaning']) + "</h1>", unsafe_allow_html=True)
    
    if st.button("🔊 お手本を聞く"): text_to_speech(word['word'])
    
    a1 = st.text_input("1回目", key="a1_" + str(idx)).strip().lower()
    a2 = st.text_input("2回目", key="a2_" + str(idx)).strip().lower()
    a3 = st.text_input("3回目", key="a3_" + str(idx)).strip().lower()
    
    correct = str(word['word']).lower()
    if a1 == correct and a2 == correct and a3 == correct:
        if st.button("次へ進む"):
            if word['id'] not in st.session_state.learned_ids:
                st.session_state.learned_ids.append(word['id'])
            st.session_state.idx += 1
            if st.session_state.idx >= 3:
                st.session_state.idx = 0
                st.session_state.phase = "test"
            st.rerun()

# --- 画面4: テスト ---
elif st.session_state.phase == "test":
    idx = st.session_state.idx
    word = st.session_state.r_list[idx]
    st.subheader("Step 2: 復習テスト (" + str(idx+1) + "/3)")
    st.markdown("<h1 style='color:#FF4B4B; text-align:center;'>" + str(word['meaning']) + "</h1>", unsafe_allow_html=True)

    if st.session_state.wrong_id == word['id']:
        st.error("特訓：正解は " + str(word['word']))
        t_ans = [st.text_input("特訓 " + str(i+1), key="t" + str(idx) + str(i)).strip().lower() for i in range(5)]
        if all(a == str(word['word']).lower() and a != "" for a in t_ans):
            if st.button("特訓クリア！"):
                st.session_state.wrong_id = None
                st.session_state.idx += 1
                if st.session_state.idx >= 3: st.session_state.phase = "goal"
                st.rerun()
    else:
        with st.form(key="test_form"):
            u_in = st.text_input("英語で？").strip().lower()
            if st.form_submit_button("判定"):
                if u_in == str(word['word']).lower():
                    st.session_state.idx += 1
                    if st.session_state.idx >= 3:
                        td = str(datetime.date.today())
                        if st.session_state.last_clear != td:
                            st.session_state.streak += 1
