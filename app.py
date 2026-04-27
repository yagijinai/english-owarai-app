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

# セッション変数の初期化（重要）
def init_session():
    if 'page' not in st.session_state:
        st.session_state.update({
            'page': 'start', 'logged_in': False, 'grade': None,
            'session_words': [], 'training_counts': {}, 'test_queue': [],
            'test_idx': 0, 'input_key': 0, 'feedback': "", 'hint_shown': False
        })

init_session()

def load_data(filename):
    data = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if filename == 'words.csv' and len(row) >= 3:
                    data.append({"grade": row[0].strip(), "q": row[1].strip(), "a": row[2].strip().lower()})
                elif filename == 'neta.csv' and len(row) >= 2:
                    data.append({"title": row[0].strip(), "story": row[1].strip()})
    except: pass
    return data

def show_train():
    # まだ練習回数が足りない単語を抽出
    pending = [w for w in st.session_state.session_words if st.session_state.training_counts[w['a']] < 3]
    
    if not pending:
        # 練習完了ならテストへ移動
        st.session_state.test_queue = list(st.session_state.session_words)
        st.session_state.test_idx = 0
        st.session_state.page = 'test'
        st.rerun()
    
    target = pending[0]
    st.subheader(f"練習: {target['q']}")
    
    if st.button("ヒント"): st.session_state.hint_shown = True
    if st.session_state.hint_shown: st.info(f"正解: {target['a']}")
    
    u_in = st.text_input("入力:", key=f"t_{st.session_state.input_key}")
    if st.button("判定"):
        if u_in.lower().strip() == target['a']:
            st.session_state.training_counts[target['a']] += 1
            st.session_state.hint_shown = False
            st.session_state.feedback = "✅ 正解！"
        else: 
            st.session_state.feedback = "❌ 不正解"
        st.session_state.input_key += 1
        st.rerun()
    st.write(st.session_state.feedback)

def show_test():
    # 全問終了チェック
    if st.session_state.test_idx >= len(st.session_state.test_queue):
        st.success("テスト終了！")
        neta_list = load_data('neta.csv')
        if neta_list:
            neta = random.choice(neta_list)
            st.subheader(f"🎁 ご褒美: {neta['title']}")
            st.info(neta['story'])
        if st.button("メニューへ戻る"): st.session_state.page = "menu"; st.rerun()
        return
    
    target = st.session_state.test_queue[st.session_state.test_idx]
    st.subheader(f"テスト: {target['q']}")
    u_in = st.text_input("回答:", key=f"test_{st.session_state.input_key}")
    if st.button("回答する"):
        if u_in.lower().strip() == target['a']:
            st.session_state.test_idx += 1
            st.session_state.input_key += 1
            st.rerun()
        else: st.error("不正解...")

# 画面切り替えルーター
if not st.session_state.logged_in: 
    st.title("Welcome"); 
    if st.button("Googleでログイン"): st.session_state.update(logged_in=True, page='menu'); st.rerun()
elif st.session_state.page == 'menu':
    st.title("メニュー")
    if st.button("練習開始"):
        words = [w for w in load_data('words.csv') if w['grade'] == "中1"]
        if words:
            st.session_state.session_words = random.sample(words, min(3, len(words)))
            st.session_state.training_counts = {w['a']: 0 for w in st.session_state.session_words}
            st.session_state.page = 'train'
            st.rerun()
elif st.session_state.page == 'train': show_train()
elif st.session_state.page == 'test': show_test()
