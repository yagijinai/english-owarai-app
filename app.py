import streamlit as st
import random
import time
import json
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. ページ設定 ---
st.set_page_config(layout="centered", page_title="英単語練習アプリ")

# --- 2. Firebase連携 ---
def init_firebase_live():
    if not firebase_admin._apps:
        try:
            if "FIREBASE_SECRET" in st.secrets:
                key_dict = json.loads(st.secrets["FIREBASE_SECRET"])
                cred = credentials.Certificate(key_dict)
                firebase_admin.initialize_app(cred)
            else:
                st.error("設定画面(Secrets)に鍵が入力されていません。")
        except Exception as e:
            st.error(f"接続失敗: {e}")

    if 'db' not in st.session_state:
        st.session_state.db = firestore.client()

def init_session_state():
    init_firebase_live()
    defaults = {
        'logged_in': False, 'page': "login", 'last_user': None, 'current_user': "",
        'streak': 0, 'learned_words': [], 'session_words': [], 'success_counts': {},
        'test_words': [], 'input_key': 0, 'missed_word': None, 'missed_count': 0,
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
    st.title("🔐 クラウド・ログイン")
    
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
            if st.button("いいえ（別のIDを使う）", use_container_width=True):
                st.session_state.last_user = None
                st.rerun()
    else:
        u_in = st.text_input("ID (名前):").strip()
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
        random.shuffle(st.session_state.test_words) # テストはランダムな順序で
        st.session_state.page = "test"
        st.rerun()

    if 'target_wa' not in st.session_state or st.session_state.target_wa not in [w['a'] for w in active]:
        target = random.choice(active)
        st.session_state.target_wq = target['q']
        st.session_state.target_wa = target['a']
    
    count_display = st.session_state.success_counts[st.session_state.target_wa] + 1
    st.subheader(f"「{st.session_state.target_wq}」 ({count_display}/3回)")
    u_in = st.text_input("スペル入力:", key=f"t_{st.session_state.input_key}").strip().lower()
    if st.button("判定"):
        if u_in == st.session_state.target_wa:
            st.session_state.success_counts[st.session_state.target_wa] += 1
            st.session_state.input_key += 1
            del st.session_state.target_wa
            st.rerun()

# ミス時の特訓モード
elif st.session_state.page == "miss_drill":
    st.warning(f"🚨 特訓中！「{st.session_state.missed_word['q']}」を5回書こう")
    st.subheader(f"「{st.session_state.missed_word['q']}」 ({st.session_state.missed_count + 1}/5回)")
    d_in = st.text_input("スペル:", key=f"d_{st.session_state.input_key}").strip().lower()
    if st.button("判定"):
        if d_in == st.session_state.missed_word['a']:
            st.session_state.missed_count += 1
            st.session_state.input_key += 1
            if st.session_state.missed_count >= 5:
                # 特訓終了！テストリストをシャッフルしてテスト画面へ戻る
                random.shuffle(st.session_state.test_words)
                st.session_state.page = "test"
                st.session_state.missed_word = None
                st.session_state.missed_count = 0
            st.rerun()

elif st.session_state.page == "test":
    # 合格していない単語がなくなれば終了
    if not st.session_state.test_words:
        st.session_state.streak += 1
        st.session_state.db.collection("users").document(st.session_state.current_user).update({
            "streak": st.session_state.streak, "learned": st.session_state.learned_words
        })
        st.session_state.page = "result"
        st.rerun()

    # テスト単語リストの先頭から出題
    word = st.session_state.test_words[0]
    st.subheader(f"最終テスト: 「{word['q']}」")
    t_in = st.text_input("答え:", key=f"v_{st.session_state.input_key}").strip().lower()
    
    if st.button("判定"):
        if t_in == word['a']:
            st.success("正解！合格です。")
            time.sleep(0.5)
            if word['a'] not in st.session_state.learned_words:
                st.session_state.learned_words.append(word['a'])
            # 合格したのでリストから消す
            st.session_state.test_words.pop(0)
            st.session_state.input_key += 1
            st.rerun()
        else:
            st.error(f"間違い！「{word['a']}」を5回特訓します。")
            time.sleep(1.5)
            # 間違えた単語を特訓へ
            st.session_state.missed_word = word
            st.session_state.missed_count = 0
            st.session_state.page = "miss_drill"
            # テストリストの中身は消さずに残しておく（特訓後に再挑戦するため）
            st.rerun()

elif st.session_state.page == "result":
    st.header("🎉 全問合格！保存しました")
    st.balloons()
    if st.button("メニューへ戻る"):
        st.session_state.page = "main_menu"
        st.rerun()
