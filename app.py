import streamlit as st
import pandas as pd
import datetime
import random
import requests
import json
import streamlit.components.v1 as components
import hashlib

# --- 1. Firebase・基本設定 ---
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyB0Bd8aBmos2fHiD7XgH_S4yM5b__FHypI",
    "authDomain": "english-ap.firebaseapp.com",
    "projectId": "english-ap",
    "storageBucket": "english-ap.firebasestorage.app",
    "messagingSenderId": "167152900538",
    "appId": "1:167152900538:web:07a87314d3121c23eca583",
    "measurementId": "G-PEH3BVTK4H"
}

FIRESTORE_URL = "https://firestore.googleapis.com/v1/projects/" + FIREBASE_CONFIG['projectId'] + "/databases/(default)/documents/users"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_id(name, password):
    combined = str(name) + "_" + hash_password(password)
    return combined[:50]

# --- 2. 便利機能 ---
def text_to_speech(text):
    clean = str(text).replace("'", "")
    js = "<script>var m=new SpeechSynthesisUtterance();m.text='" + clean + "';m.lang='en-US';window.speechSynthesis.speak(m);</script>"
    components.html(js, height=0)

def set_local_storage(u_id, u_name):
    js = "<script>localStorage.setItem('eng_app_userid','" + str(u_id) + "');localStorage.setItem('eng_app_name','" + str(u_name) + "');</script>"
    components.html(js, height=0)

@st.cache_data
def load_data():
    try:
        w = pd.read_csv('words.csv')
        n = pd.read_csv('neta.csv')
        w['id'] = w['word'].astype(str) + "_" + w['meaning'].astype(str)
        return w, n
    except Exception as e:
        st.error("CSVファイルの読み込みエラー。ファイルを確認してください。")
        st.stop()

WORDS_DF, NETA_DF = load_data()

# --- 3. Firestore連携 ---
def get_user_data(u_id):
    url = FIRESTORE_URL + "/" + str(u_id)
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            f = r.json().get("fields", {})
            return {
                "display_name": f.get("display_name", {}).get("stringValue", ""),
                "streak": int(f.get("streak", {}).get("integerValue", 0)),
                "last_clear": f.get("last_clear", {}).get("stringValue", ""),
                "learned_ids": [v.get("stringValue") for v in f.get("learned_ids", {}).get("arrayValue", {}).get("values", [])]
            }
    except: pass
    return None

def save_user_data(u_id, name, streak, last, l_ids):
    url = FIRESTORE_URL + "/" + str(u_id)
    data = {
        "fields": {
            "display_name": {"stringValue": str(name)},
            "streak": {"integerValue": int(streak)},
            "last_clear": {"stringValue": str(last)},
            "learned_ids": {"arrayValue": {"values": [{"stringValue": str(i)} for i in l_ids]}}
        }
    }
    requests.patch(url, params={"updateMask.fieldPaths": ["display_name", "streak", "last_clear", "learned_ids"]}, json=data)

# --- 4. 画面制御 ---
st.set_page_config(page_title="お笑い英語マスター Pro", page_icon="📝")

# セッション変数の確実な初期化
keys = ["user_id", "user_name", "streak", "last_clear", "learned_ids", "phase", "idx", "p_list", "r_list", "neta", "wrong_id", "show_hint"]
for k in keys:
    if k not in st.session_state:
        if k == "phase": st.session_state[k] = "login"
        elif k in ["learned_ids", "p_list", "r_list"]: st.session_state[k] = []
        elif k in ["streak", "idx"]: st.session_state[k] = 0
        elif k == "show_hint": st.session_state[k] = False
        else: st.session_state[k] = None

# --- 5. ログイン画面 ---
if st.session_state.user_id is None:
    st.title("English Master Pro")
    
    # localStorageから自動ログイン情報を取得するJS
    if "check_js" not in st.session_state:
        components.html("""<script>
            var id=localStorage.getItem('eng_app_userid');
            var nm=localStorage.getItem('eng_app_name');
            if(id && nm && !window.location.hash.includes('id=')){
                parent.window.location.hash = 'id='+id+'&nm='+encodeURIComponent(nm);
            }
            </script>""", height=0)
        st.session_state.check_js = True

    q = st.query_params
    # 自動ログイン情報がある場合
    if "id" in q and "nm" in q:
        u_id, u_name = q["id"], q["nm"]
        st.success("おかえりなさい、 " + str(u_name) + " さん！")
        
        # ご要望の「二択」ボタン
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔥 続きから勉強をはじめる", use_container_width=True):
                d = get_user_data(u_id)
                if d:
                    st.session_state.user_id, st.session_state.user_name = u_id, u_name
                    st.session_state.streak, st.session_state.last_clear = d["streak"], d["last_clear"]
                    st.session_state.learned_ids = d["learned_ids"]
                    st.session_state.phase = "init"
                    st.rerun()
        with col2:
            if st.button("👤 他の名前でログイン", use_container_width=True):
                st.query_params.clear()
                components.html("<script>localStorage.clear();</script>", height=0)
                st.session_state.clear()
                st.rerun()
    # 手動ログイン
    else:
        n_in = st.text_input("なまえ").strip()
        p_in = st.text_input("パスワード", type="password")
        if st.button("🚀 ログイン / 新規登録", use_container_width=True):
            if n_in and p_in:
                u_id = get_user_id(n_in, p_in)
                d = get_user_data(u_id)
                if not d:
                    save_user_data(u_id, n_in, 0, "", [])
                    d = {"display_name": n_in, "streak": 0, "last_clear": "", "learned_ids": []}
                st.session_state.user_id, st.session_state.user_name = u_id, n_in
                st.session_state.streak, st.session_state.last_clear = d["streak"], d["last_clear"]
                st.session_state.learned_ids = d["learned_ids"]
                set_local_storage(u_id, n_in)
                st.query_params["id"], st.query_params["nm"] = u_id, n_in
                st.session_state.phase = "init"
                st.rerun()
    st.stop()

# --- 6. データ初期化フェーズ ---
if st.session_state.phase == "init":
    today = str(datetime.date.today())
    yst = str(datetime.date.today() - datetime.timedelta(days=1))
    if st.session_state.last_clear != yst and st.session_state.last_clear != today:
        st.session_state.streak = 0
    
    random.seed(int(today.replace("-", "")))
    pool = WORDS_DF[WORDS_DF['grade'] == 1].copy() if 'grade' in WORDS_DF.columns else WORDS_DF.copy()
    unlearned = pool[~pool['id'].isin(st.session_state.learned_ids)]
    target = unlearned if len(unlearned) >= 3 else pool
    
    st.session_state.p_list = target.sample(n=min(3, len(target))).to_dict('records')
    st.session_state.r_list = WORDS_DF.sample(n=min(3, len(WORDS_DF))).to_dict('records')
    st.session_state.neta = NETA_DF.sample(n=1).iloc[0]
    st.session_state.idx = 0
    st.session_state.phase = "practice"
    st.rerun()

# --- 7. メインコンテンツ ---
st.sidebar.write("👤 " + str(st.session_state.user_name) + " | 🔥 " + str(st.session_state.streak) + " 日目")

# 練習画面
if st.session_state.phase == "practice":
    idx = st.session_state.idx
    word = st.session_state.p_list[idx]
    st.subheader("Step 1: 練習 (" + str(idx+1) + "/3)")
    st.markdown("<h1 style='color:#FF4B4B; text-align:center;'>" + str(word['meaning']) + "</h1>", unsafe_allow_html=True)
    
    # ご要望の「お手本音声」と「見本表示」ボタン
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔊 お手本を聞く", use_container_width=True): text_to_speech(word['word'])
    with c2:
        if st.button("👀 英単語を表示", use_container_width=True):
            st.session_state.show_hint = not st.session_state.show_hint
    
    if st.session_state.show_hint:
        st.info("答えの見本: **" + str(word['word']) + "**")
    
    a1 = st.text_input("1回目", key="a1_" + str(idx)).strip().lower()
    a2 = st.text_input("2回目", key="a2_" + str(idx)).strip().lower()
    a3 = st.text_input("3回目", key="a3_" + str(idx)).strip().lower()
    
    correct = str(word['word']).lower()
    if a1 == correct and a2 == correct and a3 == correct:
        if st.button("正解！次へ進む", use_container_width=True):
            if word['id'] not in st.session_state.learned_ids: st.session_state.learned_ids.append(word['id'])
            st.session_state.idx += 1
            st.session_state.show_hint = False
            if st.session_state.idx >= 3:
                st.session_state.idx = 0
                st.session_state.phase = "test"
            st.rerun()

# 復習テスト画面
elif st.session_state.phase == "test":
    idx = st.session_state.idx
    word = st.session_state.r_list[idx]
    st.subheader("Step 2: 復習テスト (" + str(idx+1) + "/3)")
    st.markdown("<h1 style='color:#FF4B4B; text-align:center;'>" + str(word['meaning']) + "</h1>", unsafe_allow_html=True)

    if st.session_state.wrong_id == word['id']:
        st.error("特訓：正解は「" + str(word['word']) + "」です。5回書いて覚えよう！")
        t_ans = [st.text_input("特訓 " + str(i+1), key="t" + str(idx) + str(i)).strip().lower() for i in range(5)]
        if all(a == str(word['word']).lower() and a != "" for a in t_ans):
            if st.button("特訓クリア！次へ"):
                st.session_state.wrong_id = None
                st.session_state.idx += 1
                if st.session_state.idx >= 3: st.session_state.phase = "goal"
                st.rerun()
    else:
        with st.form(key="test_form"):
            u_in = st.text_input("英語で何という？").strip().lower()
            if st.form_submit_button("判定"):
                if u_in == str(word['word']).lower():
                    st.session_state.idx += 1
                    if st.session_state.idx >= 3:
                        td = str(datetime.date.today())
                        if st.session_state.last_clear != td:
                            st.session_state.streak += 1
                            st.session_state.last_clear = td
                        save_user_data(st.session_state.user_id, st.session_state.user_name, st.session_state.streak, st.session_state.last_clear, st.session_state.learned_ids)
                        st.session_state.phase = "goal"
                    st.rerun()
                elif u_in != "":
                    st.session_state.wrong_id = word['id']
                    st.rerun()

# ゴール画面
elif st.session_state.phase == "goal":
    st.balloons()
    st.success("🎉 今日の学習、すべて完了！お疲れ様でした！")
    n = st.session_state.neta
    st.info("💡 " + str(n.get('comedian', '芸人')) + "の豆知識\n\n" + str(n.get('fact', 'すごい豆知識')))
    if st.button("終了してログアウト", use_container_width=True):
        st.query_params.clear()
        components.html("<script>localStorage.clear();</script>", height=0)
        st.session_state.clear()
        st.rerun()
