import streamlit as st
import datetime
import random

# --- 設定・データ準備 ---
# 本来は外部ファイルにしますが、まずは1ファイルで動くようにここに書きます
WORDS = [
    {"word": "apple", "meaning": "りんご", "grade": 1},
    {"word": "school", "meaning": "学校", "grade": 1},
    {"word": "friend", "meaning": "友達", "grade": 1},
    {"word": "happy", "meaning": "幸せな", "grade": 1},
    {"word": "pencil", "meaning": "鉛筆", "grade": 1},
    # 中2、中3の単語もここに追加していけます
]

NETA_LIST = [
    "【ガクテンソク】奥田さんは漫才の台本をきっちり書くタイプだが、よじょうさんはアドリブに強いらしいですよ！",
    "【令和ロマン】くるまさんはM-1優勝のために、過去の全大会を分析したという驚きのエピソードがあります。",
    "【ガクテンソク】ツッコミの奥田さんは、実はとても多趣味で知識が豊富。それがネタの厚みを作っています。",
    "【濱田祐太郎】R-1優勝時、舞台袖に戻った第一声は「あー緊張した！」ではなく「お腹すいたー！」だったとか。"
]

# 学年判定（4月基準）
def get_current_grade(start_year=2024):
    today = datetime.date.today()
    month = today.month
    year = today.year
    grade = year - start_year + (1 if month >= 4 else 0)
    return max(1, min(grade, 3))

# --- アプリのロジック ---
st.set_page_config(page_title="毎日英語とお笑い", page_icon="📝")
st.title("🔤 1日5分！英語マスターへの道")

# 継続日数の管理（仮：ブラウザを閉じるとリセットされます。後日保存機能を付けましょう）
if "count" not in st.session_state:
    st.session_state.count = 0
    st.session_state.phase = "new"  # new: 新規, review: 復習, goal: 終了
    st.session_state.current_word_idx = 0
    st.session_state.typing_count = 0

grade = get_current_grade()
target_words = [w for w in WORDS if w['grade'] == grade][:3]

# --- メイン画面 ---
if st.session_state.phase == "new":
    word = target_words[st.session_state.current_word_idx]
    st.header(f"ステップ1: 新しい単語 ({st.session_state.current_word_idx + 1}/3)")
    st.subheader(f"「{word['meaning']}」は英語で？ → **{word['word']}**")
    st.write(f"あと **{3 - st.session_state.typing_count}回** 正解してください")
    
    user_input = st.text_input("英字で入力してEnter!", key=f"input_{st.session_state.current_word_idx}_{st.session_state.typing_count}")
    
    if user_input.lower() == word['word'].lower():
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
    st.write("意味を見て英語を1回ずつ入力しよう！")
    # 復習用ロジック（簡易版）
    word = target_words[st.session_state.current_word_idx - 3] # 今回は今日の単語をテスト
    st.subheader(f"「{word['meaning']}」")
    
    user_input = st.text_input("英語で？", key="review_input")
    if user_input.lower() == word['word'].lower():
        st.balloons()
        st.session_state.phase = "goal"
        st.session_state.count += 1
        st.rerun()

elif st.session_state.phase == "goal":
    st.header("🎉 本日のミッション完了！")
    st.info(f"🔥 連続継続日数: {st.session_state.count}日")
    st.subheader("今日の芸人豆知識")
    st.success(random.choice(NETA_LIST))
    if st.button("もう一度（練習）"):
        st.session_state.phase = "new"
        st.session_state.current_word_idx = 0
        st.rerun()
