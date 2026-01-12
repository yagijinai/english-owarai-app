import streamlit as st
import pandas as pd
import datetime
import random
import requests
import json
import streamlit.components.v1 as components
import hashlib

# ==========================================
# 1. 基本設定（最高品質・安定性重視）
# ==========================================
st.set_page_config(page_title="お笑い英語マスター Pro", page_icon="📝")

FIREBASE_CONFIG = {
    "apiKey": "AIzaSyB0Bd8aBmos2fHiD7XgH_S4yM5b__FHypI",
    "authDomain": "english-ap.firebaseapp.com",
    "projectId": "english-ap",
    "storageBucket": "english-ap.firebasestorage.app",
    "messagingSenderId": "167152900538",
    "appId": "1:167152900538:web:07a87314d3121c23eca583"
}

FIRESTORE_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_CONFIG['projectId']}/databases/(default)/documents/users"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_id(name, password):
    combined = f"{name}_{hash_password(password)}"
    return combined[:50]

def text_to_speech(text):
    clean = str(text).replace("'", "")
    js = f"<script>var m=new SpeechSynthesisUtterance();m.text='{clean}';m.lang='en-US';window.speechSynthesis.speak(m);</script>"
    components.html(js, height=0)

# ==========================================
# 2. データ読み込み（異常検知機能付き）
# ==========================================
@st.cache_data
def load_csv_data():
    try:
        w = pd.read_csv('words.csv')
        n = pd.read_csv('neta.csv')
        if w.empty or n.empty:
            return None, None, "CSVの中身が空です。"
        w['id'] = w['word'].astype(str) + "_" + w['meaning'].astype(str)
        return w, n, None
    except Exception as e:
        return None, None, f"読み込み失敗: {str(e)}"

WORDS_DF, NETA_DF, LOAD_ERROR = load_csv_data()

if LOAD_ERROR:
    st.error(f"⚠️ 起動エラー: {LOAD_ERROR}")
    st.stop()

# ==========================================
# 3. データベース操作（真っ白画面防止ガード）
# ==========================================
def fetch_user_data(u_id):
    url = f"{FIRESTORE_URL}/{u_id}"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            f = r.json().get("fields", {})
            
            # 各項目を安全に抽出（データが欠けていても落ちないようにする）
            d_name = f.get("display_name", {}).get("stringValue", "User")
            
            streak_val = f.get("streak", {}).get("integerValue", 0)
            streak = int(streak_val)
            
            last_clear = f.get("last_clear", {}).get("stringValue", "")
            
            # 学習済みIDリストの安全な取得
            learned_ids = []
            l_raw = f.get("learned_ids", {}).get("arrayValue", {}).get("values", [])
            for v in l_raw:
                s_val = v.get("stringValue")
                if s_val:
                    learned_ids.append(s_val)
            
            return {
                "display_name": d_name,
                "streak": streak,
                "last_clear": last_clear,
                "learned_ids": learned_ids
            }
    except Exception as e:
        st.warning(f"データの取得中に小さな問題が起きました（無視して進めます）: {e}")
    return None

def save_user_data(u_id, name, streak, last, l_ids):
    url = f"{FIRESTORE_URL}/{u_id}"
    data = {
        "fields": {
            "display_name": {"stringValue": str(name)},
            "streak": {"integerValue": int(streak)},
            "last_clear": {"stringValue": str(last)},
            "learned_ids": {"arrayValue": {"values": [{"stringValue": str(i)} for i in l_ids]}}
        }
    }
    try:
        requests.patch(url, json=data, timeout=5)
    except:
        pass

# ==========================================
# 4. セッション初期化
# ==========================================
if "phase" not in st.session_state:
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.phase = "login"
    st.session_state.is_correct_feedback = False
    st.session_state.show_hint = False
    st.session_state.streak = 0
    st.session_state.last_clear = ""
    st.session_state.learned_ids = []

# ==========================================
# 5. ログイン画面（二択）
# ==========================================
if st.session_state.phase == "login":
    st.title("English Master Pro")
    
    if "checked_storage" not in st.session_state:
        components.html("""<script>
            var id=localStorage.getItem('eng_app_userid');
            var nm=localStorage.getItem('eng_app_name');
            if(id && nm && !window.location.hash.includes('id=')){
                parent.window.location.hash = 'id='+id+'&nm='+encodeURIComponent(nm);
            }
            </script>""", height=0)
        st.session_state.checked_storage = True

    q = st.query_params
    
    if "id" in q and "nm" in q:
        u_id, u_name = q["id"], q["nm"]
        st.success(f"おかえりなさい、 **{u_name}** さん！")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔥 続きをする", use_container_width=True):
                # ここで真っ白になるのを防ぐため try-except で囲む
                try:
                    d = fetch_user_data(u_id)
                    if d:
                        st.session_state.user_id = u_id
                        st.session_state.user_name = u_name
                        st.session_state.streak = d["streak"]
                        st.session_state.last_clear = d["last_clear"]
                        st.session_state.learned_ids = d["learned_ids"]
                        st.session_state.phase = "init"
                        st.rerun()
                    else:
                        st.error("保存データが見つかりませんでした。新しくログインしてください。")
                except Exception as e:
                    st.error(f"データの読み込み中にエラーが発生しました: {e}")
                    if st.button("新しくやり直す"):
                        st.query_params.clear()
                        st.rerun()
        with col2:
            if st.button("👤 新しくログインする", use_container_width=True):
                st.query_params.clear()
                components.html("<script>localStorage.clear();</script>", height=0)
                st.session_state.clear() # セッションを完全にリセット
                st.rerun()
    else:
        st.info("お名前とパスワードを入力してください")
        n_in = st.text_input("なまえ").strip()
        p_in = st.text_input("パスワード", type="password")
        if st.button("🚀 ログイン / 登録", use_container_width=True):
            if n_in and p_in:
                u_id = get_user_id(n_in, p_in)
                d = fetch_user_data(u_id)
                if not d:
                    save_user_data(u_id, n_in, 0, "", [])
                    d = {"display_name": n_in, "streak": 0, "last_clear": "", "learned_ids": []}
                
                st.session_state.user_id = u_id
                st.session_state.user_name = n_in
                st.session_state.streak = d["streak"]
                st.session_state.last_clear = d["last_clear"]
                st.session_state.learned_ids = d["learned_ids"]
                
                components.html(f"<script>localStorage.setItem('eng_app_userid','{u_id}');localStorage.setItem('eng_app_name','{n_in}');</script>", height=0)
                st.query_params["id"] = u_id
                st.query_params["nm"] = n_in
                st.session_state.phase = "init"
                st.rerun()
    st.stop()

# ==========================================
# 6. 学習ロジック（真っ白画面防止の徹底）
# ==========================================
if st.session_state.phase == "init":
    try:
        today = str(datetime.date.today())
        yst = str(datetime.date.today() - datetime.timedelta(days=1))
        
        # 連続日数の更新
        if st.session_state.last_clear != yst and st.session_state.last_clear != today:
            st.session_state.streak = 0
        
        random.seed(int(today.replace("-", "")))
        
        # 練習単語の選出
        unlearned = WORDS_DF[~WORDS_DF['id'].isin(st.session_state.learned_ids)]
        if len(unlearned) < 3: unlearned = WORDS_DF
        st.session_state.p_list = unlearned.sample(n=min(3, len(unlearned))).to_dict('records')
        
        # 復習テスト単語の選出
        st.session_state.r_list = WORDS_DF.sample(n=min(3, len(WORDS_DF))).to_dict('records')
        
        # ネタの選出
        st.session_state.neta = NETA_DF.sample(n=1).iloc[0]
        
        st.session_state.idx = 0
        st.session_state.phase = "practice"
        st.rerun()
    except Exception as e:
        st.error(f"初期化中にエラーが発生しました。データをリセットしてやり直してください: {e}")
        if st.button("ログイン画面へ戻る"):
            st.session_state.clear()
            st.rerun()

st.sidebar.write(f"👤 {st.session_state.user_name} | 🔥 {
