import streamlit as st
import random
import time
import json
import csv
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# --- ページ設定 ---
st.set_page_config(layout="centered", page_title="英単語マスター", page_icon="📝")

# --- 共通関数：データ読み込み ---
def load_csv_data(filename):
    data = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row: continue
                if filename == 'words.csv' and len(row) >= 3:
                    data.append({"grade": row[0].strip(), "q": row[1].strip(), "a": row[2].strip().lower()})
                elif filename == 'neta.csv' and len(row) >= 2:
                    data.append({"name": row[0].strip(), "story": row[1].strip()})
    except Exception: pass
    return data

# --- Firebase初期化 ---
def init_firebase():
    if not firebase_admin._apps:
        try:
            if "FIREBASE_SECRET" in st.secrets:
                key_dict = json.loads(st.secrets["FIREBASE_SECRET"])
                cred = credentials.Certificate(key_dict)
                firebase_admin.initialize_app(cred)
        except Exception: pass
    db = firestore.client()
    return db

db = init_firebase()
if 'db' not in st.session_state: st.session_state.db = db

# --- セッション初期化 ---
if 'page' not in st.session_state:
    st.session_state.update({
        'page': "login", 'logged_in': False, 'current_user': "", 'streak': 0,
        'learned_words': [], 'session_words': [], 'success_counts': {},
        'test_words': [], 'input_key': 0, 'user_grade': "中1"
    })

# --- ログイン・メニュー表示制御 ---
if not st.session_state.logged_in:
    st.title("🔐 ログイン")
    u_id = st.text_input("名前 (ID):")
    u_pw = st.text_input("パスワード:", type="password")
    
    if st.button("ログイン / 新規登録"):
        if u_id and u_pw:
            doc_ref = st.session_state.db.collection("users").document(u_id)
            doc = doc_ref.get()
            if doc.exists:
                if doc.to_dict().get('password') == u_pw:
                    data = doc.to_dict()
                    st.session_state.update({'current_user': u_id, 'logged_in': True, 'page': "main_menu",
                                             'streak': data.get('streak', 0), 'learned_words': data.get('learned', []),
                                             'user_grade': data.get('grade', "中1")})
                    st.rerun()
                else: st.error("パスワードが違います")
            else:
                doc_ref.set({"password": u_pw, "streak": 0, "learned": [], "grade": "中1"})
                st.session_state.update({'current_user': u_id, 'logged_in': True, 'page': "main_menu"})
                st.rerun()

elif st.session_state.page == "main_menu":
    st.header(f"🔥 {st.session_state.user_grade} コース")
    
    with st.expander("⚙️ 学年設定を変更する"):
        new_grade = st.selectbox("学年選択", ["中1", "中2", "中3"], 
                                 index=["中1", "中2", "中3"].index(st.session_state.user_grade))
        if st.button("変更を保存"):
            st.session_state.user_grade = new_grade
            st.session_state.db.collection("users").document(st.session_state.current_user).update({"grade": new_grade})
            st.rerun()

    if st.button("🚀 今日の練習をはじめる"):
        all_words = load_csv_data('words.csv')
        grade_words = [w for w in all_words if w['grade'] == st.session_state.user_grade]
        if not grade_words:
            st.error("その学年の単語データがCSVにありません！")
        else:
            st.session_state.session_words = random.sample(grade_words, min(3, len(grade_words)))
            st.session_state.success_counts = {w['a']: 0 for w in st.session_state.session_words}
            st.session_state.page = "training"
            st.rerun()

# --- 練習・テストロジック ---
elif st.session_state.page == "training":
    active = [w for w in st.session_state.session_words if st.session_state.success_counts.get(w['a'], 0) < 3]
    if not active:
        st.session_state.page = "test"
        st.rerun()
    
    target = active[0]
    st.subheader(f"「{target['q']}」 ({st.session_state.success_counts.get(target['a'], 0)+1}/3)")
    u_in = st.text_input("入力:", key=f"t_{st.session_state.input_key}")
    if st.button("判定"):
        if u_in.lower().strip() == target['a']:
            st.session_state.success_counts[target['a']] += 1
            st.session_state.input_key += 1
            st.rerun()
        else: st.error("間違い！")

elif st.session_state.page == "test":
    st.title("🎉 お疲れ様！")
    neta = load_csv_data('neta.csv')
    if neta:
        item = random.choice(neta)
        st.info(f"🎤 {item['name']}\n\n{item['story']}")
    if st.button("メニューへ戻る"):
        st.session_state.page = "main_menu"
        st.rerun()
