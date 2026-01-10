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
    if today.year == 2026 and today.month <= 3: return 1
    elif (today.year == 2026 and today.month >= 4) or (today.year == 2027 and today.month <= 3): return 2
    else: return 3

# --- 問題選定（重複排除と復習3問） ---
def initialize_daily_data():
    today = str(datetime.date.today())
    learned_ids = st.query_params.get_all("learned_ids")
    
    if "today_date" not in st.session_state or st.session_state.today_date != today:
        st.session_state.today_date = today
        random.seed(int(today.replace("-", "")))
        
        current_grade = get_current_grade()
        grade_pool = WORDS_DF[WORDS_DF['grade'] == current_grade]
        unlearned_pool = grade_pool[~grade_pool['id'].isin(learned_ids)]
        
        if len(unlearned_pool) < 3: unlearned_pool = grade_pool

        # 練習用3語
        st.session_state.daily_practice_words = unlearned_pool.sample(n=3).to_dict('records')
        
        # 復習用3語 (練習した語や過去語から)
        review_pool = WORDS_DF[WORDS_DF['grade'] <= current_grade]
        st.session_state.review_queue = review_pool.sample(n=3).to_dict('records')
        
        # 豆知識
        st.session_state.daily_neta = NETA_DF.sample(n=1).iloc[0]
    
    return len(learned_ids)

total_cleared = initialize_daily_data()

st.set_page_config(page_title="毎日英語とお笑い", page_icon="📝")
st.markdown("<h4 style='text-align: left;'>🔤 徹底復習モード！英語マスター</h4>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: right; color: gray; font-size: 12px;'>これまでクリアした単語数： {total_cleared} 個</p>", unsafe_allow_html=True)

if "phase" not in st.session_state:
    st.session_state.phase = "new"
    st.session_state.current_word_idx = 0
    st.session_state.review_idx = 0
    st.session_state.wrong_word_id = None

# --- ステップ1: 単語練習 (3回) ---
if st.session_state.phase == "new":
    idx = st.session_state.current_word_idx
    practice_words = st.session_state.daily_practice_words
    
    if idx >= len(practice_words):
        st.session_state.phase = "review"
        st.rerun()

    word = practice_words[idx]
    st.subheader(f"ステップ1: 新しい単語 ({idx + 1}/3)")
    st.write(f"「**{word['meaning']}**」を 3回 入力しよう！")
    st.markdown(f"つづり： <span style='font-size: 24px; font-weight: bold; color: #FF4B4B;'>{word['word']}</span>", unsafe_allow_html=True)

    ans = [st.text_input(f"{i+1}回目", key=f"ans{i}_{idx}").lower().strip() for i in range(3)]

    if all(a == str(word['word']).lower() and a != "" for a in ans):
        if st.button("次の単語へ"):
            current_learned = st.query_params.get_all("learned_ids")
            if word['id'] not in current_learned:
                current_learned.append(word['id'])
                st.query_params["learned_ids"] = current_learned
            st.session_state.current_word_idx += 1
            st.rerun()

# --- ステップ2: 徹底復習テスト ---
elif st.session_state.phase == "review":
    r_idx = st.session_state.review_idx
    queue = st.session_state.review_queue
    
    if r_idx >= len(queue):
        st.session_state.phase = "goal"
        st.rerun()

    word = queue[r_idx]
    st.subheader(f"ステップ2: 復習テスト ({r_idx + 1}/{len(queue)})")
    st.write(f"「**{word['meaning']}**」を英語で書こう！")
    
    # 以前に間違えた履歴があるかチェック（特訓モード）
    if st.session_state.wrong_word_id == word['id']:
        st.warning("⚠️ つづりを間違えました！5回入力して特訓しよう。")
        st.write(f"正解は... **{word['word']}**")
        t_ans = [st.text_input(f"特訓 {i+1}/5", key=f"t{i}_{r_idx}").lower().strip() for i in range(5)]
        
        if all(a == str(word['word']).lower() and a != "" for a in t_ans):
            if st.button("特訓完了！次へ"):
                st.session_state.wrong_word_id = None
                st.session_state.review_idx += 1
                st.rerun()
    else:
        # 通常のテスト入力
        user_ans = st.text_input("答えを入力", key=f"rev_{r_idx}").lower().strip()
        if user_ans != "":
            if user_ans == str(word['word']).lower():
                st.success("正解！")
                if st.button("次へ進む"):
                    st.session_state.review_idx += 1
                    st.rerun()
            else:
                st.error("つづりが違います！特訓を開始します。")
                # 間違えたらIDを記録し、さらに本日の最後にもう一度追加
                st.session_state.wrong_word_id = word['id']
                st.session_state.review_queue.append(word)
                if st.button("特訓を始める"):
                    st.rerun()

# --- ゴール ---
elif st.session_state.phase == "goal":
    target_neta = st.session_state.daily_neta
    st.header("🎉 全ミッション完了！")
    st.info("今日はよく頑張りましたね。復習もバッチリです！")
    st.subheader("今日の芸人豆知識")
    st.success(f"【{target_neta['comedian']}】\n\n{target_neta['fact']}")
    
    if st.button("明日も頑張る"):
        st.session_state.phase = "new"
        st.session_state.current_word_idx = 0
        st.session_state.review_idx = 0
        st.rerun()
