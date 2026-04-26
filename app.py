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
    st.session_state.update({'logged_in': False, 'current_user': "", 'page': "login", 
                             'session_words': [], 'user_grade': "中1", 'show_hint': False})

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

def inject_remember_me():
    st.components.v1.html("""<script>
        const saved = localStorage.getItem('last_user_id');
        if(saved && !window.location.href.includes('auto_login=')) {
            window.location.href = window.location.href + (window.location.href.includes('?') ? '&' : '?') + 'auto_login=' + saved;
        }
    </script>""", height=0)

def show_login_page():
    inject_remember_me()
    query = st.query_params
    auto_user = query.get("auto_login")
    if auto_user:
        doc = db.collection("users").document(auto_user).get()
        if doc.exists:
            st.session_state.update({'current_user': auto_user, 'logged_in': True, 'page': "main_menu", 
                                     'user_grade': doc.to_dict().get('grade', "中1")})
            st.rerun()
    
    st.title("🔐 ログイン")
    u_id = st.text_input("名前 (ID):")
    u_pw = st.text_input("パスワード:", type="password")
    if st.button("ログイン"):
        doc_ref = db.collection("users").document(u_id)
        doc = doc_ref.get()
        if doc.exists and doc.to_dict().get('password') == u_pw:
            st.components.v1.html(f"<script>localStorage.setItem('last_user_id', '{u_id}');</script>", height=0)
            st.session_state.update({'current_user': u_id, 'logged_in': True, 'page': "main_menu", 'user_grade': doc.to_dict().get('grade', "中1")})
            st.rerun()
        else: st.error("ログイン失敗")

def show_main_menu():
    st.header(f"🔥 {st.session_state.user_grade} コース")
    if st.button("ログアウト"):
        st.components.v1.html("<script>localStorage.removeItem('last_user_id'); window.location.reload();</script>", height=0)
    
    with st.expander("⚙️ 学年設定を変更"):
        new_grade = st.selectbox("学年", ["中1", "中2", "中3"], index=["中1", "中2", "中3"].index(st.session_state.user_grade))
        if st.button("保存"):
            st.session_state.user_grade = new_grade
            db.collection("users").document(st.session_state.current_user).update({"grade": new_grade})
            st.rerun()
    
    if st.button("🚀 練習開始"):
        all_words = load_csv_data('words.csv')
        grade_words = [w for w in all_words if w['grade'] == st.session_state.user_grade]
        st.session_state.update({'session_words': random.sample(grade_words, min(3, len(grade_words))), 
                                 'success_counts': {w['a']: 0 for w in random.sample(grade_words, min(3, len(grade_words)))}, 
                                 'page': "training", 'show_hint': False})
        st.rerun()

def show_training():
    active = [w for w in st.session_state.session_words if st.session_state.success_counts.get(w['a'], 0) < 3]
    if not active:
        st.session_state.page = "test"
        st.rerun()
    target = active[0]
    st.subheader(f"「{target['q']}」 ({st.session_state.success_counts.get(target['a'], 0)+1}/3)")
    
    if st.button("❓ ヒント"):
        st.session_state.show_hint = True
        st.rerun()
    if st.session_state.show_hint: st.info(f"正解: {target['a']}")
    
    u_in = st.text_input("入力:", key="u_input")
    if st.button("判定"):
        if u_in.lower().strip() == target['a']:
            st.session_state.success_counts[target['a']] += 1
            st.session_state.show_hint = False
            st.rerun()
        else: st.error("間違い！")

def show_test():
    st.title("🎉 お疲れ様！")
    neta = load_csv_data('neta.csv')
    if neta: st.info(random.choice(neta)['story'])
    if st.button("メニューへ戻る"):
        st.session_state.page = "main_menu"
        st.rerun()

main()
