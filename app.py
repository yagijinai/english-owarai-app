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

FIRESTORE_BASE_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_CONFIG['projectId']}/databases/(default)/documents/users"

# --- 便利機能 ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def text_to_speech(text):
    js_code = f"<script>var msg = new SpeechSynthesisUtterance(); msg.text = '{text}'; msg.lang = 'en-US'; window.speechSynthesis.speak(msg);</script>"
    components.html(js_code, height=0)

def set_local_storage(name, pwd):
    js_code = f"<script>localStorage.setItem('eng_app_user', '{name}'); localStorage.setItem('eng_app_pwd', '{pwd}');</script>"
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

# --- Firebase通信 ---
def get_user_all_data(username):
    url = f"{FIRESTORE_BASE_URL}/{username}"
    res = requests.get(url)
    if res.status_code == 200:
        f = res.json().get("fields", {})
        return {
            "password": f.get("password", {}).get("stringValue", ""),
            "streak": int(f.get("streak", {}).get("integerValue", 0)),
            "last_clear": f.get("last_clear", {}).get("stringValue", ""),
            "learned_ids": [v.get("stringValue") for v in f.get("learned_ids", {}).get("arrayValue", {}).get("values", [])]
        }
    return None

def save_user_full_data(username, password_hashed, streak, last_clear, learned_ids):
    url = f"{FIRESTORE_BASE_URL}/{username}"
    data = {
        "fields": {
            "password": {"stringValue": password_hashed},
            "streak": {"integerValue": streak},
            "last_clear": {"stringValue": last_clear},
            "learned_ids": {"arrayValue": {"values": [{"stringValue": i} for i in learned_ids]}}
        }
    }
    requests.patch(url, params={"updateMask.fieldPaths": ["password", "streak", "last_clear", "learned_ids"]}, json=data)

# --- メイン処理 ---
st.set_page_config(page_title="お笑い英語マスター Pro", page_icon="📝")

# ログイン状態の管理
if "user_name" not in st.session_state:
    # ページ中央に寄せるためのスタイル
    st.markdown("""
        <style>
        .main-title { font-size: 50px; color: #1E88E5; text-align: center; font-weight: bold; margin-bottom: 10px; }
        .sub-title { font-size: 20px; text-align: center; color: #555; margin-bottom: 30px; }
        .stButton>button { width: 100%; height: 60px; font-size: 20px; border-radius: 10px; }
        </style>
        """, unsafe_allow_html=True)

    st.markdown('<div class="main-title">English Master Pro</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">～ お笑い芸人と学ぶ、最強の英単語アプリ ～</div>', unsafe_allow_html=True)

    # ブラウザの保存情報を確認（JS）
    if "checked_local" not in st.session_state:
        components.html("""
            <script>
            var n = localStorage.getItem('eng_app_user');
            var p = localStorage.getItem('eng_app_pwd');
            if(n && p) { parent.window.location.hash = 'u=' + n + '&p=' + p; }
            else { parent.window.location.hash = 'start=true'; }
            </script>
        """, height=0)
        st.session_state.checked_local = True

    q = st.query_params
    
    # A. 自動ログイン可能な場合
    if "u" in q and "p" in q:
        saved_name = q["u"]
        st.markdown(f"<h3 style='text-align: center;'>おかえりなさい、{saved_name} さん！</h3>", unsafe_allow_html=True)
        if st.button("🔥 続きから勉強をはじめる"):
            data = get_user_all_data(saved_name)
            if data and data["password"] == q["p"]:
                st.session_state.user_name = saved_name
                st.session_state.streak = data["streak"]
                st.session_state.last_clear = data["last_clear"]
                st.session_state.learned_ids = data["learned_ids"]
                st.rerun()
            else:
                st.error("保存された情報が古いです。もう一度ログインしてください。")
                st.query_params.clear()
                st.rerun()
        
        if st.button("👤 別の名前でログイン・登録"):
            st.query_params.clear()
            st.rerun()

    # B. 新規または情報がない場合
    else:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔑 ログイン"): st.session_state.mode = "login"
        with col2:
            if st.button("✨ 新しくつくる"): st.session_state.mode = "signup"

        # ログイン入力画面
        if st.session_state.get("mode") == "login":
            st.markdown("---")
            l_name = st.text_input("名前").strip()
            l_pwd = st.text_input("パスワード", type="password")
            if st.button("ログインする"):
                data = get_user_all_data(l_name)
                if data and data["password"] == hash_password(l_pwd):
                    st.session_state.user_name = l_name
                    st.session_state.streak = data["streak"]
                    st.session_state.last_clear = data["last_clear"]
                    st.session_state.learned_ids = data["learned_ids"]
                    set_local_storage(l_name, data["password"])
                    st.rerun()
                else: st.error("名前かパスワードが違います")

        # 新規登録入力画面
        elif st.session_state.get("mode") == "signup":
            st.markdown("---")
            n_name = st.text_input("新しい名前").strip()
            n_pwd = st.text_input("新しいパスワード", type="password")
            if st.button("登録してスタート！"):
                if n_name and n_pwd:
                    if get_user_all_data(n_name): st.error("その名前はすでに使われています")
                    else:
                        hpwd = hash_password(n_pwd)
                        save_user_full_data(n_name, hpwd, 0, "", [])
                        st.session_state.user_name = n_name
                        st.session_state.streak = 0
                        st.session_state.last_clear = ""
                        st.session_state.learned_ids = []
                        set_local_storage(n_name, hpwd)
                        st.rerun()
    st.stop()

# --- 学習画面 (ロジックは維持) ---
username = st.session_state.user_name
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
    st.session_state.phase = "new"; st.session_state.current_word_idx = 0; st.session_state.review_idx = 0; st.session_state.wrong_word_id = None; st.session_state.init_done = True

st.markdown(f"### 👤 {username} | 🔥 {st.session_state.streak} 日連続")

# 学習フェーズの表示
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
    if st.button("🔊 発音を聞く"): text_to_speech(word['word'])
    u_ans = st.text_input("英語で？", key=f"rv_{r_idx}").strip().lower()
    if u_ans != "" and u_ans == str(word['word']).lower():
        if st.button("正解！次へ"):
            if st.session_state.last_clear != today_str:
                st.session_state.streak += 1
                st.session_state.last_clear = today_str
            # 現在のパスワードハッシュを再取得して保存
            curr_data = get_user_all_data(username)
            save_user_full_data(username, curr_data["password"], st.session_state.streak, st.session_state.last_clear, st.session_state.learned_ids)
            st.session_state.review_idx += 1
            if st.session_state.review_idx >= 3: st.session_state.phase = "goal"
            st.rerun()
    elif u_ans != "": st.error("ミス！特訓です")

elif st.session_state.phase == "goal":
    st.header("🎉 ミッション完了！")
    st.balloons()
    st.success(f"【{st.session_state.daily_neta['comedian']}】\n\n{st.session_state.daily_neta['fact']}")
    if st.button("ログアウトして終了"):
        st.query_params.clear()
        components.html("<script>localStorage.clear();</script>", height=0)
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()
