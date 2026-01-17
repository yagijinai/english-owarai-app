import streamlit as st
import random
import streamlit.components.v1 as components
from datetime import datetime

# --- 1. ページ設定 ---
st.set_page_config(layout="centered", page_title="英単語練習アプリ")

# --- 2. セッション状態の初期化 (エラー対策強化版) ---
def init_session_state():
    # 必須変数のリストと初期値
    defaults = {
        'logged_in': False,
        'page': "login",
        'user_db': {"お父様": "1234", "娘さん": "1234"},
        'current_user': "",
        'streak': 10,
        'learned_words': [],
        'session_words': [],
        'test_words': [],
        'word_index': 0,
        'repeat_count': 1,
        'penalty_word': None,
        'penalty_count': 0,
        'show_hint': False,
        'input_key': 0,
        'current_neta': "",
        'word_db': {
            "中学1年生": [{"q": "りんご", "a": "apple"}, {"q": "本", "a": "book"}, {"q": "猫", "a": "cat"}, {"q": "犬", "a": "dog"}, {"q": "ペン", "a": "pen"}],
            "中学2年生": [{"q": "経験", "a": "experience"}, {"q": "快適な", "a": "comfortable"}],
            "中学3年生": [{"q": "環境", "a": "environment"}, {"q": "影響", "a": "influence"}]
        }
    }
    # 変数がsession_stateに存在しない場合のみ作成
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

def get_current_grade():
    try:
        today = datetime.now()
        school_year = today.year if today.month >= 4 else today.year - 1
        grade_diff = school_year - 2025
        grades = ["中学1年生", "中学2年生", "中学3年生", "高校1年生", "高校2年生", "高校3年生"]
        return grades[grade_diff] if 0 <= grade_diff < len(grades) else "中学1年生"
    except:
        return "中学1年生"

def speak_word(word):
    js = f"<script>var m=new SpeechSynthesisUtterance('{word}');m.lang='en-US';window.speechSynthesis.speak(m);</script>"
    components.html(js, height=0)

# --- 3. ログイン画面 ---
if not st.session_state.logged_in:
    st.title("📖 英単語練習アプリ")
    u_in = st.text_input("名前 (ID):", key="main_u_in").strip()
    p_in = st.text_input("パスワード:", type="password", key="main_p_in").strip()
    
    if st.button("ログイン / 新規登録", use_container_width=True):
        if u_in and p_in:
            if u_in in st.session_state.user_db:
                if st.session_state.user_db[u_in] == p_in:
                    st.session_state.current_user = u_in
                    st.session_state.logged_in = True
                    st.rerun()
                else: st.error("パスワードが違います")
            else:
                st.session_state.user_db[u_in] = p_in
                st.session_state.current_user = u_in
                st.session_state.logged_in = True
                st.rerun()
    st.stop()

# サイドバー表示 (画像にあったステータス画面)
st.sidebar.markdown(f"### ステータス\n👤 {st.session_state.current_user}")
st.sidebar.markdown(f"🔥 連続学習: {st.session_state.streak}日")
if st.sidebar.button("ログアウト"):
    st.session_state.logged_in = False
    st.rerun()

# --- 4. メイン画面 ＆ 練習 ---
if st.session_state.page == "main_menu":
    st.header(f"連続 {st.session_state.streak}日目！")
    if st.button("🚀 学習スタート", use_container_width=True):
        grade = get_current_grade()
        all_words = st.session_state.word_db.get(grade, st.session_state.word_db["中学1年生"])
        
        # 未習単語の抽出
        unlearned = [w for w in all_words if w['a'] not in st.session_state.learned_words]
        if not unlearned:
            st.session_state.learned_words = []
            unlearned = all_words
            
        st.session_state.session_words = random.sample(unlearned, min(len(unlearned), 3))
        st.session_state.word_index = 0
        st.session_state.repeat_count = 1
        st.session_state.page = "training"
        st.rerun()

elif st.session_state.page == "training":
    # 安全策：リストが空なら戻す
    if not st.session_state.session_words:
        st.session_state.page = "main_menu"
        st.rerun()
        
    word = st.session_state.session_words[st.session_state.word_index]
    st.header(f"練習 {st.session_state.word_index+1}/3")
    st.subheader(f"「{word['q']}」")
    
    c1, c2 = st.columns(2)
    with c1: 
        if st.button("📢 音声"): speak_word(word['a'])
    with c2:
        if st.button("💡 答え"): st.session_state.show_hint = True
    if st.session_state.show_hint: st.info(f"正解： {word['a']}")

    u_in = st.text_input("スペルを入力:", key=f"in_{st.session_state.input_key}").strip().lower()
    if st.button("判定", use_container_width=True):
        if u_in == word['a']:
            st.session_state.show_hint = False
            st.session_state.input_key += 1
            if st.session_state.repeat_count < 3: st.session_state.repeat_count += 1
            else:
                if word['a'] not in st.session_state.learned_words:
                    st.session_state.learned_words.append(word['a'])
                st.session_state.repeat_count = 1
                st.session_state.word_index += 1
                
            if st.session_state.word_index >= len(st.session_state.session_words):
                # 復習テスト：今日の3語 ＋ 過去の1語
                st.session_state.test_words = list(st.session_state.session_words)
                grade = get_current_grade()
                past = [w for w in st.session_state.word_db[grade] if w['a'] in st.session_state.learned_words and w not in st.session_state.session_words]
                if past: st.session_state.test_words.append(random.choice(past))
                random.shuffle(st.session_state.test_words)
                st.session_state.page = "test"
            st.rerun()

elif st.session_state.page == "test":
    if not st.session_state.test_words:
        st.session_state.current_neta = random.choice([
            "サンドウィッチマン伊達：カステラはギュッと潰せばカロリーも潰れるから0kcal。",
            "千鳥ノブ：昔、バラエティ番組の企画で1ヶ月だけ『ノブ小池』に改名していた。",
            "出川哲朗：実家は老舗海苔問屋『蔦金商店』でお金持ち。"
        ])
        st.session_state.streak += 1 # 継続日数を増やす
        st.session_state.page = "result"
        st.rerun()

    word = st.session_state.test_words[0]
    st.header(f"復習テスト (残り {len(st.session_state.test_words)}問)")
    st.subheader(f"「{word['q']}」は？")
    
    t_in = st.text_input("回答:", key=f"v_{st.session_state.input_key}").strip().lower()
    if st.button("判定"):
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
    if st.button("送信"):
        if p_in == word['a']:
            st.session_state.input_key += 1
            if st.session_state.penalty_count < 5: st.session_state.penalty_count += 1
            else:
                st.session_state.test_words.append(st.session_state.test_words.pop(0))
                st.session_state.page = "test"
            st.rerun()

elif st.session_state.page == "result":
    st.header("✨ 全問正解！ ✨")
    st.balloons()
    st.info(f"🔥 連続学習 {st.session_state.streak}日達成！")
    st.success(f"🎁 ご褒美：{st.session_state.current_neta}")
    if st.button("メニューへ戻る", use_container_width=True):
        st.session_state.page = "main_menu"
        st.rerun()
