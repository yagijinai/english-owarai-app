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
        return words_df, neta_df
    except Exception as e:
        st.error(f"データの読み込みに失敗しました")
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

# --- 今日の問題を「金庫」に保存する仕組み ---
def initialize_daily_data():
    today = str(datetime.date.today())
    
    # まだ「今日のデータ」が金庫にないか、日付が変わっていたら新しく選ぶ
    if "today_date" not in st.session_state or st.session_state.today_date != today:
        st.session_state.today_date = today
        
        # 日付を種にしてランダムに選ぶ（この瞬間だけ実行されるようにする）
        random.seed(int(today.replace("-", "")))
        current_grade = get_current_grade()
        
        # 練習用（その学年）
        practice_pool = WORDS_DF[WORDS_DF['grade'] == current_grade]
        if len(practice_pool) < 3:
            practice_pool = WORDS_DF
        st.session_state.daily_practice_words = practice_pool.sample(n=3).to_dict('records')
        
        # 復習用（その学年以下）
        review_pool = WORDS_DF[WORDS_DF['grade'] <= current_grade]
        st.session_state.daily_review_word = review_pool.sample(n=1).iloc[0].to_dict()
        
        # 豆知識
        st.session_state.daily_neta = NETA_DF.sample(n=1).iloc[0]

# データを準備
initialize_daily_data()

# アプリ設定
st.set_page_config(page_title="毎日英語とお笑い", page_icon="📝")
st.markdown("<h4 style='text-align: left;'>🔤 1日5分！英語マスターへの道</h4>", unsafe_allow_html=True)

# --- セッション状態（進行状況）の管理 ---
if "phase" not in st.session_state:
    st.session_state.phase = "new"
    st.session_state.current_word_idx = 0

# --- ステップ1: 単語練習 (3つの入力欄) ---
if st.session_state.phase == "new":
    idx = st.session_state.current_word_idx
    practice_words = st.session_state.daily_practice_words
    
    if idx >= len(practice_words):
        st.session_state.phase = "review"
        st.rerun()

    word = practice_words[idx]
    current_grade = get_current_grade()
    
    st.subheader(f"ステップ1: 中{current_grade}の練習 ({idx + 1}/3)")
    st.write(f"「**{word['meaning']}**」を 3回 入力して覚えよう！")
    st.markdown(f"つづり： <span style='font-size: 24px; font-weight: bold; color: #FF4B4B;'>{word['word']}</span>", unsafe_allow_html=True)

    # 入力欄
    ans1 = st.text_input("1回目", key=f"ans1_{idx}", autocomplete="off").lower().strip()
    ans2 = st.text_input("2回目", key=f"ans2_{idx}", autocomplete="off").lower().strip()
    ans3 = st.text_input("3回目", key=f"ans3_{idx}", autocomplete="off").lower().strip()

    correct_answer = str(word['word']).lower()

    if ans1 == correct_answer and ans2 == correct_answer and ans3 == correct_answer:
        st.success("完璧です！3回書けましたね。")
        if st.button("次の単語へ進む"):
            st.session_state.current_word_idx += 1
            st.rerun()
    elif ans1 or ans2 or ans3:
        if (ans1 and ans1 != correct_answer) or (ans2 and ans2 != correct_answer) or (ans3 and ans3 != correct_answer):
            st.error("つづりが違うところがあるよ。よく見て直してね。")

# --- ステップ2: 復習テスト ---
elif st.session_state.phase == "review":
    review_word = st.session_state.daily_review_word
    current_grade = get_current_grade()
    
    st.subheader(f"ステップ2: 総復習テスト (中1〜中{current_grade}から)")
    st.write(f"「**{review_word['meaning']}**」を英語で書けますか？")
    
    final_ans = st.text_input("答えを入力", key="final_test", autocomplete="off").lower().strip()
    
    if final_ans == str(review_word['word']).lower():
        st.balloons()
        st.success("正解！すごい！")
        if st.button("結果を見る"):
            st.session_state.phase = "goal"
            st.rerun()

# --- ゴール ---
elif st.session_state.phase == "goal":
    target_neta = st.session_state.daily_neta
    st.header("🎉 ミッション完了！")
    st.subheader("今日の芸人豆知識")
    st.success(f"【{target_neta['comedian']}】\n\n{target_neta['fact']}")
    
    if st.button("明日も頑張る"):
        st.session_state.phase = "new"
        st.session_state.current_word_idx = 0
        # 明日になったら日付が変わるので、initialize_daily_dataで新しい単語が選ばれます
        st.rerun()
