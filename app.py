import streamlit as st
import random
import time
import json
import csv
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. ページ設定 ---
st.set_page_config(layout="centered", page_title="英単語練習アプリ")

# --- 2. CSV読み込み関数 ---
def load_csv_data(filename):
    data = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if filename == 'words.csv' and len(row) >= 3:
                    data.append({"grade": row[0].strip(), "q": row[1].strip(), "a": row[2].strip().lower()})
                elif filename == 'neta.csv' and row:
                    data.append(row[0])
    except Exception as e:
        st.error(f"ファイル {filename} の読み込みに失敗しました。")
    return data

# --- 3. Firebase / セッション初期化 ---
def init_firebase_live():
    if not firebase_admin._apps:
        try:
            if "FIREBASE_SECRET" in st.secrets:
                key_dict = json.loads(st.secrets["FIREBASE_SECRET"])
                cred = credentials.Certificate(key_dict)
                firebase_admin.initialize_app(cred)
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
        'current_episode': "", 'user_grade': "中1", 'grade_expiry': ""
    }
    for key, value in defaults.items():
        if key not in st.session_state: st.session_state[key] = value

init_session_state()
if not st.session_state.logged_in:
    st.title("🔐 クラウド・ログイン")
    
    # 端末に記録がある場合、同じIDで始めるか聞く
    if st.session_state.last_user:
        st.subheader(f"「{st.session_state.last_user}」さんですね？")
        st.write("このIDでつづけますか？")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("はい、これで始める", use_container_width=True):
                doc = st.session_state.db.collection("users").document(st.session_state.last_user).get()
                if doc.exists:
                    data = doc.to_dict()
                    st.session_state.current_user = st.session_state.last_user
                    st.session_state.streak = data.get('streak', 0)
                    st.session_state.learned_words = data.get('learned', [])
                    st.session_state.user_grade = data.get('grade', "中1")
                    st.session_state.grade_expiry = data.get('expiry', "")
                    st.session_state.logged_in = True
                    st.session_state.page = "main_menu"
                    st.rerun()
        with c2:
            if st.button("別のIDを使う", use_container_width=True):
                st.session_state.last_user = None
                st.rerun()
    else:
        # 新規または別IDログイン
        u_in = st.text_input("名前 (ID) を入れてね:").strip()
        p_in = st.text_input("パスワード:", type="password").strip()
        
        # 学年を質問
        st.write("---")
        grade_in = st.selectbox("あなたの学年を教えてね（3月31日まで固定されます）:", 
                                ["中1", "中2", "中3", "高1", "高2", "高3"])
        
        if st.button("ログイン / 新規登録", use_container_width=True):
            if u_in and p_in:
                # 3月31日までの期限を計算
                now = datetime.now()
                expiry_year = now.year if now.month <= 3 else now.year + 1
                expiry_date = f"{expiry_year}-03-31"
                
                doc_ref = st.session_state.db.collection("users").document(u_in)
                doc = doc_ref.get()
                if doc.exists:
                    if doc.to_dict()['password'] == p_in:
                        data = doc.to_dict()
                        st.session_state.current_user = u_in
                        st.session_state.last_user = u_in
                        # 既存ユーザーでも期限が切れていれば学年を更新
                        if not data.get('expiry') or datetime.now().strftime("%Y-%m-%d") > data.get('expiry'):
                            doc_ref.update({"grade": grade_in, "expiry": expiry_date})
                            st.session_state.user_grade = grade_in
                        else:
                            st.session_state.user_grade = data.get('grade')
                        st.session_state.logged_in = True
                        st.session_state.page = "main_menu"
                        st.rerun()
                    else: st.error("パスワードが違います")
                else:
                    # 完全新規登録
                    doc_ref.set({"password": p_in, "streak": 0, "learned": [], "grade": grade_in, "expiry": expiry_date})
                    st.session_state.current_user = u_in
                    st.session_state.last_user = u_in
                    st.session_state.user_grade = grade_in
                    st.session_state.logged_in = True
                    st.session_state.page = "main_menu"
                    st.rerun()
    st.stop()
    if st.session_state.page == "main_menu":
    st.header(f"🔥 {st.session_state.user_grade}コース")
    st.write(f"（3月31日までこの学年を練習します）")
    st.subheader(f"連続学習: {st.session_state.streak}日目")

    if st.button("🚀 今日の練習を始める", use_container_width=True):
        all_csv_words = load_csv_data('words.csv')
        # 学年が一致する単語だけを抽出
        grade_words = [w for w in all_csv_words if w['grade'] == st.session_state.user_grade]
        
        if not grade_words:
            st.error(f"{st.session_state.user_grade} の単['words.csv']にデータがありません。")
            st.stop()
            
        unlearned = [w for w in grade_words if w['a'] not in st.session_state.learned_words]
        if len(unlearned) < 3: st.session_state.learned_words = []
        
        st.session_state.session_words = random.sample(unlearned if len(unlearned)>=3 else grade_words, 3)
        st.session_state.success_counts = {w['a']: 0 for w in st.session_state.session_words}
        st.session_state.page = "training"
        st.rerun()

elif st.session_state.page == "training":
    active = [w for w in st.session_state.session_words if st.session_state.success_counts[w['a']] < 3]
    if not active:
        st.session_state.test_words = list(st.session_state.session_words)
        random.shuffle(st.session_state.test_words)
        st.session_state.page = "test"
        st.rerun()

    if 'target_wa' not in st.session_state or st.session_state.target_wa not in [w['a'] for w in active]:
        target = random.choice(active)
        st.session_state.target_wq, st.session_state.target_wa = target['q'], target['a']
    
    st.subheader(f"「{st.session_state.target_wq}」 ({st.session_state.success_counts[st.session_state.target_wa] + 1}/3回)")
    u_in = st.text_input("スペル入力:", key=f"t_{st.session_state.input_key}").strip().lower()
    if st.button("判定"):
        if u_in == st.session_state.target_wa:
            st.session_state.success_counts[st.session_state.target_wa] += 1
            st.session_state.input_key += 1
            del st.session_state.target_wa
            st.rerun()
            elif st.session_state.page == "miss_drill":
    st.warning(f"🚨 特訓！「{st.session_state.missed_word['q']}」を5回書こう")
    st.subheader(f"({st.session_state.missed_count + 1}/5回)")
    d_in = st.text_input("スペル:", key=f"d_{st.session_state.input_key}").strip().lower()
    if st.button("判定"):
        if d_in == st.session_state.missed_word['a']:
            st.session_state.missed_count += 1
            st.session_state.input_key += 1
            if st.session_state.missed_count >= 5:
                st.session_state.page = "test"
                st.session_state.missed_word = None
                st.session_state.missed_count = 0
            st.rerun()

elif st.session_state.page == "test":
    if not st.session_state.test_words:
        st.session_state.streak += 1
        st.session_state.db.collection("users").document(st.session_state.current_user).update({
            "streak": st.session_state.streak, "learned": st.session_state.learned_words
        })
        episodes = load_csv_data('neta.csv')
        st.session_state.current_episode = random.choice(episodes) if episodes else "ネタ募集中！"
        st.session_state.page = "result"
        st.rerun()

    word = st.session_state.test_words[0]
    st.subheader(f"最終テスト: 「{word['q']}」")
    t_in = st.text_input("答え:", key=f"v_{st.session_state.input_key}").strip().lower()
    if st.button("判定"):
        if t_in == word['a']:
            if word['a'] not in st.session_state.learned_words:
                st.session_state.learned_words.append(word['a'])
            st.session_state.test_words.pop(0)
            st.session_state.input_key += 1
            st.rerun()
        else:
            st.error("間違い！特訓開始！")
            time.sleep(1)
            st.session_state.missed_word, st.session_state.missed_count = word, 0
            st.session_state.page = "miss_drill"
            st.rerun()

elif st.session_state.page == "result":
    st.header("🎉 合格！")
    st.balloons()
    st.info(st.session_state.current_episode)
    if st.button("メニューへ戻る"):
        st.session_state.page = "main_menu"
        st.rerun()
