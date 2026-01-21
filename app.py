import streamlit as st
import random
import streamlit.components.v1 as components
from datetime import datetime
import time
import json
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. ページ設定 ---
st.set_page_config(layout="centered", page_title="英単語練習アプリ")

# --- 2. Firebase連携 (GitHub Secretsの鍵を使用) ---
def init_firebase_live():
    # Firebaseが未初期化の場合のみ実行
    if not firebase_admin._apps:
        try:
            # GitHubの「金庫(FIREBASE_SECRET)」から鍵を取り出す
            if "FIREBASE_SECRET" in st.secrets:
                key_dict = json.loads(st.secrets["FIREBASE_SECRET"])
                cred = credentials.Certificate(key_dict)
                firebase_admin.initialize_app(cred)
            else:
                st.error("GitHub Secretsに鍵が設定されていません。")
        except Exception as e:
            st.error(f"Firebase接続失敗: {e}")

    # Firestore（データベース）を使える状態にする
    if 'db' not in st.session_state:
        st.session_state.db = firestore.client()

def init_session_state():
    init_firebase_live()
    # 全ての変数を確実に初期化（AttributeErrorなどのエラー防止）
    defaults = {
        'logged_in': False, 'page': "login", 'last_user': None, 'current_user': "",
        'streak': 0, 'learned_words': [], 'session_words': [], 'success_counts': {},
        'test_words': [], 'penalty_word': None, 'penalty_count': 0, 'input_key': 0,
        'confirm_register': False,
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

# --- 3. ログイン画面 ---
if not st.session_state.logged_in:
    st.title("🔐 クラウド・ログイン")
    
    # 前回の利用者がいる場合、二択からスタート
    if st.session_state.last_user:
        st.subheader("同じIDでつづけますか？")
        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"はい ({st.session_state.last_user})", use_container_width=True):
                # クラウドからデータを復元
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
        # 新しいIDでのログイン/登録
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
                else: # 新規作成
                    doc_ref.set({"password": p_in, "streak": 0, "learned": []})
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
        all_w = st.session_state.word_db["中学1年生"]
        # 未学習のものを優先
        unlearned = [w for w in all_w if w['a'] not in st.session_state.learned_words]
        if len(unlearned) < 3: st.session_state.learned_words = []
        
        # 3問選んで練習開始
        st.session_state.session_words = random.sample(unlearned if len(unlearned)>=3 else all_w, 3)
        st.session_state.success_counts = {w['a']: 0 for w in st.session_state.session_words}
        st.session_state.page = "training"
        st.rerun()

elif st.session_state.page == "training":
    # まだ3回成功していない単語を表示
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

elif st.session_state.page == "test":
    if not st.session_state.test_words:
        # すべて終わったらクラウドの情報を更新
        st.session_state.streak += 1
        st.session_state.db.collection("users").document(st.session_state.current_user).update({
            "streak": st.session_state.streak,
            "learned": st.session_state.learned_words
        })
        st.session_state.page = "result"
        st.rerun()

    word = st.session_state.test_words[0]
    st.subheader(f"仕上げテスト: 「{word['q']}」は？")
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
            st.error("間違えたので練習メニューに戻ります！")
            time.sleep(1)
            st.session_state.page = "main_menu"
            st.rerun()

elif st.session_state.page == "result":
    st.header("🎉 クラウドに保存完了！")
    st.balloons()
    if st.button("メニューへ戻る"):
        st.session_state.page = "main_menu"
        st.rerun()
