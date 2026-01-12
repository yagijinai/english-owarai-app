import streamlit as st
import pandas as pd
import datetime
import random
import requests
import json
import streamlit.components.v1 as components
import hashlib

# ==========================================
# 1. アプリ基本設定
# ==========================================
st.set_page_config(page_title="お笑い英語マスター Pro", page_icon="📝")

# Firebaseの設定 (Firestoreを使用)
FIREBASE_CONFIG = {
    "projectId": "english-ap"
}
FIRESTORE_URL = "https://firestore.googleapis.com/v1/projects/english-ap/databases/(default)/documents/users"

# パスワードを安全に保存するための処理
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ユーザーIDの生成
def get_user_id(name, pw):
    combined = name + "_" + hash_password(pw)
    return combined[:50]

# 英語の音声を出すためのJavaScript
def text_to_speech(text):
    clean_text = str(text).replace("'", "")
    js_code = """
    <script>
    var msg = new SpeechSynthesisUtterance();
    msg.text = '""" + clean_text + """';
    msg.lang = 'en-US';
    window.speechSynthesis.speak(msg);
    </script>
    """
    components.html(js_code, height=0)

# ==========================================
# 2. データの読み込み (エラー防止ガード付)
# ==========================================
@st.cache_data
def load_app_data():
    try:
        # 単語データの読み込み
        w_df = pd.read_csv('words.csv')
        # ネタデータの読み込み
        n_df = pd.read_csv('neta.csv')
        
        if w_df.empty or n_df.empty:
            return None, None, "CSVファイルの中身が空っぽです。"
            
        # 単語に一意のIDを付与
        w_df['id'] = w_df['word'].astype(str) + "_" + w_df['meaning'].astype(str)
        return w_df, n_df, None
    except Exception as e:
        return None, None, "ファイルの読み込みに失敗しました: " + str(e)

WORDS_DF, NETA_DF, LOAD_ERROR = load_app_data()

# ==========================================
# 3. データベース（Firestore）との通信
# ==========================================
def get_remote_data(uid):
    url = FIRESTORE_URL + "/" + uid
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            fields = res.json().get("fields", {})
            
            # データの取り出し（一つずつ安全に）
            d_name = fields.get("display_name", {}).get("stringValue", "User")
            streak = int(fields.get("streak", {}).get("integerValue", 0))
            last_c = fields.get("last_clear", {}).get("stringValue", "")
            
            # 学習済みリストの取り出し
            l_ids = []
            l_raw = fields.get("learned_ids", {}).get("arrayValue", {}).get("values", [])
            for v in l_raw:
                s = v.get("stringValue")
                if s: l_ids.append(s)
            
            return {"name": d_name, "streak": streak, "last_clear": last_c, "learned_ids": l_ids}
    except:
        pass
    return None

def save_remote_data(uid, name, streak, last, l_ids):
    url = FIRESTORE_URL + "/" + uid
    id_values = []
    for i in l_ids:
        id_values.append({"stringValue": str(i)})
        
    payload = {
        "fields": {
            "display_name": {"stringValue": str(name)},
            "streak": {"integerValue": int(streak)},
            "last_clear": {"stringValue": str(last)},
            "learned_ids": {"arrayValue": {"values": id_values}}
        }
    }
    try:
        requests.patch(url, json=payload, timeout=5)
    except:
        pass

# ==========================================
# 4. セッション（記憶）の初期化
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

# ==========================================
# 5. 画面：ログイン (二択機能)
# ==========================================
if st.session_state.phase == "login":
    st.title("English Master Pro")
    
    # ブラウザに記憶があるかチェック
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

    # URLパラメータから名前を取得
    params = st.query_params
    
    if "id" in params and "nm" in params:
        u_id = params["id"]
        u_nm = params["nm"]
        st.success("おかえりなさい！ **" + u_nm + "** さん")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔥 続きをする", use_container_width=True):
                data = get_remote_data(u_id)
                if data:
                    st.session_state.user_id = u_id
                    st.session_state.user_name = u_nm
                    st.session_state.streak = data["streak"]
                    st.session_state.last_clear = data["last_clear"]
                    st.session_state.learned_ids = data["learned_ids"]
                    st.session_state.phase = "init"
                    st.rerun()
                else:
                    st.error("データが見つかりませんでした。新しくログインしてください。")
        with col2:
            if st.button("👤 別の人でログイン", use_container_width=True):
                st.query_params.clear()
                components.html("<script>localStorage.clear();</script>", height=0)
                st.rerun()
    else:
        # 通常のログインフォーム
        st.info("なまえとパスワードを決めて入力してね！")
        n_in = st.text_input("なまえ").strip()
        p_in = st.text_input("パスワード", type="password")
        
        if st.button("🚀 はじめる", use_container_width=True):
            if n_in and p_in:
                u_id = get_user_id(n_in, p_in)
                data = get_remote_data(u_id)
                if not data:
                    save_remote_data(u_id, n_in, 0, "", [])
                    data = {"name": n_in, "streak": 0, "last_clear": "", "learned_ids": []}
                
                st.session_state.user_id = u_id
                st.session_state.user_name = n_in
                st.session_state.streak = data["streak"]
                st.session_state.last_clear = data["last_clear"]
                st.session_state.learned_ids = data["learned_ids"]
                
                # ブラウザに記憶させる
                js_save = "<script>localStorage.setItem('eng_id','" + u_id + "');localStorage.setItem('eng_nm','" + n_in + "');</script>"
                components.html(js_save, height=0)
                st.query_params["id"] = u_id
                st.query_params["nm"] = n_in
                st.session_state.phase = "init"
                st.rerun()
    st.stop()

# 起動エラーがあればここで止める
if LOAD_ERROR:
    st.error(LOAD_ERROR)
    st.stop()

# ==========================================
# 6. 画面：今日の問題準備
# ==========================================
if st.session_state.phase == "init":
    today = str(datetime.date.today())
    yst = str(datetime.date.today() - datetime.timedelta(days=1))
    
    # 連続日数の計算
    if st.session_state.last_clear != yst and st.session_state.last_clear != today:
        st.session_state.streak = 0
    
    random.seed(int(today.replace("-", "")))
    
    # 練習単語の選出
    not_learned = WORDS_DF[~WORDS_DF['id'].isin(st.session_state.learned_ids)]
    if len(not_learned) < 3:
        not_learned = WORDS_DF
    
    st.session_state.p_list = not_learned.sample(n=min(3, len(not_learned))).to_dict('records')
    st.session_state.r_list = WORDS_DF.sample(n=min(3, len(WORDS_DF))).to_dict('records')
    st.session_state.neta = NETA_DF.sample(n=1).iloc[0]
    st.session_state.idx = 0
    st.session_state.phase = "practice"
    st.rerun()

# サイドバー表示
st.sidebar.write("👤 " + str(st.session_state.user_name))
st.sidebar.write("🔥 " + str(st.session_state.streak) + " 日目")

# ==========================================
# 7. 画面：練習（Step 1）
# ==========================================
if st.session_state.phase == "practice":
    word = st.session_state.p_list[st.session_state.idx]
    st.subheader("Step 1: 練習 (" + str(st.session_state.idx + 1) + "/3)")
    
    # 日本語を大きく表示
    st.markdown("<h1 style='color:#FF4B4B; text-align:center;'>" + str(word['meaning']) + "</h1>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔊 音を聞く", use_container_width=True):
            text_to_speech(word['word'])
    with c2:
        if st.button("👀 見本を見る", use_container_width=True):
            st.session_state.show_hint = not st.session_state.show_hint
            
    if st.session_state.show_hint:
        st.info("こたえ: " + str(word['word']))
    
    st.write("下に3回同じ英単語を書いてみよう！")
    a1 = st.text_input("1回目", key="a1_" + str(st.session_state.idx)).strip().lower()
    a2 = st.text_input("2回目", key="a2_" + str(st.session_state.idx)).strip().lower()
    a3 = st.text_input("3回目", key="a3_" + str(st.session_state.idx)).strip().lower()
    
    target = str(word['word']).lower()
    if a1 == target and a2 == target and a3 == target:
        if st.button("できた！次の単語へ", use_container_width=True):
            if word['id'] not in st.session_state.learned_ids:
                st.session_state.learned_ids.append(word['id'])
            st.session_state.idx += 1
            st.session_state.show_hint = False
            if st.session_state.idx >= 3:
                st.session_state.idx = 0
                st.session_state.phase = "test"
            st.rerun()

# ==========================================
# 8. 画面：復習テスト（Step 2）
# ==========================================
elif st.session_state.phase == "test":
    word = st.session_state.r_list[st.session_state.idx]
    st.subheader("Step 2: 復習テスト (" + str(st.session_state.idx + 1) + "/3)")
    st.markdown("<h1 style='color:#FF4B4B; text-align:center;'>" + str(word['meaning']) + "</h1>", unsafe_allow_html=True)

    if st.session_state.is_correct_feedback:
        st.success("✨ 正解！！ すばらしい！ ✨")
        if st.button("次の問題へ進む ➡️", use_container_width=True):
            st.session_state.is_correct_feedback = False
            st.session_state.idx += 1
            if st.session_state.idx >= 3:
                # すべてクリア
                t_day = str(datetime.date.today())
                if st.session_state.last_clear != t_day:
                    st.session_state.streak += 1
                    st.session_state.last_clear = t_day
                save_remote_data(st.session_state.user_id, st.session_state.user_name, st.session_state.streak, st.session_state.last_clear, st.session_state.learned_ids)
                st.session_state.phase = "goal"
            st.rerun()
    else:
        with st.form(key="test_form_" + str(st.session_state.idx)):
            user_ans = st.text_input("この単語、英語で書けるかな？").strip().lower()
            if st.form_submit_button("判定する！"):
                if user_ans == str(word['word']).lower():
                    st.session_state.is_correct_feedback = True
                    st.rerun()
                elif user_ans != "":
                    st.warning("おしい！つづりを確認してもう一度やってみよう。")

# ==========================================
# 9. 画面：ゴール
# ==========================================
elif st.session_state.phase == "goal":
    st.balloons()
    st.success("🎉 おめでとうございます！今日の学習はすべて完了です！")
    
    n = st.session_state.neta
    st.info("💡 【" + str(n.get('comedian', '芸人')) + "】の豆知識\n\n" + str(n.get('fact', 'データなし')))
    
    if st.button("ログアウトして終わる", use_container_width=True):
        st.query_params.clear()
        components.html("<script>localStorage.clear();</script>", height=0)
        st.session_state.clear()
        st.rerun()

# ==========================================
# [おわり] これより下の行は何も書かないでください
# ==========================================
