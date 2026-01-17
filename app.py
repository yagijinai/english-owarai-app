import streamlit as st
import random
import streamlit.components.v1 as components
from datetime import datetime

# --- 1. ページ設定 ---
st.set_page_config(layout="centered", page_title="英単語レベルアップアプリ")

# --- 2. 学年と単語の管理 ---
def get_current_grade():
    today = datetime.now()
    year = today.year
    # 4月1日より前なら、年度としては前年扱い
    school_year = year if today.month >= 4 else year - 1
    
    # 娘さんが2025年度に中1（2026年1月現在は中1）という前提で計算
    # 2025年度:中1, 2026年度:中2, 2027年度:中3...
    base_year = 2025 
    grade_diff = school_year - base_year
    
    grades = ["中学1年生", "中学2年生", "中学3年生", "高校1年生", "高校2年生", "高校3年生"]
    if 0 <= grade_diff < len(grades):
        return grades[grade_diff]
    elif grade_diff < 0:
        return "入学準備（中1レベル）"
    else:
        return "高校卒業レベル"

def init_session_state():
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'page' not in st.session_state: st.session_state.page = "login"
    if 'user_name' not in st.session_state: st.session_state.user_name = "娘さん"
    if 'password' not in st.session_state: st.session_state.password = "1234"
    if 'streak' not in st.session_state: st.session_state.streak = 0

    # --- お父様が単語を追加・変更する場所 ---
    if 'word_db' not in st.session_state:
        st.session_state.word_db = {
            "中学1年生": [{"q": "食べる", "a": "eat"}, {"q": "話す", "a": "speak"}, {"q": "友達", "a": "friend"}],
            "中学2年生": [{"q": "経験", "a": "experience"}, {"q": "快適な", "a": "comfortable"}],
            "中学3年生": [{"q": "環境", "a": "environment"}, {"q": "影響", "a": "influence"}],
            "高校1年生": [{"q": "分析する", "a": "analyze"}, {"q": "重要な", "a": "significant"}],
            "高校2年生": [{"q": "経済", "a": "economy"}, {"q": "維持する", "a": "maintain"}],
            "高校3年生": [{"q": "哲学", "a": "philosophy"}, {"q": "複雑な", "a": "complicated"}]
        }
    
    # 現在の学年を判定して単語を読み込む
    current_grade = get_current_grade()
    st.session_state.master_words = st.session_state.word_db.get(current_grade, st.session_state.word_db["中学1年生"])
    st.session_state.current_grade_name = current_grade

    # 練習・テスト用変数
    if 'session_words' not in st.session_state: st.session_state.session_words = []
    if 'test_words' not in st.session_state: st.session_state.test_words = []
    if 'word_index' not in st.session_state: st.session_state.word_index = 0
    if 'repeat_count' not in st.session_state: st.session_state.repeat_count = 1
    if 'penalty_word' not in st.session_state: st.session_state.penalty_word = None
    if 'penalty_count' not in st.session_state: st.session_state.penalty_count = 0
    if 'show_hint' not in st.session_state: st.session_state.show_hint = False
    if 'input_key' not in st.session_state: st.session_state.input_key = 0

init_session_state()

def speak_word(word):
    js = f"<script>var m=new SpeechSynthesisUtterance('{word}');m.lang='en-US';window.speechSynthesis.speak(m);</script>"
    components.html(js, height=0)

# --- 3. ログイン画面 ---
if not st.session_state.logged_in:
    st.title("📖 成長する英単語帳")
    st.subheader(f"現在の設定学年: {st.session_state.current_grade_name}")
    
    user_in = st.text_input("名前:")
    pwd_in = st.text_input("パスワード:", type="password")
    
    if st.button("ログイン", use_container_width=True):
        if user_in == st.session_state.user_name and pwd_in == st.session_state.password:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("名前かパスワードが違います")
    st.stop()

# --- 4. サイドバー（管理画面） ---
st.sidebar.title("⚙ 設定")
st.sidebar.write(f"学年: {st.session_state.current_grade_name}")

if st.sidebar.checkbox("お父様メニュー（単語追加）"):
    st.sidebar.write("---")
    target_grade = st.sidebar.selectbox("追加する学年", list(st.session_state.word_db.keys()))
    new_q = st.sidebar.text_input("日本語の意味")
    new_a = st.sidebar.text_input("英単語")
    if st.sidebar.button("単語を追加する"):
        if new_q and new_a:
            st.session_state.word_db[target_grade].append({"q": new_q, "a": new_a})
            st.sidebar.success(f"{target_grade}に「{new_a}」を追加しました！")

# --- 5. メインメニュー ＆ 練習 ---
if st.session_state.page == "main_menu":
    st.header(f"頑張れ、{st.session_state.user_name}さん！")
    st.write(f"今は【{st.session_state.current_grade_name}】の単語を練習中だよ。")
    if st.button("🚀 学習スタート", use_container_width=True):
        # その学年の単語から3つ選ぶ
        available_words = st.session_state.master_words
        count = min(len(available_words), 3)
        st.session_state.session_words = random.sample(available_words, count)
        st.session_state.word_index = 0
        st.session_state.repeat_count = 1
        st.session_state.page = "training"
        st.rerun()

elif st.session_state.page == "training":
    word = st.session_state.session_words[st.session_state.word_index]
    st.header(f"練習 ({st.session_state.repeat_count}/3回目)")
    st.subheader(f"「{word['q']}」")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📢 発音を聞く"): speak_word(word['a'])
    with col2:
        if st.button("💡 答えを見る"): st.session_state.show_hint = True
    
    if st.session_state.show_hint: st.info(f"答え： {word['a']}")

    u_in = st.text_input("スペルを入力:", key=f"t_{st.session_state.input_key}").strip().lower()
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
                # テスト準備（今日の単語 ＋ 過去のランダム1語）
                st.session_state.test_words = list(st.session_state.session_words)
                other_words = [w for w in st.session_state.master_words if w not in st.session_state.test_words]
                if other_words:
                    st.session_state.test_words.append(random.choice(other_words))
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
    st.subheader(f"「{word['q']}」を英語で？")
    if st.button("📢 発音"): speak_word(word['a'])

    t_in = st.text_input("回答:", key=f"v_{st.session_state.input_key}").strip().lower()
    if st.button("テスト判定", use_container_width=True):
        if t_in == word['a']:
            st.session_state.test_words.pop(0) # 正解したらリストから消す
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
                # 特訓終了。間違えた単語をテストリストの最後に回す
                failed = st.session_state.test_words.pop(0)
                st.session_state.test_words.append(failed)
                st.session_state.page = "test"
            st.rerun()

elif st.session_state.page == "result":
    st.header("全問正解！すごいぞ！ 🎉")
    st.balloons()
    if st.button("メインメニューへ", use_container_width=True):
        st.session_state.streak += 1
        st.session_state.page = "main_menu"
        st.rerun()
