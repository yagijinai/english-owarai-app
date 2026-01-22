import streamlit as st
import random
import time
import json
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. ページ設定 ---
st.set_page_config(layout="centered", page_title="英単語練習アプリ")

# --- 2. Firebase連携 (GitHub Secretsを使用) ---
def init_firebase_live():
    if not firebase_admin._apps:
        try:
            if "FIREBASE_SECRET" in st.secrets:
                key_dict = json.loads(st.secrets["FIREBASE_SECRET"])
                cred = credentials.Certificate(key_dict)
                firebase_admin.initialize_app(cred)
            else:
                st.error("GitHub Secretsに鍵が見つかりません。")
        except Exception as e:
            st.error(f"接続失敗: {e}")

    if 'db' not in st.session_state:
        st.session_state.db = firestore.client()

def init_session_state():
    init_firebase_live()
    defaults = {
        'logged_in': False, 'page': "login", 'last_user': None, 'current_user': "",
        'streak': 0, 'learned_words': [], 'session_words': [], 'success_counts': {},
        'test_words': [], 'input_key': 0,
        'word_db': {
            "中学1年生": [
                {"q": "りんご", "a": "apple"}, {"q": "本", "a": "book"}, {"q": "猫", "a": "cat"}, 
                {"q": "犬", "a": "dog"}, {"q": "ペン", "a": "pen"}, {"q": "机", "a": "desk"}
            ]
        }
    }
    for key, value in defaults.items():
        if key not in st.session_state: st.session_state[key] = value

init_session_state()

if not st.session_state.logged_in:
    st.title("🔐 クラウド英単語練習")
    
    if st.session_state.last_user:
        st.subheader("同じIDでつづけますか？")
        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"はい ({st.session_state.last_user})", use_container_width=True):
                doc = st.session_state.db.collection("users").document(st.session_state.last_user).get()
                if doc.exists:
                    data = doc.to_dict()
                    st.session_state.current_user = st.session_state.last_user
                    st.session_state.streak = data.get('streak', 0)
                    st.session_state.learned_words = data.get('learned', [])
                    st.session_state.logged_in = True
                    st.session_state.page = "main_menu"
                    st.rerun()
        with c2:
            if st.button("いいえ（新しいID）", use_container_width=True):
                st.session_state.last_user = None
                st.rerun()
    else:
        u_in = st.text_input("名前 (ID):").strip()
        p_in = st.text_input("パスワード:", type="password").strip()
        if st.button("ログイン / 新規登録", use_container_width=True):
            if u_in and p_in:
                doc_ref = st.session_state.db.collection("users").document(u_in)
                doc = doc_ref.get()
                if doc.exists:
                    if doc.to_dict()['password'] == p_in:
                        data = doc.to_dict()
                        st.session_state.current_user = u_in
                        st.session_state.last_user = u_in
                        st.session_state.streak = data.get('streak', 0)
                        st.session_state.learned_words = data.get('learned', [])
                        st.session_state.logged_in = True
                        st.session_state.page = "main_menu"
                        st.rerun()
                    else: st.error("パスワードが違います")
                else:
                    doc_ref.set({"password": p_in, "streak": 0, "learned": []})
                    st.session_state.current_user = u_in
                    st.session_state.last_user = u_in
                    st.session_state.logged_in = True
                    st.session_state.page = "main_menu"
                    st.rerun()
    st.stop()

if st.session_state.page == "main_menu":
    st.header(f"🔥 連続 {st.session_state.streak}日目")
    if st.button("🚀 学習スタート", use_container_width=True):
        all_w = st.session_state.word_db["中学1年生"]
        unlearned = [w for w in all_w if w['a'] not in st.session_state.learned_words]
        if len(unlearned) < 3: st.session_state.learned_words = []
        st.session_state.session_words = random.sample(unlearned if len(unlearned)>=3 else all_w, 3)
        st.session_state.success_counts = {w['a']: 0 for w in st.session_state.session_words}
        st.session_state.page = "training"
        st.rerun()

elif st.session_state.page == "training":
    active = [w for w in st.session_state.session_words if st.session_state.success_counts[w['a']] < 3]
    if not active:
        st.session_state.test_words = list(st.session_state.session_words)
        st.session_state.page = "test"
        st.rerun()

    if 'target_wa' not in st.session_state or st.session_state.target_wa not in [w['a'] for w in active]:
        target = random.choice(active)
        st.session_state.target_wq = target['q']
        st.session_state.target_wa = target['a']
    
    st.subheader(f"「{st.session_state.target_wq}」 ({st.session_state.success_counts[st.session_state.target_wa]}/3回)")
    u_in = st.text_input("スペル入力:", key=f"t_{st.session_state.input_key}").strip().lower()
    if st.button("判定"):
        if u_in == st.session_state.target_wa:
            st.session_state.success_counts[st.session_state.target_wa] += 1
            st.session_state.input_key += 1
            del st.session_state.target_wa
            st.rerun()

elif st.session_state.page == "test":
    if not st.session_state.test_words:
        st.session_state.streak += 1
        st.session_state.db.collection("users").document(st.session_state.current_user).update({
            "streak": st.session_state.streak, "learned": st.session_state.learned_words
        })
        st.session_state.page = "result"
        st.rerun()

    word = st.session_state.test_words[0]
    st.subheader(f"テスト: 「{word['q']}」は？")
    t_in = st.text_input("回答:", key=f"v_{st.session_state.input_key}").strip().lower()
    if st.button("判定"):
        if t_in == word['a']:
            st.success("✨ 正解！")
            time.sleep(0.5)
            if word['a'] not in st.session_state.learned_words:
                st.session_state.learned_words.append(word['a'])
            st.session_state.test_words.pop(0)
            st.session_state.input_key += 1
            st.rerun()
        else:
            st.session_state.page = "main_menu"
            st.rerun()

elif st.session_state.page == "result":
    st.header("🎉 保存完了！")
    st.balloons()
    if st.button("戻る"):
        st.session_state.page = "main_menu"
        st.rerun()
