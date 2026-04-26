import streamlit as st
import random
import json
import csv
import firebase_admin
from firebase_admin import credentials, firestore

st.set_page_config(layout="centered", page_title="英単語マスター", page_icon="📝")

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

def init_firebase():
    if not firebase_admin._apps:
        try:
            if "FIREBASE_SECRET" in st.secrets:
                key_dict = json.loads(st.secrets["FIREBASE_SECRET"])
                cred = credentials.Certificate(key_dict)
                firebase_admin.initialize_app(cred)
        except Exception: pass
    return firestore.client()

db = init_firebase()
if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 'current_user': "", 'page': "login", 
        'session_words': [], 'learned_words': [], 'user_grade': "中1", 
        'show_hint': False, 'input_key': 0, 'test_queue': [], 'test_idx': 0,
        'correction_target': None, 'correction_count': 0
    })

def main():
    if not st.session_state.logged_in:
        show_login_page()
    else:
        if st.session_state.page == "main_menu":
            show_main_menu()
        elif st.session_state.page == "training":
            show_training()
        elif st.session_state.page == "test":
            show_test()

def show_login_page():
    # 簡易ログイン処理（前回のロジックを継承）
    st.title("🔐 ログイン")
    u_id = st.text_input("ID:")
    u_pw = st.text_input("PW:", type="password")
    if st.button("ログイン"):
        doc = db.collection("users").document(u_id).get()
        if doc.exists and doc.to_dict().get('password') == u_pw:
            data = doc.to_dict()
            st.session_state.update({'current_user': u_id, 'logged_in': True, 'page': "main_menu", 
                                     'user_grade': data.get('grade', "中1"), 'learned_words': data.get('learned', [])})
            st.rerun()

def show_main_menu():
    st.header(f"🔥 {st.session_state.user_grade} コース")
    if st.button("練習開始"):
        all_words = load_csv_data('words.csv')
        grade_words = [w for w in all_words if w['grade'] == st.session_state.user_grade]
        sample = random.sample(grade_words, min(3, len(grade_words)))
        st.session_state.update({'session_words': sample, 'page': "training", 
                                 'training_counts': {w['a']: 0 for w in sample}})
        st.rerun()

def show_training():
    # 練習：3回ずつ
    target = next((w for w in st.session_state.session_words if st.session_state.training_counts[w['a']] < 3), None)
    if not target:
        # テスト準備
        prev = random.sample(st.session_state.learned_words, min(2, len(st.session_state.learned_words)))
        st.session_state.test_queue = st.session_state.session_words + prev
        st.session_state.update({'page': "test", 'test_idx': 0})
        st.rerun()

    st.subheader(f"練習: {target['q']} ({st.session_state.training_counts[target['a']]}/3)")
    u_in = st.text_input("入力:", key=f"t_{st.session_state.input_key}")
    if st.button("判定"):
        if u_in.lower().strip() == target['a']:
            st.session_state.training_counts[target['a']] += 1
            st.session_state.input_key += 1
            st.rerun()

def show_test():
    if st.session_state.correction_target:
        st.error(f"復習: {st.session_state.correction_target['q']} をもう一度！")
        u_in = st.text_input("入力:", key="corr")
        if st.button("回答"):
            if u_in.lower().strip() == st.session_state.correction_target['a']:
                st.session_state.correction_count += 1
                if st.session_state.correction_count >= 3:
                    st.session_state.correction_target = None
                    st.rerun()
            else: st.error("間違い！")
        return

    if st.session_state.test_idx >= len(st.session_state.test_queue):
        st.success("完了！")
        if st.button("戻る"): st.session_state.page = "main_menu"; st.rerun()
        return

    target = st.session_state.test_queue[st.session_state.test_idx]
    st.subheader(f"テスト: {target['q']}")
    u_in = st.text_input("入力:", key="test_in")
    if st.button("判定"):
        if u_in.lower().strip() == target['a']:
            st.session_state.test_idx += 1
            st.rerun()
        else:
            st.session_state.correction_target = target
            st.session_state.correction_count = 0
            st.rerun()
