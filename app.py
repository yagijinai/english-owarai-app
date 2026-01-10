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
        # 一意識別用のIDを作成
        words_df['id'] = words_df['word'] + "_" + words_df['meaning']
        return words_df, neta_df
    except Exception as e:
        st.error("データの読み込みに失敗しました。ファイルを確認してください。")
        st.stop()

WORDS_DF, NETA_DF = load_data()

# --- 学年判定 (2026年想定) ---
def get_current_grade():
    today = datetime.date.today()
    if today.year == 2026 and today.month <= 3: return 1
    elif (today.year == 2026 and today.month >= 4) or (today.year == 2027 and today.month <= 3): return 2
    else: return 3

# --- 学習データの初期化と取得 ---
def initialize_daily_data():
    today = datetime.date.today()
    today_str = str(today)
    
    # URLパラメータから保存データを取得
    learned_ids = st.query_params.get_all("learned_ids")
    streak_count = int(st.query_params.get("streak", 0))
    
    # 日付が変わった場合、またはデータが未設定の場合に初期化
    if "today_date" not in st.session_state or st.session_state.today_date != today_str:
        st.session_state.today_date = today_str
        random.seed(int(today_str.replace("-", "")))
        
        current_grade = get_current_grade()
        grade_pool = WORDS_DF[WORDS_DF['grade'] == current_grade]
        unlearned_pool = grade_pool[~grade_pool['id'].isin(learned_ids)]
        
        # もし全単語クリアしていたらリセット
        if len(unlearned_pool) < 3: unlearned_pool = grade_pool

        # 今日の練習単語(3個)
        st.session_state.daily_practice_words = unlearned_pool.sample(n=3).to_dict('records')
        # 復習単語(3個)
        review_pool = WORDS_DF[WORDS_DF['grade'] <= current_grade]
        st.session_state.review_queue = review_pool.sample(n=3).to_dict('records')
        # 今日の豆知識
