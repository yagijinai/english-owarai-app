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
        st.error("データの読み込みに失敗しました。")
        st.stop()

WORDS_DF, NETA_DF = load_data()

# --- 学年判定 ---
def get_current_grade():
    today = datetime.date.today()
    if today.year == 2026 and today.month <= 3: return 1
    elif (today.year == 2026 and today.month >= 4) or (today.year == 2027 and today.month <= 3): return 2
    else: return 3

# --- 連続日数と学習データの初期化 ---
def sync_data():
    today = datetime.date.today()
    today_str = str(today)
    yesterday_str = str(today - datetime.timedelta(days=1))
    
    # URLパラメータから情報を取得
    learned_ids = st.query_params.get_all("learned_ids")
    last_clear = st.query_params.get("last_clear", "")
    streak = int(st.query_params.get("streak", 0))
    
    # 連続日数の判定ロジック
    if last_clear == "":
        current_streak = 0
    elif last_clear == today_str:
        current_streak = streak
    elif last_clear == yesterday_str:
        current_streak = streak
    else:
        # 1日以上空いたらリセット
        current_streak = 0
    
    # セッションへの初期化（1日1回）
    if "today_date" not in st.session_state or st.session_state.today_date != today_str:
        st.session_state.today_date = today_str
        random.seed(int(today_str.replace("-", "")))
        
        current_grade = get_current_grade()
        grade_pool = WORDS_DF[WORDS_DF['grade'] == current_grade]
        unlearned_pool = grade_pool[~grade_pool['id'].isin(learned_ids)]
        
        if len(unlearned_pool) < 3: unlearned_pool = grade_pool

        st.session_state.daily_practice_words = unlearned_pool.sample(n=3).to_dict('records')
        review_pool = WORDS_DF[WORDS_DF['grade'] <= current_grade]
        st.session_state.review_queue = review_pool.sample(n=3).to_dict('records')
        st.session_state.daily_neta = NETA_DF.sample(n=1).iloc[0]
        st.session_state.show_hint = False

    return len(learned_ids), current_streak

# 状態の初期化
if "phase" not in st.session_state:
    st.session_state.phase = "new"
    st.session_state.current_word_idx = 0
    st.session_state.review_idx = 0
    st.session_state.wrong_word_id = None

total_cleared, streak_count = sync_data()

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
    st.markdown(f"「<span style='font-size: 26px; font-weight: bold; color: #FF4B4B;'>{word['meaning']}</span>」を 3回 入力しよう！", unsafe_allow_html=True)
    
    if not st.session_state.get("show_hint", False):
        if st.button("つづりを見る（ヒント）"):
            st.session_state.show_hint = True
            st.rerun()
    else:
        st.markdown(f"つづり： <span style='font-size: 22px; font-weight: bold; color: black;'>{word['word']}</span>", unsafe_allow_html=True)

    ans1 = st.text_input("1回目", key=f"ans1_{idx}").lower().strip()
    ans2 = st.text_input("2回目", key=f"ans2_{idx}").lower().strip()
    ans3 = st.text_input("3回目", key=f"ans3_{idx}").lower().strip()

    if ans1 == ans2 == ans3 == str(word['word']).lower() and ans1 != "":
        if st.button("次の単語へ"):
            current_learned = st.query_params.get_all("learned_ids")
            if word['id'] not in current_learned:
                current_learned.append(word['id'])
                st.query_params["learned_ids"] = current_learned
            st.session_state.current_word_idx += 1
            st.session_state.show_hint = False
            st.rerun()

# --- ステップ2: 復習テスト ---
elif st.session_state.phase == "review":
    r_idx = st.session_state.review_idx
    queue = st.session_state.review_queue
    
    if r_idx >= len(queue):
        st.session_state.phase = "goal"
        st.rerun()

    word = queue[r_idx]
    st.subheader(f"ステップ2: 復習テスト ({r_idx + 1}/{len(queue)})")
    st.markdown(f"「<span style='font-size: 26px; font-weight: bold; color: #FF4B4B;'>{word['meaning']}</span>」を英語で書こう！", unsafe_allow_html=True)
    
    if st.session_state.wrong_word_id == word['id']:
        st.warning("⚠️ 特訓中！正解は... " + word['word'])
        t_ans = [st.text_input(f"特訓 {i+1}/5", key=f"t{i}_{r_idx}").lower().strip() for i in range(5)]
        if all(a == str(word['word']).lower() and a != "" for a in t_ans):
            if st.button("特訓完了！"):
                st.session_state.wrong_word_id = None
                st.session_state.review_idx += 1
                st.rerun()
    else:
        user_ans = st.text_input("答えを入力", key=f"rev_{r_idx}").lower().strip()
        if user_ans != "":
            if user_ans == str(word['word']).lower():
                st.success("正解！")
                if st.button("次へ進む"):
                    # 正解した瞬間に連続日数を更新して保存する
                    today_str = str(datetime.date.today())
                    yesterday_str = str(datetime.date.today() - datetime.timedelta(days=1))
                    
                    last_clear = st.query_params.get("last_clear", "")
                    current_streak = int(st.query_params.get("streak", 0))
                    
                    if last_clear != today_str:
                        if last_clear == yesterday_str:
                            new_streak = current_streak + 1
                        else:
                            new_streak = 1
                        st.query_params["streak"] = new_streak
                        st.query_params["last_clear"] = today_str
                    
                    st.session_state.review_idx += 1
                    st.rerun()
            else:
                st.markdown("<style>.stApp { background-color: #ffe6e6; }</style>", unsafe_allow_html=True)
                st.error("つづりが違います！")
                st.session_state.wrong_word_id = word['id']
                st.session_state.review_queue.append(word)
                if st.button("特訓を始める"):
                    st.rerun()

# --- ゴール ---
elif st.session_state.phase == "goal":
    target_neta = st.session_state.daily_neta
    st.header("🎉 全ミッション完了！")
    st.balloons()
    final_streak = st.query_params.get("streak", 1)
    st.info(f"🔥 現在 {final_streak} 日連続です！明日も頑張ろう！")
    st.subheader("今日の芸人豆知識")
    st.success(f"【{target_neta['comedian']}】\n\n{target_neta['fact']}")
    
    if st.button("終了してトップへ"):
        st.session_state.phase = "new"
        st.session_state.current_word_idx = 0
        st.session_state.review_idx = 0
        st.rerun()
