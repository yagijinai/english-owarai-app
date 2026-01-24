import streamlit as st
import random
import time
import json
import csv
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. ページ設定 ---
st.set_page_config(layout="centered", page_title="英単語練習アプリ", page_icon="📝")

# --- 2. CSV読み込み ---
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

# --- 3. Firebase / セッション初期化 ---
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

if not st.session_state.logged_in:
    st.title("🔐 ログイン")
    
    # URLまたはクエリパラメータから前回のIDを取得
    last_id = st.query_params.get("id", "")
    
    if last_id and "manual_login" not in st.session_state:
        st.subheader(f"「{last_id}」さんですね？")
        st.write("このままスタートしますか？")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ はい、これで始める", use_container_width=True):
                doc = st.session_state.db.collection("users").document(last_id).get()
                if doc.exists:
                    data = doc.to_dict()
                    st.session_state.current_user = last_id
                    st.session_state.streak = data.get('streak', 0)
                    st.session_state.learned_words = data.get('learned', [])
                    st.session_state.user_grade = data.get('grade', "中1")
                    st.session_state.logged_in = True
                    st.session_state.page = "main_menu"
                    st.rerun()
        with c2:
            if st.button("👤 別のIDで入る", use_container_width=True):
                st.session_state.manual_login = True
                st.rerun()
    else:
        # 手動ログイン画面
        u_id = st.text_input("名前 (ID):", value=last_id).strip()
        u_pw = st.text_input("パスワード:", type="password").strip()
        u_grade = st.selectbox("学年:", ["中1", "中2", "中3", "高1", "高2", "高3"])
        
        if st.button("ログイン / 新規登録", use_container_width=True):
            if u_id and u_pw:
                doc_ref = st.session_state.db.collection("users").document(u_id)
                doc = doc_ref.get()
                valid = False
                if doc.exists:
                    if doc.to_dict()['password'] == u_pw:
                        data = doc.to_dict(); valid = True
                        st.session_state.user_grade = data.get('grade', u_grade)
                        st.session_state.streak = data.get('streak', 0)
                        st.session_state.learned_words = data.get('learned', [])
                    else: st.error("パスワードが違います")
                else:
                    now = datetime.now()
                    expiry = f"{now.year if now.month <= 3 else now.year + 1}-03-31"
                    doc_ref.set({"password": u_pw, "streak": 0, "learned": [], "grade": u_grade, "expiry": expiry})
                    st.session_state.user_grade = u_grade; valid = True
                
                if valid:
                    st.session_state.current_user = u_id
                    st.session_state.logged_in = True
                    st.session_state.page = "main_menu"
                    st.query_params["id"] = u_id
                    if "manual_login" in st.session_state: del st.session_state.manual_login
                    st.rerun()
    st.stop()

if st.session_state.page == "main_menu":
    st.header(f"🔥 {st.session_state.user_grade}コース")
    st.subheader(f"連続学習: {st.session_state.streak}日目")
    
    if st.button("🚀 今日の練習をはじめる", use_container_width=True):
        all_csv = load_csv_data('words.csv')
        grade_words = [w for w in all_csv if w['grade'] == st.session_state.user_grade]
        if not grade_words:
            st.error("単語データがありません。"); st.stop()
            
        unlearned = [w for w in grade_words if w['a'] not in st.session_state.learned_words]
        if len(unlearned) < 3: st.session_state.learned_words = []
        
        # 今日の3問を選出
        st.session_state.session_words = random.sample(unlearned if len(unlearned)>=3 else grade_words, 3)
        st.session_state.success_counts = {w['a']: 0 for w in st.session_state.session_words}
        st.session_state.page = "training"
        st.rerun()

elif st.session_state.page == "training":
    active = [w for w in st.session_state.session_words if st.session_state.success_counts[w['a']] < 3]
    if not active:
        # --- 復習テスト5問の作成ロジック ---
        today_words = list(st.session_state.session_words)
        # 昨日までの既習単語（今日の3問以外）
        past_learned = [w for w in load_csv_data('words.csv') if w['a'] in st.session_state.learned_words and w['a'] not in [tw['a'] for tw in today_words]]
        
        if not past_learned:
            # 初日：3問でテスト
            st.session_state.test_words = today_words
        else:
            # 2日目以降：今日の3問 + 過去からランダム2問
            extra = random.sample(past_learned, min(2, len(past_learned)))
            st.session_state.test_words = today_words + extra
            
        random.shuffle(st.session_state.test_words)
        st.session_state.page = "test"; st.rerun()

    if 'target_wa' not in st.session_state or st.session_state.target_wa not in [w['a'] for w in active]:
        target = random.choice(active)
        st.session_state.target_wq, st.session_state.target_wa = target['q'], target['a']
        st.session_state.show_hint = False

    st.subheader(f"「{st.session_state.target_wq}」 ({st.session_state.success_counts[st.session_state.target_wa] + 1}/3)")
    if st.button("❓ つづりヘルプ"): st.session_state.show_hint = True
    if st.session_state.show_hint: st.info(f"正解: **{st.session_state.target_wa}**")
    
    u_in = st.text_input("入力:", key=f"t_{st.session_state.input_key}").strip().lower()
    if st.button("判定", type="primary"):
        if u_in == st.session_state.target_wa:
            st.session_state.success_counts[st.session_state.target_wa] += 1
            st.session_state.input_key += 1; st.session_state.show_hint = False
            del st.session_state.target_wa; st.rerun()

elif st.session_state.page == "miss_drill":
    st.warning(f"🚨 特訓！「{st.session_state.missed_word['q']}」")
    d_in = st.text_input("スペル:", key=f"d_{st.session_state.input_key}").strip().lower()
    if d_in == st.session_state.missed_word['a']:
        st.session_state.missed_count += 1; st.session_state.input_key += 1
        if st.session_state.missed_count >= 5:
            st.session_state.page = "test"; st.session_state.missed_word = None; st.session_state.missed_count = 0
        st.rerun()

elif st.session_state.page == "test":
    if not st.session_state.test_words:
        st.session_state.streak += 1
        st.session_state.db.collection("users").document(st.session_state.current_user).update({
            "streak": st.session_state.streak, "learned": st.session_state.learned_words
        })
        n_data = load_csv_data('neta.csv')
        st.session_state.current_episode = random.choice(n_data) if n_data else {"name": "合格", "story": "よく頑張ったね！"}
        st.session_state.page = "result"; st.rerun()

    word = st.session_state.test_words[0]
    st.subheader(f"テスト: 「{word['q']}」 (残り {len(st.session_state.test_words)}問)")
    if st.button("❓ ヒント"): st.session_state.show_hint = True
    if st.session_state.show_hint: st.info(f"正解: **{word['a']}**")

    t_in = st.text_input("答え:", key=f"v_{st.session_state.input_key}").strip().lower()
    if st.button("判定する", type="primary"):
        if t_in == word['a']:
            if word['a'] not in st.session_state.learned_words: st.session_state.learned_words.append(word['a'])
            st.session_state.test_words.pop(0); st.session_state.input_key += 1; st.session_state.show_hint = False
            st.rerun()
        else:
            st.error("間違い！特訓だ！"); time.sleep(1)
            st.session_state.missed_word, st.session_state.missed_count = word, 0
            st.session_state.page = "miss_drill"; st.rerun()

elif st.session_state.page == "result":
    st.balloons(); st.title("🎉 合格！")
    ep = st.session_state.current_episode
    st.success(f"🎤 **{ep['name']}**"); st.write(ep['story'])
    if st.button("メニューへ戻る", use_container_width=True):
        st.session_state.page = "main_menu"; st.rerun()
