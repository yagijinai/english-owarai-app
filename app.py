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

def init_session():
    defaults = {
        'page': 'login', 'user_id': None, 'grade': None, 
        'session_words': [], 'training_counts': {}, 
        'test_queue': [], 'test_idx': 0, 'wrong_target': None,
        'wrong_count': 0, 'input_key': 0, 'feedback': ""
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session()

def show_login():
    st.title("🔐 ログイン")
    u_id = st.text_input("ID")
    u_pw = st.text_input("PW", type="password")
    if st.button("ログイン"):
        doc = db.collection("users").document(u_id).get()
        if doc.exists and doc.to_dict().get('password') == u_pw:
            st.session_state.user_id = u_id
            st.session_state.page = 'grade_select'
            st.rerun()

def show_grade_select():
    st.title("🎓 学年を選んでください")
    if st.button("中1"): st.session_state.grade = "中1"; st.session_state.page = "menu"; st.rerun()
    if st.button("中2"): st.session_state.grade = "中2"; st.session_state.page = "menu"; st.rerun()
    if st.button("中3"): st.session_state.grade = "中3"; st.session_state.page = "menu"; st.rerun()

    def show_training():
    words = [w for w in load_data('words.csv') if w['grade'] == st.session_state.grade]
    
    # 練習用の単語がまだセットされていなければ初期化
    if not st.session_state.session_words:
        st.session_state.session_words = random.sample(words, min(3, len(words)))
        st.session_state.training_counts = {w['a']: 0 for w in st.session_state.session_words}

    # まだ3回終わっていない単語を探す
    target = next((w for w in st.session_state.session_words if st.session_state.training_counts[w['a']] < 3), None)
    
    if not target:
        # 練習終了、テストへ
        prev = random.sample(words, min(2, len(words)))
        st.session_state.test_queue = st.session_state.session_words + prev
        st.session_state.test_idx = 0
        st.session_state.page = 'test'
        st.rerun()

    st.subheader(f"練習: {target['q']} ({st.session_state.training_counts[target['a']]}/3)")
    if st.button("❓ ヒント"): st.info(f"正解: {target['a']}")
    
    u_in = st.text_input("入力:", key=f"t_{st.session_state.input_key}")
    if st.button("判定"):
        if u_in.lower().strip() == target['a']:
            st.session_state.training_counts[target['a']] += 1
            st.session_state.feedback = "✅ 正解！"
        else:
            st.session_state.feedback = "❌ 不正解..."
        st.session_state.input_key += 1
        st.rerun()
    st.write(st.session_state.feedback)

def show_test():
    if st.session_state.wrong_target:
        st.error(f"復習: {st.session_state.wrong_target['q']} をもう一度！")
        u_in = st.text_input("入力:", key=f"r_{st.session_state.input_key}")
        if st.button("判定"):
            if u_in.lower().strip() == st.session_state.wrong_target['a']:
                st.session_state.wrong_count += 1
                if st.session_state.wrong_count >= 3: st.session_state.wrong_target = None
            st.session_state.input_key += 1
            st.rerun()
        return

    target = st.session_state.test_queue[st.session_state.test_idx]
    st.subheader(f"テスト: {target['q']}")
    u_in = st.text_input("入力:", key=f"test_{st.session_state.input_key}")
    if st.button("判定"):
        if u_in.lower().strip() == target['a']:
            st.session_state.test_idx += 1
            if st.session_state.test_idx >= len(st.session_state.test_queue):
                st.success("全部クリア！"); st.session_state.page = "menu"
        else: st.session_state.wrong_target = target; st.session_state.wrong_count = 0
        st.session_state.input_key += 1
        st.rerun()

# 画面切り替え
if st.session_state.page == 'login': show_login()
elif st.session_state.page == 'grade_select': show_grade_select()
elif st.session_state.page == 'menu':
    if st.button("練習開始"): st.session_state.session_words = []; st.session_state.page = 'train'; st.rerun()
elif st.session_state.page == 'train': show_training()
elif st.session_state.page == 'test': show_test()
