import streamlit as st
import random
import json
import csv
import firebase_admin
from firebase_admin import credentials, firestore

st.set_page_config(layout="centered", page_title="英単語マスター", page_icon="📝")

# Firebase初期化
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

def load_data(filename):
    data = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 3:
                    data.append({"grade": row[0].strip(), "q": row[1].strip(), "a": row[2].strip().lower()})
    except: pass
    return data

# 状態管理の初期化
if 'page' not in st.session_state:
    st.session_state.update({
        'page': 'start', 'user_id': None, 'grade': None,
        'session_words': [], 'training_counts': {}, 'test_queue': [],
        'test_idx': 0, 'wrong_target': None, 'wrong_count': 0,
        'input_key': 0, 'feedback': ""
    })

def show_start():
    st.title("Welcome")
    if st.button("同じIDでつづける"): st.session_state.page = 'login'; st.rerun()
    if st.button("新しいIDではじめる"): st.session_state.page = 'login'; st.rerun()

def show_login():
    st.title("ログイン")
    u_id = st.text_input("ID")
    u_pw = st.text_input("PW", type="password")
    if st.button("OK"):
        st.session_state.user_id = u_id
        st.session_state.page = 'grade_select'
        st.rerun()

def show_grade_select():
    st.title("学年選択")
    if st.button("中1"): st.session_state.grade = "中1"; st.session_state.page = "menu"; st.rerun()
    if st.button("中2"): st.session_state.grade = "中2"; st.session_state.page = "menu"; st.rerun()


def show_menu():
    st.title("メニュー")
    if st.button("練習開始"):
        words = [w for w in load_data('words.csv') if w['grade'] == st.session_state.grade]
        st.session_state.session_words = random.sample(words, min(3, len(words)))
        st.session_state.training_counts = {w['a']: 0 for w in st.session_state.session_words}
        st.session_state.page = 'train'
        st.rerun()

def show_train():
    target = next((w for w in st.session_state.session_words if st.session_state.training_counts[w['a']] < 3), None)
    if not target:
        st.session_state.page = 'test'
        st.rerun()
    
    st.subheader(f"練習: {target['q']}")
    if st.button("ヒント"): st.info(f"正解: {target['a']}")
    
    u_in = st.text_input("入力:", key=f"t_{st.session_state.input_key}")
    if st.button("判定"):
        if u_in.lower().strip() == target['a']:
            st.session_state.training_counts[target['a']] += 1
            st.session_state.feedback = "✅"
        else: st.session_state.feedback = "❌"
        st.session_state.input_key += 1
        st.rerun()
    st.write(st.session_state.feedback)

def show_test():
    st.write("テスト画面（実装中）")
    if st.button("戻る"): st.session_state.page = "menu"; st.rerun()

# 画面切り替えのルーター
if st.session_state.page == 'start': show_start()
elif st.session_state.page == 'login': show_login()
elif st.session_state.page == 'grade_select': show_grade_select()
elif st.session_state.page == 'menu': show_menu()
elif st.session_state.page == 'train': show_train()
elif st.session_state.page == 'test': show_test()

