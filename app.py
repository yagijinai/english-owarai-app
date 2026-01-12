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
    combined = f"{name}_{hash_password(password)}"
    return combined[:50]

FIRESTORE_BASE_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_CONFIG['projectId']}/databases/(default)/documents/users"

# --- 便利機能 ---
def text_to_speech(text):
    js_code = f"<script>var msg = new SpeechSynthesisUtterance(); msg.text = '{text}'; msg.lang = 'en-US'; window.speechSynthesis.speak(msg);</script>"
    components.html(js_code, height=0)

def set_local_storage(user_id, display_name):
    # JavaScriptで確実に保存
    js_code = f"""
    <script>
    localStorage.setItem('eng_app_userid', '{user_id}');
    localStorage.setItem('eng_app_name', '{display_name}');
    console.log('Saved to localStorage');
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

# --- 画面構成 ---
st.set_page_config(page_title="お笑い英語マスター Pro", page_icon="📝")

# 状態の初期化
if "wrong_word_id" not in st.session_state: st.session_state.wrong_word_id = None
if "login_success" not in st.session_state: st.session_state.login_success = False

# メインのログイン判定
if not st.session_state.login_success:
    st.markdown("""<style>
    .main-title { font-size: 50px; color: #1E88E5; text-align: center; font-weight: bold; }
    .sub-title { font-size: 18px; text-align: center; color: #555; margin-bottom: 40px; }
    div.stButton > button { width: 100%; height: 70px; font-size: 22px; font-weight: bold; border-radius: 15px; }
    </style>""", unsafe_allow_html=True)
    
    st.markdown('<div class="main-title">English Master Pro</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">～ お笑い芸人と学ぶ、最強の英単語アプリ ～</div>', unsafe_allow_html=True)

    # ブラウザの保存情報をチェック
    if "check_js" not in st.session_state:
        components.html("""
            <script>
            var id = localStorage.getItem('eng_app_userid');
            var nm = localStorage.getItem('eng_app_name');
            if(id && nm && !window.location.hash.includes('id=')) {
                parent.window.location.hash = 'id=' + id + '&nm=' + encodeURIComponent(nm);
            }
            </script>
        """, height=0)
        st.session_state.check_js = True

    q = st.query_params
    
    # パターン1: 「おかえり」状態
    if "id" in q and "nm" in q:
        u_id, u_name = q["id"], q["nm"]
        st.success(f"おかえりなさい！ {u_name} さん")
        if st.button("🔥 続きから勉強をはじめる"):
            data = get_user_data_by_id(u_id)
            if data:
                st.session_state.user_id = u_id
                st.session_state.user_name = u_name
                st.session_state.streak = data["streak"]
                st.session_state.last_clear = data["last_clear"]
                st.session_state.learned_ids = data["learned_ids"]
                st.session_state.login_success = True
                st.rerun()
        
        if st.button("👤 別のなまえでログイン"):
            st.query_params.clear()
            components.html("<script>localStorage.clear();</script>", height=0)
            st.rerun()

    # パターン2: 新規ログイン入力
    else:
        n_input = st.text_input("なまえ").strip()
        p_input = st.text_input("パスワード", type="password")
        if st.button("🚀 ログイン / 新規登録"):
            if n_input and p_input:
                u_id = get_user_id(n_input, p_input)
                data = get_user_data_by_id(u_id)
                if not data:
                    save_user_data_by_id(u_id, n_input, 0, "", [])
                    data = {"display_name": n_input, "streak": 0, "last_clear": "", "learned_ids": []}
                
                # 情報保存
                st.session_state.user_id = u_id
                st.session_state.user_name = n_input
                st.session_state.streak = data["streak"]
                st.session_state.last_clear = data["last_clear"]
                st.session_state.learned_ids = data["learned_ids"]
                
                set_local_storage(u_id, n_input)
                st.query_params["id"] = u_id
                st.query_params["nm"] = n_input
                
                # ここで一回成功フラグを立ててからリラン
                st.session_state.login_success = True
                st.rerun()
    st.stop()

# --- 学習メイン画面 ---
username, userid = st.session_state.user_name, st.session_state.user_id
today_str = str(datetime.date.today())
yesterday_str = str(datetime.date.today() - datetime.timedelta(days=1))

if "init_done" not in st.session_state:
    if st.session_state.last_clear != yesterday_str and st.session_state.last_clear != today_str:
        st.session_state.streak = 0
    random.seed(int(today_str.replace("-", "")))
    grade_pool = WORDS_DF[WORDS_DF['grade'] == 1]
    unlearned_pool = grade_pool[~grade_pool['id'].isin(st.session_state.learned_ids)]
    if len(unlearned_pool) < 3: unlearned_pool = grade_pool
    st.session_state.daily_practice_words = unlearned_pool.sample(n=3).to_dict('records')
    st.session_state.review_queue = WORDS_DF.sample(n=3).to_dict('records')
    st.session_state.daily_neta = NETA_DF.sample(n=1).iloc[0]
    st.session_state.phase = "new"; st.session_state.current_word_idx = 0; st.session_state.review_idx = 0; st.session_state.init_done = True

st.markdown(f"### 👤 {username} | 🔥 {st.session_state.streak} 日連続")

if st.session_state.phase == "new":
    idx = st.session_state.current_word_idx
    word = st.session_state.daily_practice_words[idx]
    st.subheader(f"Step 1: 練習 ({idx+1}/3)")
    st.markdown(f"<h1 style='color: #FF4B4B; text-align: center;'>{word['meaning']}</h1>", unsafe_allow_html=True)
    if st.button("🔊 音を聞く"): text_to_speech(word['word'])
    ans = [st.text_input(f"{i+1}回目", key=f"p_{idx}_{i}").strip().lower() for i in range(3)]
    if all(a == str(word['word']).lower() and a != "" for a in ans):
        if st.button("次へ"):
            if word['id'] not in st.session_state.learned_ids: st.session_state.learned_ids.append(word['id'])
            st.session_state.current_word_idx += 1
            if st.session_state.current_word_idx >= 3: st.session_state.phase = "review"
            st.rerun()

elif st.session_state.phase == "review":
    r_idx = st.session_state.review_idx
    word = st.session_state.review_queue[r_idx]
    st.subheader(f"Step 2: 復習テスト ({r_idx+1}/3)")
    st.markdown(f"<h1 style='color: #FF4B4B; text-align: center;'>{word['meaning']}</h1>", unsafe_allow_html=True)
    if st.session_state.wrong_word_id == word['id']:
        st.error(f"ミス！特訓です。正解は「{word['word']}」")
        if st.button("🔊 正解の音を聞く"): text_to_speech(word['word'])
        t_ans = [st.text_input(f"特訓 {i+1}/5", key=f"t_{r_idx}_{i}").strip().lower() for i in range(5)]
        if all(a == str(word['word']).lower() and a != "" for a in t_ans):
            if st.button("特訓クリア！次へ"):
                st.session_state.wrong_word_id = None
                st.session_state.review_idx += 1
                if st.session_state.review_idx >= 3:
