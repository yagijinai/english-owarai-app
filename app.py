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
    js_code = f"<script>localStorage.setItem('eng_app_userid', '{user_id}'); localStorage.setItem('eng_app_name', '{display_name}');</script>"
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

# --- ログイン画面 ---
st.set_page_config(page_title="お笑い英語マスター Pro", page_icon="📝")

if "user_id" not in st.session_state:
    st.markdown("""<style>.main-title { font-size: 50px; color: #1E88E5; text-align: center; font-weight: bold; }
    .sub-title { font-size: 20px; text-align: center; color: #555; margin-bottom: 30px; }
    .stButton>button { width: 100%; height: 60px; font-size: 20px; }</style>""", unsafe_allow_html=True)
    st.markdown('<div class="main-title">English Master Pro</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">～ お笑い芸人と学ぶ、最強の英単語アプリ ～</div>', unsafe_allow_html=True)

    if "checked_local" not in st.session_state:
        components.html("""<script>
            var id = localStorage.getItem('eng_app_userid');
            var nm = localStorage.getItem('eng_app_name');
            if(id && nm) { parent.window.location.hash = 'id=' + id + '&nm=' + nm; }
            </script>""", height=0)
        st.session_state.checked_local = True

    q = st.query_params
    if "id" in q and "nm" in q:
        user_id, display_name = q["id"], q["nm"]
        st.markdown(f"<h3 style='text-align: center;'>おかえりなさい、{display_name} さん！</h3>", unsafe_allow_html=True)
        if st.button("🔥 続きから勉強をはじめる"):
            data = get_user_data_by_id(user_id)
            if data:
                st.session_state.user_id, st.session_state.user_name = user_id, display_name
                st.session_state.streak, st.session_state.last_clear = data["streak"], data["last_clear"]
                st.session_state.learned_ids = data["learned_ids"]
                st.rerun()
        if st.button("👤 別の名前でログイン"):
            st.query_params.clear()
            st.rerun()
    else:
        name_input = st.text_input("名前（例：てつじ）").strip()
        pwd_input = st.text_input("パスワード", type="password")
        if st.button("はじめる"):
            if name_input and pwd_input:
                u_id = get_user_id(name_input, pwd_input)
                data = get_user_data_by_id(u_id)
                if not data:
                    data = {"display_name": name_input, "streak": 0, "last_clear": "", "learned_ids": []}
                    save_user_data_by_id(u_id, name_input, 0, "", [])
                st.session_state.user_id, st.session_state.user_name = u_id, name_input
                st.session_state.streak, st.session_state.last_clear = data["streak"], data["last_clear"]
                st.session_state.learned_ids = data["learned_ids"]
                set_local_storage(u_id, name_input)
                st.rerun()
            else: st.warning("名前とパスワードを入れてね！")
    st.stop()

# --- 学習ロジック ---
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
    st.session_state.phase = "new"; st.session_state.current_word_idx = 0; st.session_state.review_idx = 0; st.session_state.wrong_word_id = None; st.session_state.init_done = True

st.markdown(f"### 👤 {username} | 🔥 {st.session_state.streak} 日連続")

# --- フェーズ1: 練習 ---
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

# --- フェーズ2: 復習テスト ---
elif st.session_state.phase == "review":
    r_idx = st.session_state.review_idx
    word = st.session_state.review_queue[r_idx]
    st.subheader(f"Step 2: 復習テスト ({r_idx+1}/3)")
    st.markdown(f"<h1 style='color: #FF4B4B; text-align: center;'>{word['meaning']}</h1>", unsafe_allow_html=True)
    
    # 【重要】特訓モードの処理
    if st.session_state.wrong_word_id == word['id']:
        st.error(f"ミス！特訓です。正解は「{word['word']}」")
        if st.button("🔊 正解の音を聞く"): text_to_speech(word['word'])
        t_ans = [st.text_input(f"特訓 {i+1}/5", key=f"t_{r_idx}_{i}").strip().lower() for i in range(5)]
        if all(a == str(word['word']).lower() and a != "" for a in t_ans):
            if st.button("特訓クリア！次へ"):
                st.session_state.wrong_word_id = None
                st.session_state.review_idx += 1
                if st.session_state.review_idx >= 3: st.session_state.phase = "goal"
                st.rerun()
    else:
        u_ans = st.text_input("英語で？", key=f"rv_{r_idx}").strip().lower()
        if u_ans != "" and u_ans == str(word['word']).lower():
            if st.button("正解！次へ"):
                if st.session_state.last_clear != today_str:
                    st.session_state.streak += 1
                    st.session_state.last_clear = today_str
                save_user_data_by_id(userid, username, st.session_state.streak, st.session_state.last_clear, st.session_state.learned_ids)
                st.session_state.review_idx += 1
                if st.session_state.review_idx >= 3: st.session_state.phase = "goal"
                st.rerun()
        elif u_ans != "":
            # 間違えたらその単語のIDをセットしてリラン（これで特訓画面が出る）
            st.session_state.wrong_word_id = word['id']
            st.rerun()

# --- フェーズ3: ゴール ---
elif st.session_state.phase == "goal":
    st.header("🎉 ミッション完了！")
    st.balloons()
    st.success(f"【{st.session_state.daily_neta['comedian']}】\n\n{st.session_state.daily_neta['fact']}")
    if st.button("終了"):
        st.query_params.clear()
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()
