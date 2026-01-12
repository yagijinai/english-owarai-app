import streamlit as st
import pandas as pd
import datetime
import random
import requests
import json
import streamlit.components.v1 as components
import hashlib

# ==========================================
# 1. 基本設定とFirebase連携
# ==========================================
st.set_page_config(page_title="お笑い英語マスター Pro", page_icon="📝")

# Firebaseの設定 (Firestore)
FIRESTORE_URL = "https://firestore.googleapis.com/v1/projects/english-ap/databases/(default)/documents/users"

def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def get_user_id(name, pw):
    combined = name + "_" + hash_password(pw)
    return combined[:50]

def text_to_speech(text):
    clean_text = str(text).replace("'", "")
    js_code = f"""
    <script>
    var msg = new SpeechSynthesisUtterance();
    msg.text = '{clean_text}';
    msg.lang = 'en-US';
    window.speechSynthesis.speak(msg);
    </script>
    """
    components.html(js_code, height=0)

# ==========================================
# 2. データの読み込み（安全設計）
# ==========================================
@st.cache_data
def load_app_data():
    try:
        w_df = pd.read_csv('words.csv')
        n_df = pd.read_csv('neta.csv')
        if w_df.empty or n_df.empty:
            return None, None, "CSVデータが読み込めません。GitHubのファイルを確認してください。"
        w_df['id'] = w_df['word'].astype(str) + "_" + w_df['meaning'].astype(str)
        return w_df, n_df, None
    except Exception as e:
        return None, None, f"エラーが発生しました: {str(e)}"

WORDS_DF, NETA_DF, LOAD_ERROR = load_app_data()

# ==========================================
# 3. データベース（Firestore）操作
# ==========================================
def fetch_data(uid):
    url = f"{FIRESTORE_URL}/{uid}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            f = res.json().get("fields", {})
            d_name = f.get("display_name", {}).get("stringValue", "User")
            streak = int(f.get("streak", {}).get("integerValue", 0))
            last_c = f.get("last_clear", {}).get("stringValue", "")
            l_ids = [v.get("stringValue") for v in f.get("learned_ids", {}).get("arrayValue", {}).get("values", []) if v.get("stringValue")]
            return {"name": d_name, "streak": streak, "last_clear": last_c, "learned_ids": l_ids}
    except:
        pass
    return None

def save_data(uid, name, streak, last, l_ids):
    url = f"{FIRESTORE_URL}/{uid}"
    payload = {
        "fields": {
            "display_name": {"stringValue": str(name)},
            "streak": {"integerValue": int(streak)},
            "last_clear": {"stringValue": str(last)},
            "learned_ids": {"arrayValue": {"values": [{"stringValue": str(i)} for i in l_ids]}}
        }
    }
    try:
        requests.patch(url, json=payload, timeout=5)
    except:
        pass

# ==========================================
# 4. セッション（アプリの記憶）の初期化
# ==========================================
if "phase" not in st.session_state:
    st.session_state.phase = "login"
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.streak = 0
    st.session_state.last_clear = ""
    st.session_state.learned_ids = []
    st.session_state.is_correct_feedback = False
    st.session_state.show_hint = False
    st.session_state.tokkun_word = None
    st.session_state.p_list = [] # 練習用
    st.session_state.r_list = [] # テスト用
    st.session_state.idx = 0

# ==========================================
# 5. メイン画面：ログイン
# ==========================================
if st.session_state.phase == "login":
    st.title("English Master Pro")
    
    # ブラウザ記憶チェック
    if "checked_storage" not in st.session_state:
        components.html("""
            <script>
            var id = localStorage.getItem('eng_id');
            var nm = localStorage.getItem('eng_nm');
            if(id && nm && !window.location.hash.includes('id=')){
                parent.window.location.hash = 'id=' + id + '&nm=' + encodeURIComponent(nm);
            }
            </script>
        """, height=0)
        st.session_state.checked_storage = True

    params = st.query_params
    if "id" in params and "nm" in params:
        u_id, u_nm = params["id"], params["nm"]
        st.success(f"おかえりなさい、 **{u_nm}** さん！")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔥 続きをする", use_container_width=True):
                data = fetch_data(u_id)
                if data:
                    st.session_state.user_id, st.session_state.user_name = u_id, u_nm
                    st.session_state.streak, st.session_state.last_clear = data["streak"], data["last_clear"]
                    st.session_state.learned_ids = data["learned_ids"]
                    st.session_state.phase = "init"
                    st.rerun()
        with c2:
            if st.button("👤 別の人でログイン", use_container_width=True):
                st.query_params.clear()
                components.html("<script>localStorage.clear();</script>", height=0)
                st.rerun()
    else:
        n_in = st.text_input("なまえ").strip()
        p_in = st.text_input("パスワード", type="password")
        if st.button("🚀 はじめる", use_container_width=True):
            if n_in and p_in:
                u_id = get_user_id(n_in, p_in)
                data = fetch_data(u_id) or {"name": n_in, "streak": 0, "last_clear": "", "learned_ids": []}
                st.session_state.user_id, st.session_state.user_name = u_id, n_in
                st.session_state.streak, st.session_state.last_clear = data["streak"], data["last_clear"]
                st.session_state.learned_ids = data["learned_ids"]
                components.html(f"<script>localStorage.setItem('eng_id','{u_id}');localStorage.setItem('eng_nm','{n_in}');</script>", height=0)
                st.query_params["id"], st.query_params["nm"] = u_id, n_in
                st.session_state.phase = "init"
                st.rerun()
    st.stop()

# データエラーがあれば表示
if LOAD_ERROR:
    st.error(LOAD_ERROR)
    st.stop()

# ==========================================
# 6. 画面：初期化 (init)
# ==========================================
if st.session_state.phase == "init":
    today = str(datetime.date.today())
    yst = str(datetime.date.today() - datetime.timedelta(days=1))
    if st.session_state.last_clear != yst and st.session_state.last_clear != today:
        st.session_state.streak = 0
    
    random.seed(int(today.replace("-", "")))
    
    # 未学習単語の抽出
    not_learned = WORDS_DF[~WORDS_DF['id'].isin(st.session_state.learned_ids)]
    if len(not_learned) < 3: not_learned = WORDS_DF
    
    st.session_state.p_list = not_learned.sample(n=min(3, len(not_learned))).to_dict('records')
    st.session_state.r_list = WORDS_DF.sample(n=min(3, len(WORDS_DF))).to_dict('records')
    st.session_state.neta = NETA_DF.sample(n=1).iloc[0]
    st.session_state.idx = 0
    st.session_state.phase = "practice"
    st.rerun()

# サイドバー表示
st.sidebar.write(f"👤 {st.session_state.user_name} | 🔥 {st.session_state.streak}日目")

# ==========================================
# 7. 画面：Step 1 練習
# ==========================================
if st.session_state.phase == "practice":
    if not st.session_state.p_list:
        st.session_state.phase = "init"
        st.rerun()
        
    word = st.session_state.p_list[st.session_state.idx]
    st.subheader(f"Step 1: 練習 ({st.session_state.idx + 1}/3)")
    st.markdown(f"<h1 style='color:#FF4B4B; text-align:center;'>{word['meaning']}</h1>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔊 音を聞く", use_container_width=True): text_to_speech(word['word'])
    with c2:
        if st.button("👀 見本を見る", use_container_width=True): st.session_state.show_hint = not st.session_state.show_hint
    
    if st.session_state.show_hint: st.info(f"こたえ: {word['word']}")
    
    a1 = st.text_input("1回目", key=f"p1_{st.session_state.idx}").strip().lower()
    a2 = st.text_input("2回目", key=f"p2_{st.session_state.idx}").strip().lower()
    a3 = st.text_input("3回目", key=f"p3_{st.session_state.idx}").strip().lower()
    
    target = str(word['word']).lower()
    if a1 == target and a2 == target and a3 == target:
        if st.button("できた！次の単語へ", use_container_width=True):
            if word['id'] not in st.session_state.learned_ids:
                st.session_state.learned_ids.append
