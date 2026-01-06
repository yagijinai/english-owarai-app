import streamlit as st
import pandas as pd
import datetime
import random

# --- データの読み込み ---
@st.cache_data
def load_data():
    # GitHub上に作ったcsvファイルを読み込む
    words_df = pd.read_csv('words.csv')
    neta_df = pd.read_csv('neta.csv')
    return words_df, neta_df

try:
    WORDS_DF, NETA_DF = load_data()
except:
    st.error("csvファイルが見つかりません。words.csv と neta.csv を作成してください。")
    st.stop()

# 学年判定（2026年現在、2024年入学なら新中2〜中3）
def get_current_grade(start_year=2024):
    today = datetime.date.today()
    month = today.month
    year = today.year
    grade = year - start_year + (1 if month >= 4 else 0)
    return max(1, min(grade, 3))

# --- アプリの基本設定 ---
st.set_page_config(page_title="毎日英語とお笑い", page_icon="📝")
st.title("🔤 1日5分！英語マスターへの道")

if "count" not in st.session_state:
    st.session_state.count = 0
    st.session_state.phase = "new"
    st.session_state.current_word_idx = 0
    st.session_state.typing_count = 0

grade = get_current_grade()
# 今の学年に合った単語を抽出
target_words = WORDS_DF[WORDS_DF['grade'] == grade].to_dict('records')
if not target_words:
    target_words = WORDS_DF[WORDS_DF['grade'] == 1].to_dict('records')
target_words = target_words[:3] # 最大3問

# --- 画面表示 ---
if st.session_state.phase == "new":
    word = target_words[st.session_state.current_word_idx]
    st.header(f"ステップ1: 新しい単語 ({st.session_state.current_word_idx + 1}/3)")
    st.subheader(f"「{word['meaning']}」を英語で？ → **{word['word']}**")
    st.write(f"あと **{3 - st.session_state.typing_count}回** 入力！")
    
    user_input = st.text_input("英字で入力", key=f"in_{st.session_state.current_word_idx}_{st.session_state.typing_count}")
    
    if user_input.lower().strip() == str(word['word']).lower():
        st.success("正解！")
        st.session_state.typing_count += 1
        if st.session_state.typing_count >= 3:
            st.session_state.typing_count = 0
            st.session_state.current_word_idx += 1
        if st.session_state.current_word_idx >= len(target_words):
            st.session_state.phase = "review"
        st.rerun()

elif st.session_state.phase == "review":
    st.header("ステップ2: 復習テスト")
    if "review_target" not in st.session_state:
        st.session_state.review_target = random.choice(target_words)
    
    word = st.session_state.review_target
    st.subheader(f"「{word['meaning']}」を英語で？")
    user_input = st.text_input("答えを入力", key="rev")
    
    if user_input.lower().strip() == str(word['word']).lower():
        st.balloons()
        st.session_state.phase = "goal"
        st.session_state.count += 1
        st.rerun()

elif st.session_state.phase == "goal":
    st.header("🎉 ミッション完了！")
    st.info(f"🔥 連続継続日数: {st.session_state.count}日")
    st.subheader("今日の芸人豆知識")
    
    # 豆知識リストからランダムに表示
    neta = NETA_DF.sample(n=1).iloc[0]
    st.success(f"【{neta['comedian']}】\n\n{neta['fact']}")
    
    if st.button("明日も頑張る"):
        del st.session_state.review_target
        st.session_state.phase = "new"
        st.session_state.current_word_idx = 0
        st.rerun()
