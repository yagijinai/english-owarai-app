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

if 'init' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 'current_user': "", 'page': "login",
        'session_words': [], 'learned_words': [], 'user_grade': "中1",
        'training_counts': {}, 'test_queue': [], 'test_idx': 0,
        'wrong_target': None, 'wrong_count': 0, 'input_key': 0,
        'feedback': "" # 判定結果を表示するための場所を追加
    })
    st.session_state.init = True

def main():
    if not st.session_state.logged_in:
        show_login()
    else:
        if st.session_state.page == "main": show_main()
        elif st.session_state.page == "train": show_train()
        elif st.session_state.page == "test": show_test()

def show_login():
    st.title("🔐 ログイン")
    u_id = st.text_input("ID:")
    u_pw = st.text_input("PW:", type="password")
    if st.button("ログイン"):
        doc = db.collection("users").document(u_id).get()
        if doc.exists and doc.to_dict().get('password') == u_pw:
            data = doc.to_dict()
            st.session_state.update({'current_user': u_id, 'logged_in': True, 'page': "main",
                                     'user_grade': data.get('grade', "中1"), 'learned_words': data.get('learned', [])})
            st.rerun()

def show_main():
    st.header(f"🔥 {st.session_state.user_grade} コース")
    if st.button("🚀 練習開始"):
        words = [w for w in load_csv_data('words.csv') if w['grade'] == st.session_state.user_grade]
        sample = random.sample(words, min(3, len(words)))
        st.session_state.update({
            'session_words': sample, 
            'training_counts': {w['a']: 0 for w in sample}, 
            'page': "train",
            'feedback': ""
        })
        st.rerun()

def show_train():
    target = next((w for w in st.session_state.session_words if st.session_state.training_counts[w['a']] < 3), None)
    if not target:
        prev = random.sample(st.session_state.learned_words, min(2, len(st.session_state.learned_words)))
        st.session_state.update({'test_queue': st.session_state.session_words + prev, 'test_idx': 0, 'page': "test", 'feedback': ""})
        st.rerun()
        
    st.subheader(f"練習: {target['q']} ({st.session_state.training_counts[target['a']]}/3)")
    st.write(st.session_state.feedback) # 判定結果を表示
    
    u_in = st.text_input("入力:", key=f"t_{st.session_state.input_key}")
    if st.button("判定"):
        if u_in.lower().strip() == target['a']:
            st.session_state.training_counts[target['a']] += 1
            st.session_state.feedback = "✅ 正解！"
        else:
            st.session_state.feedback = "❌ 不正解...もう一度！"
        
        st.session_state.input_key += 1
        st.rerun()

def show_test():
    # テストロジックは以前の通り維持
    if st.session_state.wrong_target:
        st.error(f"復習: {st.session_state.wrong_target['q']} をもう一度！")
        u_in = st.text_input("入力:", key=f"r_{st.session_state.input_key}")
        if st.button("判定"):
            if u_in.lower().strip() == st.session_state.wrong_target['a']:
                st.session_state.wrong_count += 1
                if st.session_state.wrong_count >= 3: st.session_state.update({'wrong_target': None, 'wrong_count': 0})
            st.session_state.input_key += 1
            st.rerun()
        return
    # (テストの続きの処理も同様の構成)
    if st.session_state.test_idx >= len(st.session_state.test_queue):
        st.success("全部クリア！")
        if st.button("戻る"): st.session_state.page = "main"; st.rerun()
        return
    target = st.session_state.test_queue[st.session_state.test_idx]
    st.subheader(f"テスト: {target['q']}")
    u_in = st.text_input("入力:", key=f"test_{st.session_state.input_key}")
    if st.button("判定"):
        if u_in.lower().strip() == target['a']: st.session_state.test_idx += 1
        else: st.session_state.update({'wrong_target': target, 'wrong_count': 0})
        st.session_state.input_key += 1
        st.rerun()

if __name__ == "__main__":
    main()
