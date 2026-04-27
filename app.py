import streamlit as st
import random, json, csv
import firebase_admin
from firebase_admin import credentials, firestore, auth

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

# アカウント統合・データ引き継ぎ用関数
def migrate_data(old_id, new_google_uid):
    old_ref = db.collection("users").document(old_id)
    old_doc = old_ref.get()
    if old_doc.exists:
        data = old_doc.to_dict()
        # Streak等のデータを新しいGoogle UIDのドキュメントへコピー
        db.collection("users").document(new_google_uid).set(data)
        # 移行完了フラグ
        return True
    return False

if 'page' not in st.session_state:
    st.session_state.update({
        'page': 'start', 'user_id': None, 'google_uid': None,
        'logged_in': False, 'streak': 0, 'feedback': ""
    })

def show_start():
    st.title("ログイン")
    # ここにFirebase Authのフロントエンドコンポーネントを配置
    # 今回は簡略化のため、Googleログイン成功をシミュレート
    if st.button("Googleでログイン"):
        # 実際にはここでFirebase AuthのIDトークンを取得
        fake_uid = "google_user_12345" 
        st.session_state.google_uid = fake_uid
        st.session_state.logged_in = True
        
        # データが既に存在するか確認
        if not db.collection("users").document(fake_uid).get().exists:
            st.session_state.page = 'migrate'
        else:
            st.session_state.page = 'grade_select'
        st.rerun()

def show_migrate():
    st.subheader("アカウント引き継ぎ")
    old_id = st.text_input("以前使っていたIDを入力して引き継ぐ")
    if st.button("データ引き継ぎ"):
        if migrate_data(old_id, st.session_state.google_uid):
            st.success("引き継ぎ完了！")
            st.session_state.page = 'grade_select'
            st.rerun()
        else:
            st.error("IDが見つかりません")

def show_grade_select():
    st.title("学年選択")
    if st.button("中1"): st.session_state.grade = "中1"; st.session_state.page = "menu"; st.rerun()
    if st.button("中2"): st.session_state.grade = "中2"; st.session_state.page = "menu"; st.rerun()

def show_menu():
    st.title("メニュー")
    # streakの表示
    st.write(f"現在の学習継続日数: {st.session_state.streak}日")
    if st.button("ログアウト"):
        st.session_state.logged_in = False
        st.session_state.page = 'start'
        st.rerun()

# 画面切り替えルーター
if not st.session_state.logged_in: show_start()
elif st.session_state.page == 'migrate': show_migrate()
elif st.session_state.page == 'grade_select': show_grade_select()
elif st.session_state.page == 'menu': show_menu()
