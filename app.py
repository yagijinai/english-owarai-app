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
        st.session_state.daily_neta = NETA_DF.sample(n=1).iloc[0]
    
    return len(learned_ids), streak_count

# 状態の初期化
if "phase" not in st.session_state:
    st.session_state.phase = "new"
    st.session_state.current_word_idx = 0
    st.session_state.review_idx = 0
    st.session_state.wrong_word_id = None
if "show_hint" not in st.session_state:
    st.session_state.show_hint = False

total_cleared, streak_count = initialize_daily_data()

# アプリ設定
st.set_page_config(page_title="毎日英語とお笑い", page_icon="📝")
st.markdown("<h4 style='text-align: left;'>🔤 徹底復習モード！英語マスター</h4>", unsafe_allow_html=True)

# 記録を右上に表示
st.markdown(f"<p style='text-align: right; color: gray; font-size: 12px; margin-bottom: 0;'>これまでクリア： {total_cleared} 個 | 🔥 連続 {streak_count} 日</p>", unsafe_allow_html=True)

# --- ステップ1: 単語練習 ---
if st.session_state.phase == "new":
    idx = st.session_state.current_word_idx
    practice_words = st.session_state.daily_practice_words
    
    if idx >= len(practice_words):
        st.session_state.phase = "review"
        st.rerun()

    word = practice_words[idx]
    st.subheader(f"ステップ1: 新しい単語 ({idx + 1}/3)")
    
    # 日本語を大きく赤文字で表示
    st.markdown(f"「<span style='font-size: 26px; font-weight: bold; color: #FF4B4B;'>{word['meaning']}</span>」を 3回 入力しよう！", unsafe_allow_html=True)
    
    # ヒント機能
    if not st.session_state.show_hint:
        if st.button("つづりを見る（ヒント）"):
            st.session_state.show_hint = True
            st.rerun()
    else:
        st.markdown(f"つづり： <span style='font-size: 22px; font-weight: bold; color: black;'>{word['word']}</span>", unsafe_allow_html=
