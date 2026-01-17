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
    if 'user_db' not in st.session_state: st.session_state.user_db = {"お父様": "1234", "娘さん": "1234"}
    if 'current_user' not in st.session_state: st.session_state.current_user = ""
    
    # 学年別単語DB
    if 'word_db' not in st.session_state:
        st.session_state.word_db = {
            "中学1年生": [{"q": "りんご", "a": "apple"}, {"q": "本", "a": "book"}, {"q": "猫", "a": "cat"}],
            "中学2年生": [{"q": "経験", "a": "experience"}, {"q": "快適な", "a": "comfortable"}],
            "中学3年生": [{"q": "環境", "a": "environment"}, {"q": "影響", "a": "influence"}],
            "高校1年生": [{"q": "分析する", "a": "analyze"}, {"q": "重要な", "a": "significant"}],
            "高校2年生": [{"q": "経済", "a": "economy"}, {"q": "維持する", "a": "maintain"}],
            "高校3年生": [{"q": "哲学", "a": "philosophy"}, {"q": "複雑な", "a": "complicated"}]
        }

    # 進捗管理変数
    if 'session_words' not in st.session_state: st.session_state.session_words = []
    if 'test_words' not in st.session_state: st.session_state.test_words = []
    if 'word_index' not in st.session_state: st.session_state.word_index = 0
    if 'repeat_count' not in st.session_state: st.session_state.repeat_count = 1
    if 'penalty_word' not in st.session_state: st.session_state.penalty_word = None
    if 'penalty_count' not in st.session_state: st.session_state.penalty_count = 0
    if 'show_hint' not in st.session_state: st.session_state.show_hint = False
    if 'input_key' not in st.session_state: st.session_state.input_key = 0
    
    # 【対策】ご褒美エピソードを保持する変数
    if 'current_neta' not in st.session_state: st.session_state.current_neta = ""

def get_current_grade():
    today = datetime.now()
    school_year = today.year if today.month >= 4 else today.year - 1
    grade_diff = school_year - 2025
    grades = ["中学1年生", "中学2年生", "中学3年生", "高校1年生", "高校2年生", "高校3年生"]
    if 0 <= grade_diff < len(grades): return grades[grade_diff]
    return "中学1年生"

init_session_state()

def speak_word(word):
    js = f"<script>var m=new SpeechSynthesisUtterance('{word}');m.lang='en-US';window.speechSynthesis.speak(m);</script>"
    components.html(js, height=0)

# --- 3. ログイン画面 ---
if not st.session_state.logged_in:
    st.title("📖 英単語練習")
    u_in = st.text_input("名前 (ID):", key="login_user").strip()
    p_in = st.text_input("パスワード:", type="password", key="login_pass").strip()
    
    if st.button("ログイン / 新規登録", use_container_width=True):
        if u_in and p_in:
            if u_in in st.session_state.user_db:
                if st.session_state.user_db[u_in] == p_in:
                    st.session_state.current_user = u_in
                    st.session_state.logged_in = True
                    st.session_state.page = "main_menu"
                    st.rerun()
                else: st.error("パスワードが違います")
            else:
                st.session_state.user_db[u_in] = p_in
                st.session_state.current_user = u_in
                st.session_state.logged_in = True
                st.session_state.page = "main_menu"
                st.rerun()
    st.stop()

# サイドバー
st.sidebar.title(f"👤 {st.session_state.current_user}")
st.sidebar.info(f"学年: {get_current_grade()}")

# --- 4. メイン画面 ＆ 練習 ---
if st.session_state.page == "main_menu":
    st.header("メニュー")
    if st.button("🚀 学習スタート", use_container_width=True):
        grade = get_current_grade()
        all_words = st.session_state.word_db[grade]
        count = min(len(all_words), 3)
        st.session_state.session_words = random.sample(all_words, count)
        st.session_state.word_index = 0
        st.session_state.repeat_count = 1
        st.session_state.page = "training"
        st.rerun()

elif st.session_state.page == "training":
    word = st.session_state.session_words[st.session_state.word_index]
    st.header(f"練習 {st.session_state.repeat_count}/3回")
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
            if st.session_state.repeat_count < 3: st.session_state.repeat_count += 1
            else:
                st.session_state.repeat_count = 1
                st.session_state.word_index += 1
            if st.session_state.word_index >= len(st.session_state.session_words):
                st.session_state.test_words = list(st.session_state.session_words)
                grade = get_current_grade()
                past = [w for w in st.session_state.word_db[grade] if w not in st.session_state.test_words]
                if past: st.session_state.test_words.append(random.choice(past))
                random.shuffle(st.session_state.test_words)
                st.session_state.page = "test"
            st.rerun()

elif st.session_state.page == "test":
    if not st.session_state.test_words:
        # 【対策】テスト合格時にネタをセット
        neta_list = [
            "サンドウィッチマン伊達：カステラはギュッと潰せばカロリーも潰れるから0kcal。",
            "千鳥ノブ：昔、バラエティ番組の企画で1ヶ月だけ『ノブ小池』に改名していた。",
            "出川哲朗：実家は明治27年創業の老舗海苔問屋『蔦金商店』でお金持ち。",
            "やす子：実は元自衛官で、ドーザー（ブルドーザー）の運転ができる。",
            "チョコレートプラネット：TT兄弟のネタは、元々は別のネタの繋ぎで作ったもの。"
        ]
        st.session_state.current_neta = random.choice(neta_list)
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
            if st.session_state.penalty_count < 5: st.session_state.penalty_count += 1
            else:
                failed = st.session_state.test_words.pop(0)
                st.session_state.test_words.append(failed)
                st.session_state.page = "test"
            st.rerun()

elif st.session_state.page == "result":
    st.header("✨ 全問正解！おめでとう！ ✨")
    st.balloons()
    
    # 【対策】大きく分かりやすく表示
    st.success("🎁 ご褒美：お笑い芸人豆知識")
    st.markdown(f"### {st.session_state.current_neta}")
    
    if st.button("メインメニューへ戻る", use_container_width=True):
        st.session_state.page = "main_menu"
        st.rerun()
