import streamlit as st
import random
import time
import json
import csv
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. ページ設定 ---
st.set_page_config(layout="centered", page_title="英単語マスター", page_icon="📝")

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

# --- 3. Firebase初期化 & ルール保存/読込 ---
def init_firebase_and_rules():
    if not firebase_admin._apps:
        try:
            if "FIREBASE_SECRET" in st.secrets:
                key_dict = json.loads(st.secrets["FIREBASE_SECRET"])
                cred = credentials.Certificate(key_dict)
                firebase_admin.initialize_app(cred)
        except Exception: pass
    
    db = firestore.client()
    if 'db' not in st.session_state:
        st.session_state.db = db

    # 【重要】お父様の指示をFirebaseに永続保存する
    rules_ref = db.collection("config").document("rules")
    my_rules = {
        "rule1": "コードを分ける時は、意味のあるパートごとに分ける。",
        "rule2": "ログイン画面は『前回のIDで始める』か『他ID』の二択ボタンから始める。",
        "rule3": "修正時は前のコードを全部消すので、常にフルセットでコードを書く。",
        "rule4": "復習テスト終了後、必ず芸人の名前とエピソードを表示する（result画面）。",
        "rule5": "復習テストは5問（今日3問＋過去ランダム2問）。初日は3問。",
        "rule6": "各問題に『つづりヘルプ（ヒント）』ボタンを設置する。"
    }
    # 初回または更新時にFirebaseへ書き込み
    rules_ref.set(my_rules, merge=True)
    st.session_state.app_rules = rules_ref.get().to_dict()

def init_session():
    init_firebase_and_rules()
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
    
    # URLから保存されたIDを取得
    url_id = st.query_params.get("id", "")
    
    # 指示：前回のIDがある場合、ボタン2つだけを表示（パスワード入力なし）
    if url_id and "force_manual" not in st.session_state:
        st.write(f"おかえりなさい！")
        if st.button(f"🚀 {url_id} で始める", use_container_width=True, type="primary"):
            doc = st.session_state.db.collection("users").document(url_id).get()
            if doc.exists:
                data = doc.to_dict()
                st.session_state.current_user = url_id
                st.session_state.streak = data.get('streak', 0)
                st.session_state.learned_words = data.get('learned', [])
                st.session_state.user_grade = data.get('grade', "中1")
                st.session_state.logged_in = True
                st.session_state.page = "main_menu"
                st.rerun()
            else:
                st.error("データが見つかりませんでした。")
                st.session_state.force_manual = True
                st.rerun()
        
        if st.button("👤 他のIDでログインする", use_container_width=True):
            st.session_state.force_manual = True
            st.rerun()
            
    else:
        # 手動ログイン画面
        u_id = st.text_input("なまえ (ID):").strip()
        u_pw = st.text_input("パスワード:", type="password").strip()
        u_grade = st.selectbox("がくねん:", ["中1", "中2", "中3", "高1", "高2", "高3"])
        
        if st.button("ログインして開始", use_container_width=True, type="primary"):
            if u_id and u_pw:
                doc_ref = st.session_state.db.collection("users").document(u_id)
                doc = doc_ref.get()
                valid = False
                if doc.exists:
                    if doc.to_dict()['password'] == u_pw:
                        data = doc.to_dict()
                        st.session_state.user_grade = data.get('grade', u_grade)
                        st.session_state.streak = data.get('streak', 0)
                        st.session_state.learned_words = data.get('learned', [])
                        valid = True
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
                    if "force_manual" in st.session_state: del st.session_state.force_manual
                    st.rerun()
    st.stop()

if st.session_state.page == "main_menu":
    st.header(f"🔥 {st.session_state.user_grade}コース")
    st.subheader(f"連続学習: {st.session_state.streak}日目")
    
    if st.button("🚀 今日の練習をはじめる", use_container_width=True):
        all_words = load_csv_data('words.csv')
        grade_words = [w for w in all_words if w['grade'] == st.session_state.user_grade]
        if not grade_words:
            st.error("単語データがありません。"); st.stop()
            
        unlearned = [w for w in grade_words if w['a'] not in st.session_state.learned_words]
        if len(unlearned) < 3: st.session_state.learned_words = []
        
        st.session_state.session_words = random.sample(unlearned if len(unlearned)>=3 else grade_words, 3)
        st.session_state.success_counts = {w['a']: 0 for w in st.session_state.session_words}
        st.session_state.page = "training"
        st.rerun()

elif st.session_state.page == "training":
    active = [w for w in st.session_state.session_words if st.session_state.success_counts.get(w['a'], 0) < 3]
    if not active:
        # --- 復習テスト作成：今日3問 + 過去ランダム2問 ---
        today_list = list(st.session_state.session_words)
        all_csv = load_csv_data('words.csv')
        past_learned = [w for w in all_csv if w['a'] in st.session_state.learned_words and w['a'] not in [tw['a'] for tw in today_list]]
        
        if not past_learned:
            st.session_state.test_words = today_list # 初日
        else:
            extra = random.sample(past_learned, min(2, len(past_learned)))
            st.session_state.test_words = today_list + extra
            
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
    if st.button("判定", type="primary", use_container_width=True):
        if u_in == st.session_state.target_wa:
            st.session_state.success_counts[st.session_state.target_wa] += 1
            st.session_state.input_key += 1; st.session_state.show_hint = False
            del st.session_state.target_wa; st.rerun()

elif st.session_state.page == "test":
    if not st.session_state.test_words:
        st.session_state.streak += 1
        st.session_state.db.collection("users").document(st.session_state.current_user).update({
            "streak": st.session_state.streak, "learned": st.session_state.learned_words
        })
        # 芸人ネタをFirebaseからではなくCSVから取得して表示
        n_data = load_csv_data('neta.csv')
        st.session_state.current_episode = random.choice(n_data) if n_data else {"name": "合格", "story": "完璧！"}
        st.session_state.page = "result"; st.rerun()

    word = st.session_state.test_words[0]
    st.subheader(f"テスト（全{len(st.session_state.test_words)}問）: 「{word['q']}」")
    if st.button("❓ つづりヘルプ"): st.session_state.show_hint = True
    if st.session_state.show_hint: st.info(f"正解: **{word['a']}**")

    t_in = st.text_input("答え:", key=f"v_{st.session_state.input_key}").strip().lower()
    if st.button("判定する", type="primary", use_container_width=True):
        if t_in == word['a']:
            if word['a'] not in st.session_state.learned_words: st.session_state.learned_words.append(word['a'])
            st.session_state.test_words.pop(0)
            st.session_state.input_key += 1; st.session_state.show_hint = False
            st.rerun()
        else:
            st.error("間違い！特訓開始！"); time.sleep(1)
            st.session_state.missed_word, st.session_state.missed_count = word, 0
            st.session_state.page = "miss_drill"; st.rerun()

elif st.session_state.page == "miss_drill":
    st.warning(f"🚨 特訓！「{st.session_state.missed_word['q']}」")
    d_in = st.text_input("スペル:", key=f"d_{st.session_state.input_key}").strip().lower()
    if d_in == st.session_state.missed_word['a']:
        st.session_state.missed_count += 1; st.session_state.input_key += 1
        if st.session_state.missed_count >= 5:
            st.session_state.page = "test"; st.session_state.missed_word = None; st.session_state.missed_count = 0
        st.rerun()

elif st.session_state.page == "result":
    st.balloons(); st.title("🎉 合格！")
    ep = st.session_state.current_episode
    st.subheader(f"🎤 {ep['name']}")
    st.info(ep['story'])
    
    # 最後に、Firebaseから読み込んだ「絶対ルール」をデバッグ表示（開発時確認用）
    with st.expander("📌 このアプリの絶対ルール（Firebase保存済み）"):
        for k, v in st.session_state.app_rules.items():
            st.write(f"・{v}")
            
    if st.button("メニューへ戻る", use_container_width=True):
        st.session_state.page = "main_menu"; st.rerun()

