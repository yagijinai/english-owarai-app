import streamlit as st
import pandas as pd
import datetime
import random
import requests
import json

# --- Firebase 設定 (お父様の設定値を反映済み) ---
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyB0Bd8aBmos2fHiD7XgH_S4yM5b__FHypI",
    "authDomain": "english-ap.firebaseapp.com",
    "projectId": "english-ap",
    "storageBucket": "english-ap.firebasestorage.app",
    "messagingSenderId": "167152900538",
    "appId": "1:167152900538:web:07a87314d3121c23eca583",
    "measurementId": "G-PEH3BVTK4H"
}

# REST APIを使ってFirestoreを操作するためのベースURL
FIRESTORE_BASE_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_CONFIG['projectId']}/databases/(default)/documents/users"

# --- データの読み込み ---
@st.cache_data
def load_data():
    try:
        words_df = pd.read_csv('words.csv')
        neta_df = pd.read_csv('neta.csv')
        words_df['id'] = words_df['word'] + "_" + words_df['meaning']
        return words_df, neta_df
    except Exception as e:
        st.error("words.csv または neta.csv が見つかりません。")
        st.stop()

WORDS_DF, NETA_DF = load_data()

# --- Firebaseとの通信関数 ---
def get_user_data(username):
    """サーバーからユーザー情報を取得"""
    url = f"{FIRESTORE_BASE_URL}/{username}"
    res = requests.get(url)
    if res.status_code == 200:
        fields = res.json().get("fields", {})
        return {
            "streak": int(fields.get("streak", {}).get("integerValue", 0)),
            "last_clear": fields.get("last_clear", {}).get("stringValue", ""),
            "learned_ids": [v.get("stringValue") for v in fields.get("learned_ids", {}).get("arrayValue", {}).get("values", [])]
        }
    return {"streak": 0, "last_clear": "", "learned_ids": []}

def save_user_data(username, streak, last_clear, learned_ids):
    """サーバーへユーザー情報を保存"""
    url = f"{FIRESTORE_BASE_URL}/{username}"
    data = {
        "fields": {
            "streak": {"integerValue": streak},
            "last_clear": {"stringValue": last_clear},
            "learned_ids": {"arrayValue": {"values": [{"stringValue": i} for i in learned_ids]}}
        }
    }
    requests.patch(url, params={"updateMask.fieldPaths": ["streak", "last_clear", "learned_ids"]}, json=data)

# --- アプリのメイン処理 ---
st.set_page_config(page_title="お笑い英語マスター Pro", page_icon="🔥")

# 1. ログイン画面
if "user_name" not in st.session_state:
    st.title("🔥 お笑い英語マスター")
    name = st.text_input("名前を入力してね（例：たろう）").strip()
    if st.button("はじめる"):
        if name:
            st.session_state.user_name = name
            # サーバーからデータ取得
            user_data = get_user_data(name)
            st.session_state.streak = user_data["streak"]
            st.session_state.last_clear = user_data["last_clear"]
            st.session_state.learned_ids = user_data["learned_ids"]
            st.rerun()
        else:
            st.warning("名前を入れてね！")
    st.stop()

# ログイン後の初期化
username = st.session_state.user_name
today_str = str(datetime.date.today())
yesterday_str = str(datetime.date.today() - datetime.timedelta(days=1))

if "init_done" not in st.session_state:
    # 連続日数の更新ロジック
    if st.session_state.last_clear == yesterday_str:
        pass # 継続中（クリア時に加算）
    elif st.session_state.last_clear == today_str:
        pass # 今日はもうクリア済み
    else:
        st.session_state.streak = 0 # 1日以上空いたらリセット

    # 今日の問題をセット
    random.seed(int(today_str.replace("-", "")))
    grade_pool = WORDS_DF[WORDS_DF['grade'] == 1] # 学年判定は1固定
    unlearned_pool = grade_pool[~grade_pool['id'].isin(st.session_state.learned_ids)]
    if len(unlearned_pool) < 3: unlearned_pool = grade_pool
    
    st.session_state.daily_practice_words = unlearned_pool.sample(n=3).to_dict('records')
    st.session_state.review_queue = WORDS_DF.sample(n=3).to_dict('records')
    st.session_state.daily_neta = NETA_DF.sample(n=1).iloc[0]
    st.session_state.phase = "new"
    st.session_state.current_word_idx = 0
    st.session_state.review_idx = 0
    st.session_state.wrong_word_id = None
    st.session_state.init_done = True

# UI表示
st.markdown(f"### 👤 ユーザー: {username}")
st.markdown(f"<p style='text-align: right; font-weight: bold;'>🔥 連続 {st.session_state.streak} 日目</p>", unsafe_allow_html=True)

# --- 学習フェーズ ---
if st.session_state.phase == "new":
    idx = st.session_state.current_word_idx
    words = st.session_state.daily_practice_words
    if idx >= len(words):
        st.session_state.phase = "review"
        st.rerun()
    
    word = words[idx]
    st.subheader(f"Step 1: 練習 ({idx+1}/3)")
    st.markdown(f"<h1 style='color: #FF4B4B; text-align: center;'>{word['meaning']}</h1>", unsafe_allow_html=True)
    
    if st.button("ヒント"): st.info(f"つづり: {word['word']}")
    
    ans = [st.text_input(f"{i+1}回目", key=f"p_{idx}_{i}").strip().lower() for i in range(3)]
    if all(a == str(word['word']).lower() and a != "" for a in ans):
        if st.button("次へ"):
            if word['id'] not in st.session_state.learned_ids:
                st.session_state.learned_ids.append(word['id'])
            st.session_state.current_word_idx += 1
            st.rerun()

elif st.session_state.phase == "review":
    r_idx = st.session_state.review_idx
    queue = st.session_state.review_queue
    if r_idx >= len(queue):
        st.session_state.phase = "goal"
        st.rerun()
    
    word = queue[r_idx]
    st.subheader(f"Step 2: 復習テスト ({r_idx+1}/{len(queue)})")
    st.markdown(f"<h1 style='color: #FF4B4B; text-align: center;'>{word['meaning']}</h1>", unsafe_allow_html=True)

    if st.session_state.wrong_word_id == word['id']:
        st.warning(f"正解は {word['word']} です")
        t_ans = [st.text_input(f"特訓 {i+1}/5", key=f"t_{r_idx}_{i}").strip().lower() for i in range(5)]
        if all(a == str(word['word']).lower() and a != "" for a in t_ans):
            if st.button("特訓クリア"):
                st.session_state.wrong_word_id = None
                st.session_state.review_idx += 1
                st.rerun()
    else:
        u_ans = st.text_input("答えを入力", key=f"rv_{r_idx}").strip().lower()
        if u_ans != "" and u_ans == str(word['word']).lower():
            if st.button("正解！次へ"):
                # ここでサーバーに保存！
                if st.session_state.last_clear != today_str:
                    st.session_state.streak += 1
                    st.session_state.last_clear = today_str
                
                save_user_data(username, st.session_state.streak, st.session_state.last_clear, st.session_state.learned_ids)
                st.session_state.review_idx += 1
                st.rerun()
        elif u_ans != "":
            st.error("残念！特訓です")
            st.session_state.wrong_word_id = word['id']
            st.session_state.review_queue.append(word)
            st.rerun()

elif st.session_state.phase == "goal":
    st.header("🎉 ミッション完了！")
    st.balloons()
    st.success(f"【{st.session_state.daily_neta['comedian']}】\n\n{st.session_state.daily_neta['fact']}")
    if st.button("トップに戻る"):
        del st.session_state.init_done
        st.rerun()
