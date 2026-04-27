import streamlit as st
import random, json, csv
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

# セッション変数をここで全て初期化 (KeyError対策)
def init_session():
    if 'page' not in st.session_state:
        st.session_state.update({
            'page': 'start', 'logged_in': False, 'grade': None,
            'session_words': [], 'training_counts': {}, 'test_queue': [],
            'test_idx': 0, 'input_key': 0, 'feedback': "", 
            'hint_shown': False  # ヒント表示用変数を追加
        })

init_session()

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

def show_start():
    st.title("Welcome")
    if st.button("Googleでログイン"):
        st.session_state.logged_in = True
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
        st.session_state.hint_shown = False # 練習開始時にヒントフラグをリセット
        st.rerun()

def show_train():
    target = next((w for w in st.session_state.session_words if st.session_state.training_counts[w['a']] < 3), None)
    if not target:
        st.session_state.test_queue = list(st.session_state.session_words)
        st.session_state.test_idx = 0
        st.session_state.page = 'test'
        st.rerun()
    
    st.subheader(f"練習: {target['q']}")
    
    # ヒント機能
    if st.button("ヒント"):
        st.session_state.hint_shown = True
    if st.session_state.hint_shown:
        st.info(f"正解: {target['a']}")
    
    u_in = st.text_input("入力:", key=f"t_{st.session_state.input_key}")
    if st.button("判定"):
        if u_in.lower().strip() == target['a']:
            st.session_state.training_counts[target['a']] += 1
            st.session_state.feedback = "✅ 正解"
            st.session_state.hint_shown = False # 次の問題へ移るのでヒントを隠す
        else: 
            st.session_state.feedback = "❌ 不正解"
        st.session_state.input_key += 1
        st.rerun()
    st.write(st.session_state.feedback)

def show_test():
    if st.session_state.test_idx >= len(st.session_state.test_queue):
        st.success("全部クリア！"); st.session_state.page = "menu"; st.rerun()
    
    target = st.session_state.test_queue[st.session_state.test_idx]
    st.subheader(f"テスト: {target['q']}")
    u_in = st.text_input("回答:", key=f"test_{st.session_state.input_key}")
    if st.button("回答する"):
        if u_in.lower().strip() == target['a']:
            st.session_state.test_idx += 1
        else: st.error("不正解...")
        st.session_state.input_key += 1
        st.rerun()

# 画面切り替えルーター
if not st.session_state.logged_in: 
    show_start()
elif st.session_state.page == 'grade_select': 
    show_grade_select()
elif st.session_state.page == 'menu': 
    show_menu()
elif st.session_state.page == 'train': 
    show_train()
elif st.session_state.page == 'test': 
    show_test()
