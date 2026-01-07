import streamlit as st
import pandas as pd
import datetime
import random

# --- データの読み込み ---
@st.cache_data
def load_data():
    try:
        words_df = pd.read_csv('words.csv')
        neta_df = pd.read_csv('neta.csv')
        words_df['id'] = words_df['word'] + "_" + words_df['meaning']
        return words_df, neta_df
    except Exception as e:
        st.error("データの読み込みに失敗しました")
        st.stop()

WORDS_DF, NETA_DF = load_data()

# --- 学年判定 ---
def get_current_grade():
    today = datetime.date.today()
    if today.year == 2026 and today.month <= 3:
        return 1
    elif (today.year == 2026 and today.month >= 4) or (today.year == 2027 and today.month <= 3):
        return 2
    else:
        return 3

# --- 問題選定と学習状況の取得 ---
def initialize_daily_data():
    today = str(datetime.date.today())
    # ブラウザから学習済みリストを取得
    learned_ids = st.query_params.get_all("learned_ids")
    
    if "today_date" not in st.session_state or st.session_state.today_date != today:
        st.session_state.today_date = today
        random.seed(int(today.replace("-", "")))
        
        current_grade = get_current_grade()
        grade_pool = WORDS_DF[WORDS_DF['grade'] == current_grade]
        unlearned_pool = grade_pool[~grade_pool['id'].isin(learned_ids)]
        
        if len(unlearned_pool) < 3:
            unlearned_pool = grade_pool
            st.toast("全単語クリア！二周目に入ります。")

        st.session_state.daily_practice_words = unlearned_pool.sample(n=3).to_dict('records')
        review_pool = WORDS_DF[WORDS_DF['grade'] <= current_grade]
        st.session_state.daily_review_word = review_pool.sample(n=1).iloc[0].to_dict()
        st.session_state.daily_neta = NETA_DF.sample(n=1).iloc[0]
    
    return len(learned_ids)

# データを準備し、クリア数を取得
total_cleared = initialize_daily_data()

# アプリ設定
st.set_page_config(page_title="毎日英語とお笑い", page_icon="📝")
st.markdown("<h4 style='text-align: left;'>🔤 1日5分！英語マスターへの道</h4>", unsafe_allow_html=True)

# クリアした単語数を小さく表示
st.markdown(f"<p style='text-align: right; color: gray; font-size: 12px;'>これまでクリアした単語数： {total_cleared} 個</p>", unsafe_allow_html=True)

if "phase" not in st.session_state:
    st.session_state.phase = "new"
    st.session_state.current_word_idx = 0

# --- ステップ1: 単語練習 ---
if st.session_state.phase == "new":
    idx = st.session_state.current_word_idx
    practice_words = st.session_state.daily_practice_words
    
    if idx >= len(practice_words):
        st.session_state.phase = "review"
        st.rerun()

    word = practice_words[idx]
    st.subheader(f"ステップ1: 中{get_current_grade()}の練習 ({idx + 1}/3)")
    st.write(f"「**{word['meaning']}**」を 3回 入力しよう！")
    st.markdown(f"つづり： <span style='font-size: 24px; font-weight: bold; color: #FF4B4B;'>{word['word']}</span>", unsafe_allow_html=True)

    ans1 = st.text_input("1回目", key=f"ans1_{idx}").lower().strip()
    ans2 = st.text_input("2回目", key=f"ans2_{idx}").lower().strip()
    ans3 = st.text_input("3回目", key=f"ans3_{idx}").lower().strip()

    if ans1 == ans2 == ans3 == str(word['word']).lower():
        if st.button("次の単語へ進む"):
            # 学習済みに追加
            current_learned = st.query_params.get_all("learned_ids")
            if word['id'] not in current_learned:
                current_learned.append(word['id'])
                st.query_params["learned_ids"] = current_learned
            st.
