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

# --- 日替わり問題の選定 ---
def get_daily_items(current_grade):
    today = datetime.date.today()
    seed_value = today.year * 10000 + today.month * 100 + today.day
    random.seed(seed_value)
    
    practice_pool = WORDS_DF[WORDS_DF['grade'] == current_grade]
    if len(practice_pool) < 3:
        practice_pool = WORDS_DF
    daily_practice_words = practice_pool.sample(n=3).to_dict('records')
    
    review_pool = WORDS_DF[WORDS_DF['grade'] <= current_grade]
    daily_review_word = review_pool.sample(n=1).iloc[0].to_dict()
    daily_neta = NETA_DF.sample(n=1).iloc[0]
    
    return daily_practice_words, daily_review_word, daily_neta

# アプリ設定
st.set_page_config(page_title="毎日英語とお笑い", page_icon="📝")
st.markdown("<h4 style='text-align: left;'>🔤 1日5分！英語マスターへの道</h4>", unsafe_allow_html=True)

# --- セッション状態の管理 ---
if "phase" not in st.session_state:
    st.session_state.phase = "new"
    st.session_state.current_word_idx = 0
    st.session_state.typing_count = 0

current_grade = get_current_grade()
practice_words, review_word, target_neta = get_daily_items(current_grade)

# --- ステップ1: 単語練習 (3回入力) ---
if st.session_state.phase == "new":
    # インデックスが範囲を超えないようガード
    idx = st.session_state.current_word_idx
    if idx >= len(practice_words):
        st.session_state.phase = "review"
        st.rerun()

    word = practice_words[idx]
    st.subheader(f"ステップ1: 中{current_grade}の練習 ({idx + 1}/3)")
    st.write(f"「{word['meaning']}」は英語で？ → **{word['word']}**")
    
    # 進行状況を視覚的に表示
    count = st.session_state.typing_count
    st.info(f"進捗: {'★' * count}{'☆' * (3-count)} （{count}/3回成功）")
    
    # 入力欄のキーを完全にユニークにする
    input_key = f"input_{idx}_{count}_{datetime.datetime.now().microsecond}"
    user_input = st.text_input("英字で入力してください", key=input_key, autocomplete="off")
    
    if user_input:
        if user_input.lower().strip() == str(word['word']).lower():
            st.session_state.typing_count += 1
            if st.session_state.typing_count >= 3:
                st.session_state.typing_count = 0
                st.session_state.current_word_idx += 1
                st.success("完璧です！次の単語へ進みます。")
            else:
                st.success(f"正解！あと {3 - st.session_state.typing_count} 回入力しましょう。")
            
            # 画面を強制更新して次の回数へ
            st.rerun()
        else:
            # 間違えた場合はメッセージを出すが、カウントは増やさない
            if user_input.strip() != "":
                st.error("つづりが違います。もう一度確認して入力してね！")

# --- ステップ2: 復習テスト ---
elif st.session_state.phase == "review":
    st.subheader(f"ステップ2: 総復習テスト (中1〜中{current_grade}から)")
    st.write(f"「{review_word['meaning']}」を英語で書けますか？")
    
    user_input = st.text_input("答えを入力", key="final_test_input", autocomplete="off")
    
    if user_input:
        if user_input.lower().strip() == str(review_word['word']).lower():
            st.balloons()
            st.session_state.phase = "goal"
            st.rerun()
        elif user_input.strip() != "":
            st.error("おっと、つづりが違うみたい。ヒント：ステップ1でやった単語かも？")

# --- ゴール ---
elif st.session_state.phase == "goal":
    st.header("🎉 ミッション完了！")
    st.subheader("今日の芸人豆知識")
    st.success(f"【{target_neta['comedian']}】\n\n{target_neta['fact']}")
    
    if st.button("明日も頑張る"):
        st.session_state.phase = "new"
        st.session_state.current_word_idx = 0
        st.session_state.typing_count = 0
        st.rerun()
