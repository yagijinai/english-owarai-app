import streamlit as st
import random
import streamlit.components.v1 as components
from datetime import datetime

# --- 1. ページ設定 ---
st.set_page_config(layout="centered", page_title="英単語練習アプリ")

# --- 2. セッション状態の初期化 ---
def init_session_state():
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'page' not in st.session_state: st.session_state.page = "login"
    
    # テスト用：最大1000人を想定した簡易ユーザーDB（名前をキー、パスワードを値に保存）
    if 'user_db' not in st.session_state:
        st.session_state.user_db = {"お父様": "1234", "娘さん": "1234"}
    
    # 現在のログインユーザー情報
    if 'current_user' not in st.session_state: st.session_state.current_user = ""
    if 'streak' not in st.session_state: st.session_state.streak = 0

    # 単語マスターDB（学年別）
    if 'word_db' not in st.session_state:
        st.session_state.word_db = {
            "中学1年生": [{"q": "りんご", "a": "apple"}, {"q": "本", "a": "book"}, {"q": "猫", "a": "cat"}],
            "中学2年生": [{"q": "経験", "a": "experience"}, {"q": "快適な", "a": "comfortable"}],
            "中学3年生": [{"q": "環境", "a": "environment"}, {"q": "影響", "a": "influence"}],
            "高校1年生": [{"q": "分析する", "a": "analyze"}, {"q": "重要な", "a": "significant"}],
            "高校2年生": [{"q": "経済", "a": "economy"}, {"q": "維持する", "a": "maintain"}],
            "高校3年生": [{"q": "哲学", "a": "philosophy"}, {"q": "複雑な", "a": "complicated"}]
        }

    # 練習用変数
    if 'session_words' not in st.session_state: st.session_state.session_words = []
    if 'test_words' not in st.session_state: st.session_state.test_words = []
    if 'word_index' not in st.session_state: st.session_state.word_index = 0
    if 'repeat_count' not in st.session_state: st.session_state.repeat_count = 1
    if 'penalty_word' not in st.session_state: st.session_state.penalty_word = None
    if 'penalty_count' not in st.session_state: st.session_state.penalty_count = 0
    if 'show_hint' not in st.session_state: st.session_state.show_hint = False
    if 'input_key' not in st.session_state: st.session_state.input_key = 0

def get_current_grade():
    today = datetime.now()
    # 2025年度(2026年3月まで)が中1の想定
    base_year = 2025
    school_year = today.year if today.month >= 4 else today.year - 1
    grade_diff = school_year - base_year
    grades = ["中学1年生", "中学2年生", "中学3年生", "高校1年生", "高校2年生", "高校3年生"]
    if 0 <= grade_diff < len(grades):
        return grades[grade_diff]
    return "中学1年生"

init_session_state()

def speak_word(word):
    js = f"<script>var m=new SpeechSynthesisUtterance('{word}');m.lang='en-US';window.speechSynthesis.speak(m);</script>"
    components.html(js, height=0)

# --- 3. ログイン画面（緩め設定） ---
if not st.session_state.logged_in:
    st.title("📖 英単語学習アプリ")
    st.write("名前とパスワードを入力してください。初めての方はその場で登録されます。")
    
    user_in = st.text_input("名前（ID）:").strip()
    pwd_in = st.text_input("パスワード:", type="password").strip()
    
    if st.button("ログイン / 新規登録", use_container_width=True):
        if user_in and pwd_in:
            # すでに名前がある場合
            if user_in in st.session_state.user_db:
                if st.session_state.user_db[user_in] == pwd_in:
                    st.session_state.current_user = user_in
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("パスワードが違います。")
            # 名前がない場合は、その場で自動登録
            else:
                st.session_state.user_db[user_in] = pwd_in
                st.session_state.current_user = user_in
                st.session_state.logged_in = True
                st.success(f"新しく「{user_in}」として登録しました！")
                st.rerun()
        else:
            st.warning("名前とパスワードを入力してください。")
    st.stop()

# --- 4. サイドバー ＆ 単語追加 ---
st.sidebar.title(f"👤 {st.session_state.current_user}")
grade = get_current_grade()
st.sidebar.info(f"現在の学年: {grade}")

if st.sidebar.checkbox("単語を追加する"):
    st.sidebar.write("---")
    target_grade = st.sidebar.selectbox("対象学年", list(st.session_state.word_db.keys()))
    new_q = st.sidebar.text_input("日本語")
    new_a = st.sidebar.text_input("英語")
    if st.sidebar.button("追加実行"):
        if new_q and new_a:
            st.session_state.word_db[target_grade].append({"q": new_q, "a": new_a})
            st.sidebar.success("追加しました！")

# --- 5. メインメニュー ＆ 練習 ---
if st.session_state.page == "main_menu":
    st.header(f"ようこそ、{st.session_state.current_user}さん")
    if st.button("🚀 学習スタート", use_container_width=True):
        grade = get_current_grade()
        words = st.session_state.word_db[grade]
        count = min(len(words), 3)
        st.session_state.session_words = random.sample(words, count)
        st.session_state.word_index = 0
        st.session_state.repeat_count = 1
        st.session_state.page = "training"
        st.rerun()

elif st.session_state.page == "training":
    word = st.session_state.session_words[st.session_state.word_index]
    st.header(f"練習 ({st.session_state.repeat_count}/3回目)")
    st.subheader(f"「{word['q']}」")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("📢 音声"): speak_word(word['a'])
    with c2:
        if st.button("💡 答え"): st.session_state.show_hint = True
    
    if st.session_state.show_hint: st.info(f"正解： {word['a']}")

    u_in = st.text_input("入力:", key=f"t_{st.session_state.input_key}").strip().lower()
    if st.button("判定", use_container_width=True):
        if u_in == word['a']:
            st.session_state.show_hint = False
            st.session_state.input_key += 1
            if st.session_state.repeat_count < 3:
                st.session_state.repeat_count += 1
            else:
                st.session_state.repeat_count = 1
                st.session_state.word_index += 1
            
            if st.session_state.word_index >= len(st.session_state.session_words):
                # テスト作成（今日の3語 ＋ 過去1語）
                st.session_state.test_words = list(st.session_state.session_words)
                grade = get_current_grade()
                past = [w for w in st.session_state.word_db[grade] if w not in st.session_state.test_words]
                if past: st.session_state.test_words.append(random.choice(past))
                random.shuffle(st.session_state.test_words)
                st.session_state.page = "test"
            st.rerun()

# --- 6. 復習テスト ＆ 特訓 ＆ 結果 ---
elif st.session_state.page == "test":
    if not st.session_state.test_words:
        st.session_state.page = "result"
        st.rerun()

    word = st.session_state.test_words[0]
    st.header(f"🔥 復習テスト (残り {len(st.session_state.test_words)}問)")
    st.subheader(f"「{word['q']}」を英語で！")
    if st.button("📢 音声"): speak_word(word['a'])

    t_in = st.text_input("回答:", key=f"v_{st.session_state.input_key}").strip().lower()
    if st.button("判定", use_container_width=True):
        if t_in == word['a']:
            st.session_state.test_words.pop(0)
            st.session_state.input_key += 1
            st.rerun()
        else:
            st.session_state.penalty_word = word
            st.session_state.penalty_count = 1
            st.session_state.page = "penalty"
            st.rerun()

elif st.session_state.page == "penalty":
    word = st.session_state.penalty_word
    st.error(f"【特訓】あと {6-st.session_state.penalty_count} 回！(正解:{word['a']})")
    p_in = st.text_input(f"{st.session_state.penalty_count}回目:", key=f"p_{st.session_state.input_key}").strip().lower()
    if st.button("送信", use_container_width=True):
        if p_in == word['a']:
            st.session_state.input_key += 1
            if st.session_state.penalty_count < 5:
                st.session_state.penalty_count += 1
            else:
                failed = st.session_state.test_words.pop(0)
                st.session_state.test_words.append(failed)
                st.session_state.page = "test"
            st.rerun()

elif st.session_state.page == "result":
    st.header("全問正解！お疲れ様 🎉")
    st.balloons()
    if st.button("メインメニューへ", use_container_width=True):
        st.session_state.page = "main_menu"
        st.rerun()
    if st.button("ログアウト", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
