import streamlit as st
import random
import time
import json
import csv
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. ページ設定（スマホ最適化） ---
st.set_page_config(layout="centered", page_title="英単語マスター", page_icon="📝")

# --- 2. データ読み込み ---
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

# --- 3. Firebase初期化 ---
def init_firebase():
    if not firebase_admin._apps:
        try:
            if "FIREBASE_SECRET" in st.secrets:
                key_dict = json.loads(st.secrets["FIREBASE_SECRET"])
                cred = credentials.Certificate(key_dict)
                firebase_admin.initialize_app(cred)
        except Exception: pass
    if 'db' not in st.session_state:
        st.session_state.db = firestore.client()

def init_session():
    init_firebase()
    defaults = {
        'logged_in': False, 'page': "login", 'current_user': "",
        'streak': 0, 'learned_words': [], 'session_words': [], 'success_counts': {},
        'test_words': [], 'input_key': 0, 'missed_word': None, 'missed_count': 0,
        'current_episode': None, 'user_grade': "中1", 'show_hint': False
    }
    for key, val in defaults.items():
        if key not in st.session_state: st.session_state[key] = val

init_session()

# --- 重要：URLからの自動ログイン判定 ---
if not st.session_state.logged_in and "id" in st.query_params:
    uid = st.query_params["id"]
    doc = st.session_state.db.collection("users").document(uid).get()
    if doc.exists:
        data = doc.to_dict()
        st.session_state.current_user = uid
        st.session_state.streak = data.get('streak', 0)
        st.session_state.learned_words = data.get('learned', [])
        st.session_state.user_grade = data.get('grade', "中1")
        st.session_state.logged_in = True
        st.session_state.page = "main_menu"

if not st.session_state.logged_in:
    st.title("🔑 ログイン")
    
    tab1, tab2 = st.tabs(["ログイン", "Pixel設定ガイド"])
    
    with tab1:
        u_id = st.text_input("名前 (ID):").strip()
        u_pw = st.text_input("パスワード:", type="password").strip()
        u_grade = st.selectbox("学年を選んでね:", ["中1", "中2", "中3", "高1", "高2", "高3"])
        
        if st.button("ログインして専用URLを発行", use_container_width=True):
            if u_id and u_pw:
                doc_ref = st.session_state.db.collection("users").document(u_id)
                doc = doc_ref.get()
                
                if doc.exists:
                    if doc.to_dict()['password'] == u_pw:
                        st.query_params["id"] = u_id
                        st.rerun()
                    else: st.error("パスワードが違います")
                else:
                    now = datetime.now()
                    expiry = f"{now.year if now.month <= 3 else now.year + 1}-03-31"
                    doc_ref.set({"password": u_pw, "streak": 0, "learned": [], "grade": u_grade, "expiry": expiry})
                    st.query_params["id"] = u_id
                    st.rerun()

    with tab2:
        st.info("💡 **Pixelで自動ログインする方法**")
        st.write("1. ログイン後、URLに自分のIDが入った状態にします。")
        st.write("2. Chromeの右上『︙』をタップ。")
        st.write("3. 『ホーム画面に追加』を選択。")
        st.write("4. 以降、そのアイコンから開くだけで自動ログインされます。")
    st.stop()

if st.session_state.page == "main_menu":
    st.title(f"🔥 {st.session_state.user_grade}")
    st.metric(label="連続学習", value=f"{st.session_state.streak} 日")
    st.write(f"👤 ユーザー: {st.session_state.current_user}")
    
    st.divider()

    if st.button("🚀 今日の練習をはじめる", use_container_width=True):
        all_words = load_csv_data('words.csv')
        grade_words = [w for w in all_words if w['grade'] == st.session_state.user_grade]
        if not grade_words:
            st.error("単語データが見つかりません。")
            st.stop()
            
        unlearned = [w for w in grade_words if w['a'] not in st.session_state.learned_words]
        if len(unlearned) < 3: st.session_state.learned_words = []
        
        st.session_state.session_words = random.sample(unlearned if len(unlearned)>=3 else grade_words, 3)
        st.session_state.success_counts = {w['a']: 0 for w in st.session_state.session_words}
        st.session_state.page = "training"
        st.rerun()

    if st.button("別のIDで入る (ログアウト)", variant="secondary"):
        st.query_params.clear()
        st.session_state.logged_in = False
        st.rerun()

elif st.session_state.page == "training":
    active = [w for w in st.session_state.session_words if st.session_state.success_counts[w['a']] < 3]
    if not active:
        st.session_state.test_words = list(st.session_state.session_words)
        random.shuffle(st.session_state.test_words)
        st.session_state.page = "test"
        st.rerun()

    if 'target_wa' not in st.session_state or st.session_state.target_wa not in [w['a'] for w in active]:
        target = random.choice(active)
        st.session_state.target_wq, st.session_state.target_wa = target['q'], target['a']
        st.session_state.show_hint = False

    st.subheader(f"「{st.session_state.target_wq}」 ({st.session_state.success_counts[st.session_state.target_wa] + 1}/3)")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("❓ ヒント", use_container_width=True): st.session_state.show_hint = True
    with col2:
        if st.button("判定", type="primary", use_container_width=True):
            # 判定ロジックは下のtext_inputの後に
            pass 

    if st.session_state.show_hint:
        st.info(f"正解: **{st.session_state.target_wa}**")

    u_in = st.text_input("スペル入力:", key=f"t_{st.session_state.input_key}").strip().lower()
    if u_in == st.session_state.target_wa:
        st.session_state.success_counts[st.session_state.target_wa] += 1
        st.session_state.input_key += 1
        st.session_state.show_hint = False
        del st.session_state.target_wa
        st.rerun()

elif st.session_state.page == "miss_drill":
    st.warning(f"🚨 特訓！「{st.session_state.missed_word['q']}」")
    st.write(f"あと {5 - st.session_state.missed_count} 回書こう！")
    d_in = st.text_input("スペル:", key=f"d_{st.session_state.input_key}").strip().lower()
    if d_in == st.session_state.missed_word['a']:
        st.session_state.missed_count += 1
        st.session_state.input_key += 1
        if st.session_state.missed_count >= 5:
            st.session_state.page = "test"
            st.session_state.missed_word = None
            st.session_state.missed_count = 0
        st.rerun()

elif st.session_state.page == "test":
    if not st.session_state.test_words:
        st.session_state.streak += 1
        st.session_state.db.collection("users").document(st.session_state.current_user).update({
            "streak": st.session_state.streak, "learned": st.session_state.learned_words
        })
        episodes = load_csv_data('neta.csv')
        st.session_state.current_episode = random.choice(episodes) if episodes else {"name": "合格", "story": "おめでとう！"}
        st.session_state.page = "result"
        st.rerun()

    word = st.session_state.test_words[0]
    st.subheader(f"最終テスト: 「{word['q']}」")
    t_in = st.text_input("答え:", key=f"v_{st.session_state.input_key}").strip().lower()
    if st.button("判定する", type="primary", use_container_width=True):
        if t_in == word['a']:
            if word['a'] not in st.session_state.learned_words:
                st.session_state.learned_words.append(word['a'])
            st.session_state.test_words.pop(0)
            st.session_state.input_key += 1
            st.rerun()
        else:
            st.error("間違い！特訓開始！")
            time.sleep(1)
            st.session_state.missed_word, st.session_state.missed_count = word, 0
            st.session_state.page = "miss_drill"
            st.rerun()

elif st.session_state.page == "result":
    st.balloons()
    st.title("㊗️ 合格！")
    ep = st.session_state.current_episode
    st.success(f"🎤 **{ep['name']}**")
    st.write(ep['story'])
    if st.button("メニューへ戻る", use_container_width=True):
        st.session_state.page = "main_menu"
        st.rerun()
