import streamlit as st
import pandas as pd
import datetime
import random
import requests
import json
import streamlit.components.v1 as components
import hashlib

# 1. ページ基本設定
st.set_page_config(page_title="お笑い英語マスター 完全版", page_icon="📝")

# 2. データの入れ物を最初に準備 (AttributeError対策)
# ここに全ての名前を登録しておくことで、エラーを根絶します
if "phase" not in st.session_state:
    st.session_state.update({
        "phase": "start_choice",
        "uid": None,
        "unm": "Guest",
        "streak": 0,
        "last_lc": "",
        "learned_ids": [],
        "p_list": [],
        "r_list": [],
        "idx": 0,
        "show_hint": False,
        "is_ok": False,
        "t_word": None,
        "neta": None
    })

# 3. 音声再生機能
def play_sound(txt):
    t = str(txt).replace("'", "")
    code = f"<script>var m=new SpeechSynthesisUtterance();m.text='{t}';m.lang='en-US';window.speechSynthesis.speak(m);</script>"
    components.html(code, height=0)
    # 4. CSVデータの読み込み
@st.cache_data
def load_data():
    try:
        w = pd.read_csv('words.csv')
        n = pd.read_csv('neta.csv')
        # IDを確実に作成
        w['id'] = w['word'].astype(str) + "_" + w['meaning'].astype(str)
        return w, n
    except:
        return None, None

W_DF, N_DF = load_data()

# 5. ユーザーデータの読み書き (Firestore)
FB_URL = "https://firestore.googleapis.com/v1/projects/english-ap/databases/(default)/documents/users"

def load_user(uid):
    try:
        r = requests.get(f"{FB_URL}/{uid}", timeout=5)
        if r.status_code == 200:
            f = r.json().get("fields", {})
            return {
                "nm": f.get("display_name", {}).get("stringValue", "User"),
                "sk": int(f.get("streak", {}).get("integerValue", 0)),
                "lc": f.get("last_clear", {}).get("stringValue", ""),
                "ids": [v.get("stringValue") for v in f.get("learned_ids", {}).get("arrayValue", {}).get("values", []) if v.get("stringValue")]
            }
    except: pass
    return None

def save_user(uid, nm, sk, lc, ids):
    iv = [{"stringValue": str(i)} for i in ids]
    pay = {"fields": {"display_name": {"stringValue": str(nm)}, "streak": {"integerValue": int(sk)}, "last_clear": {"stringValue": str(lc)}, "learned_ids": {"arrayValue": {"values": iv}}}}
    try: requests.patch(f"{FB_URL}/{uid}", json=pay, timeout=5)
    except: pass
        # 6. 開始時の選択画面
if st.session_state.phase == "start_choice":
    st.title("English Master Pro")
    st.subheader("どちらではじめますか？")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 同じIDでつづける", use_container_width=True):
            components.html("<script>var id=localStorage.getItem('eid');var nm=localStorage.getItem('enm');if(id){parent.window.location.hash='id='+id+'&nm='+encodeURIComponent(nm);}</script>", height=0)
            st.session_state.phase = "login"
            st.rerun()
    with col2:
        if st.button("✨ 新しいIDではじめる", use_container_width=True):
            st.query_params.clear()
            components.html("<script>localStorage.clear();</script>", height=0)
            st.session_state.phase = "login"
            st.rerun()
    st.stop()

# 7. ログイン画面
if st.session_state.phase == "login":
    st.title("ログイン / ユーザー登録")
    p = st.query_params
    if "id" in p and "nm" in p:
        u_id, u_nm = p["id"], p["nm"]
        st.success(f"{u_nm} さんとしてログインしています")
        if st.button("🚀 学習スタート！", use_container_width=True):
            d = load_user(u_id)
            if d:
                st.session_state.update({"uid":u_id, "unm":u_nm, "streak":d["sk"], "last_lc":d["lc"], "learned_ids":d["ids"], "phase":"init"})
                st.rerun()
    
    n_in = st.text_input("なまえ").strip()
    p_in = st.text_input("パスワード", type="password")
    if st.button("ログイン / 新規登録", use_container_width=True):
        if n_in and p_in:
            u_id = hashlib.sha256((n_in + p_in).encode()).hexdigest()[:30]
            d = load_user(u_id) or {"nm": n_in, "sk": 0, "lc": "", "ids": []}
            st.session_state.update({"uid":u_id, "unm":n_in, "streak":d["sk"], "last_lc":d["lc"], "learned_ids":d["ids"], "phase":"init"})
            components.html(f"<script>localStorage.setItem('eid','{u_id}');localStorage.setItem('enm','{n_in}');</script>", height=0)
            st.query_params["id"], st.query_params["nm"] = u_id, n_in
            st.rerun()
    st.stop()
