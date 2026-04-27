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

# セッション変数の初期化（網羅的定義）
def init_session():
    if 'page' not in st.session_state:
        st.session_state.update({
            'page': 'menu', 'grade': "中1", 'session_words': [],
            'training_counts': {}, 'test_queue': [], 'test_idx': 0,
            'wrong_target': None, 'wrong_retry_count': 0, 'input_key': 0,
            'hint_shown': False
        })
init_session()

def load_data(filename):
    data = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 3 and filename == 'words.csv':
                    data.append({"grade": row[0].strip(), "q": row[1].strip(), "a": row[2].strip().lower()})
                elif len(row) >= 2 and filename == 'neta.csv':
                    data.append({"title": row[0].strip(), "story": row[1].strip()})
    except: pass
    return data

def show_train():
    pending = [w for w in st.session_state.session_words if st.session_state.training_counts.get(w['a'], 0) < 3]
    if not pending:
        st.session_state.test_queue = list(st.session_state.session_words)
        st.session_state.test_idx = 0
        st.session_state.page = 'test'
        st.rerun()
    
    target = pending[0]
    st.subheader(f"練習: {target['q']}")
    
    # ヒント機能
    if st.button("ヒントを表示"):
        st.session_state.hint_shown = True
    if st.session_state.hint_shown:
        st.info(f"正解: {target['a']}")
        
    u_in = st.text_input("入力:", key=f"t_{st.session_state.input_key}")
    if st.button("判定"):
        if u_in.lower().strip() == target['a']:
            st.session_state.training_counts[target['a']] = st.session_state.training_counts.get(target['a'], 0) + 1
            st.session_state.hint_shown = False # 次の単語のためにリセット
        st.session_state.input_key += 1
        st.rerun()

def show_retry():
    target = st.session_state.wrong_target
    if not target:
        st.session_state.page = 'test'
        st.rerun()
        
    st.error(f"復習: {target['q']} を3回入力 ({st.session_state.wrong_retry_count}/3)")
    u_in = st.text_input("入力:", key=f"r_{st.session_state.input_key}")
    if st.button("回答"):
        if u_in.lower().strip() == target['a']:
            st.session_state.wrong_retry_count += 1
            if st.session_state.wrong_retry_count >= 3:
                st.session_state.wrong_target = None
                st.session_state.test_idx += 1 
                st.session_state.page = 'test'
        st.session_state.input_key += 1
        st.rerun()

def show_test():
    if st.session_state.test_idx >= len(st.session_state.test_queue):
        st.success("テストクリア！")
        neta_list = load_data('neta.csv')
        if neta_list:
            neta = random.choice(neta_list)
            st.info(f"🎁 ご褒美: {neta['title']}\n\n{neta['story']}")
        if st.button("メニューへ戻る"): 
            st.session_state.page = 'menu'
            st.rerun()
        return
    
    target = st.session_state.test_queue[st.session_state.test_idx]
    st.subheader(f"テスト: {target['q']}")
    u_in = st.text_input("回答:", key=f"test_{st.session_state.input_key}")
    if st.button("回答する"):
        if u_in.lower().strip() == target['a']:
            st.session_state.test_idx += 1
        else:
            st.session_state.wrong_target = target
            st.session_state.wrong_retry_count = 0
            st.session_state.page = 'retry'
        st.session_state.input_key += 1
        st.rerun()

# メインルーター
if st.session_state.page == 'menu':
    st.title("メニュー")
    if st.button("練習開始"):
        words = [w for w in load_data('words.csv') if w['grade'] == st.session_state.grade]
        if words:
            st.session_state.session_words = random.sample(words, min(3, len(words)))
            st.session_state.training_counts = {w['a']: 0 for w in st.session_state.session_words}
            st.session_state.hint_shown = False
            st.session_state.page = 'train'
            st.rerun()
        else:
            st.error("単語データが読み込めません。")
elif st.session_state.page == 'train': show_train()
elif st.session_state.page == 'retry': show_retry()
elif st.session_state.page == 'test': show_test()
