import streamlit as st
import random
import streamlit.components.v1 as components
from datetime import datetime
import time

# --- 1. ページ設定 ---
st.set_page_config(layout="centered", page_title="英単語練習アプリ")

# --- 2. Firebase設定 (画像から取得した情報を反映済み) ---
def init_firebase_sync():
    # 画像の config 情報をセット
    st.session_state.firebase_config = {
        "apiKey": "AIzaSyD4Y2BfabSxlmddoCWJCgXNRbPTpUqHxF0",
        "authDomain": "english-app-c7d19.firebaseapp.com",
        "projectId": "english-app-c7d19",
        "storageBucket": "english-app-c7d19.firebasestorage.app",
        "messagingSenderId": "737877180458",
        "appId": "1:737877180458:web:94d346c2aa284092958353"
    }
    
    # クラウド代わりの仮DB（Firebase通信の本格実装までの繋ぎ）
    if 'cloud_db' not in st.session_state:
        st.session_state.cloud_db = {
            "お父様": {"p": "1234", "s": 10, "l": []},
            "娘さん": {"p": "1234", "s": 10, "l": []}
        }

def init_session_state():
    init_firebase_sync()
    # 画像のエラー(AttributeError)を完全に防ぐための初期化
    defaults = {
        'logged_in': False,
        'page': "login",
        'last_user': None,
        'current_user': "",
        'streak': 10,
        'learned_words': [], 
        'session_words': [],
        'success_counts': {},
        'test_words': [],
        'penalty_word': None,
        'penalty_count': 0,
        'show_hint': False,
        'input_key': 0,
        'confirm_register': False,
        'word_db': {
            "中学1年生": [
                {"q": "りんご", "a": "apple"}, {"q": "本", "a": "book"}, {"q": "猫", "a": "cat"}, 
                {"q": "犬", "a": "dog"}, {"q": "ペン", "a": "pen"}, {"q": "机", "a": "desk"}
            ]
        }
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

def speak_word(word):
    js = f"<script>var m=new SpeechSynthesisUtterance('{word}');m.lang='en-US';window.speechSynthesis.speak(m);</script>"
    components.html(js, height=0)

# --- 3. ログイン管理 ---
if not st.session_state.logged_in:
    st.title("🔐 ログイン")
    
    if st.session_state.last_user:
        st.subheader("同じ端末でアプリをスタートします。")
        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"同じID ({st.session_state.last_user}) で続ける", use_container_width=True):
                user_data = st.session_state.cloud_db.get(st.session_state.last_user)
                st.session_state.current_user = st.session_state.last_user
                st.session_state.streak = user_data['s']
                st.session_state.learned_words = user_data['l']
                st.session_state.logged_in = True
                st.session_state.page = "main_menu"
                st.rerun()
        with c2:
            if st.button("違うIDではじめる", use_container_width=True):
                st.session_state.last_user = None
                st.rerun()
    else:
        u_in = st.text_input("名前 (ID):").strip()
        p_in = st.text_input("パスワード:", type="password").strip()
        col_l, col_r = st.columns(2)
        with col_l:
            if st.button("ログイン", use_container_width=True):
                if u_in in st.session_state.cloud_db and st.session_state.cloud_db[u_in]['p'] == p_in:
                    user_data = st.session_state.cloud_db[u_in]
                    st.session_state.current_user = u_in
                    st.session_state.last_user = u_in
                    st.session_state.streak = user_data['s']
                    st.session_state.learned_words = user_data['l']
                    st.session_state.logged_in = True
                    st.session_state.page = "main_menu"
                    st.rerun()
                else: st.error("名前またはパスワードが違います")
        with col_r:
            if st.button("新規登録", use_container_width=True):
                if u_in and p_in: st.session_state.confirm_register = True
        
        if st.session_state.confirm_register:
            if st.button(f"「{u_in}」を登録して開始"):
                st.session_state.cloud_db[u_in] = {"p": p_in, "s": 0, "l": []}
                st.session_state.current_user = u_in
                st.session_state.last_user = u_in
                st.session_state.logged_in = True
                st.session_state.page = "main_menu"
                st.rerun()
    st.stop()

# --- 4. メインメニュー ＆ 練習 ---
if st.session_state.page == "main_menu":
    st.header(f"🔥 連続 {st.session_state.streak}日目")
    st.subheader(f"こんにちは、{st.session_state.current_user}さん！")
    
    if st.button("🚀 学習スタート", use_container_width=True):
        all_words = st.session_state.word_db["中学1年生"]
        unlearned = [w for w in all_words if w['a'] not in st.session_state.learned_words]
        if len(unlearned) < 3:
            st.session_state.learned_words = []
            unlearned = all_words
            
        st.session_state.session_words = random.sample(unlearned, 3)
        st.session_state.success_counts = {w['a']: 0 for w in st.session_state.session_words}
        st.session_state.page = "training"
        st.rerun()

elif st.session_state.page == "training":
    active = [w for w in st.session_state.session_words if st.session_state.success_counts[w['a']] < 3]
    if not active:
        st.session_state.test_words = list(st.session_state.session_words)
        st.session_state.page = "test"
        st.rerun()

    if 'target_w' not in st.session_state or st.session_state.target_w not in [w['a'] for w in active]:
        st.session_state.target_w = random.choice(active)['a']
    
    word = next(w for w in st.session_state.session_words if w['a'] == st.session_state.target_w)
    st.subheader(f"「{word['q']}」 (成功: {st.session_state.success_counts[word['a']]} / 3回)")

    u_in = st.text_input("スペル入力:", key=f"t_{st.session_state.input_key}").strip().lower()
    if st.button("判定", use_container_width=True):
        if u_in == word['a']:
            st.session_state.success_counts[word['a']] += 1
            st.session_state.input_key += 1
            del st.session_state.target_w
            st.rerun()
        else:
            st.error("おしい！もう一度書いてみよう")

elif st.session_state.page == "test":
    if not st.session_state.test_words:
        st.session_state.streak += 1
        # クラウド保存をシミュレート（パート1のFirebase Configを使って連携可能）
        st.session_state.cloud_db[st.session_state.current_user].update({
            "s": st.session_state.streak, "l": st.session_state.learned_words
        })
        st.session_state.page = "result"
        st.rerun()

    word = st.session_state.test_words[0]
    st.subheader(f"復習テスト: 「{word['q']}」は？")
    t_in = st.text_input("回答:", key=f"v_{st.session_state.input_key}").strip().lower()
    if st.button("判定"):
        if t_in == word['a']:
            st.success("✨ 正解！ ✨")
            time.sleep(0.5)
            if word['a'] not in st.session_state.learned_words:
                st.session_state.learned_words.append(word['a'])
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
    p_in = st.text_input(f"入力 {st.session_state.penalty_count}:", key=f"p_{st.session_state.input_key}").strip().lower()
    if st.button("送信"):
        if p_in == word['a']:
            st.session_state.input_key += 1
            if st.session_state.penalty_count < 5: st.session_state.penalty_count += 1
            else:
                st.session_state.test_words.append(st.session_state.test_words.pop(0))
                st.session_state.page = "test"
            st.rerun()

elif st.session_state.page == "result":
    st.header("🎉 合格！")
    st.balloons()
    if st.button("メニューへ戻る"):
        st.session_state.page = "main_menu"
        st.rerun()
