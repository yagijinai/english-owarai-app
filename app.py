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

# 2. 変数の初期化 (AttributeErrorを根絶するための重要な部分です)
if "phase" not in st.session_state:
    st.session_state.update({
        "phase": "start_choice",
        "uid": None, "unm": "Guest", "streak": 0,
        "last_lc": "", "learned_ids": [], "p_list": [], "r_list": [],
        "idx": 0, "show_hint": False, "is_ok": False, "t_word": None, "neta": None
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
        w['id'] = w['word'].astype(str) + "_" + w['meaning'].astype(str)
        return w, n
    except:
        return None, None

W_DF, N_DF = load_data()

# 5. ユーザーデータの読み書き
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

# 7. ログイン・ユーザー確認
if st.session_state.phase == "login":
    st.title("ログイン / ユーザー登録")
    p = st.query_params
    if "id" in p and "nm" in p:
        u_id, u_nm = p["id"], p["nm"]
        st.success(f"{u_nm} さんとしてログインしています")
        if st.button("🚀 学習スタート！", use_container_width=True):
            # ログインボタンを押した時に、データを全てセットしてから画面を切り替えます
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

# 8. 学習の準備
if st.session_state.phase == "init":
    if W_DF is None: st.error("単語データが見つかりません"); st.stop()
    today = str(datetime.date.today()); yst = str(datetime.date.today() - datetime.timedelta(days=1))
    if st.session_state.last_lc not in [yst, today]: st.session_state.streak = 0
    random.seed(int(today.replace("-", "")))
    not_l = W_DF[~W_DF['id'].isin(st.session_state.learned_ids)]
    if len(not_l) < 3: not_l = W_DF
    # 豆知識データを辞書として確実に取得
    n_pick = None
    if N_DF is not None and not N_DF.empty:
        n_pick = N_DF.sample(n=1).iloc[0].to_dict()
    
    st.session_state.update({
        "p_list": not_l.sample(n=min(3, len(not_l))).to_dict('records'),
        "r_list": W_DF.sample(n=min(3, len(W_DF))).to_dict('records'),
        "neta": n_pick, "idx": 0, "phase": "practice"
    })
    st.rerun()

# サイドバー表示（データが確定した後に表示するようにガードを強化）
if st.session_state.uid:
    st.sidebar.write(f"👤 {st.session_state.unm} | 🔥 {st.session_state.streak} 日目")

if st.session_state.phase == "practice":
    if st.session_state.idx >= len(st.session_state.p_list):
        st.session_state.update({"idx":0, "phase":"test"}); st.rerun()
    wd = st.session_state.p_list[st.session_state.idx]
    st.subheader(f"練習 ({st.session_state.idx+1}/3)")
    st.markdown(f"<h1 style='color:#FF4B4B;text-align:center;'>{wd['meaning']}</h1>", unsafe_allow_html=True)
    if st.button("🔊 音を聞く"): play_sound(wd['word'])
    a = [st.text_input(f"{i+1}回目", key=f"p{st.session_state.idx}_{i}").strip().lower() for i in range(3)]
    if all(x == str(wd['word']).lower() for x in a) and a[0] != "":
        if st.button("次へ"):
            if wd['id'] not in st.session_state.learned_ids: st.session_state.learned_ids.append(wd['id'])
            st.session_state.idx += 1; st.rerun()

elif st.session_state.phase == "test":
    if st.session_state.idx >= len(st.session_state.r_list):
        st.session_state.phase = "goal"; st.rerun()
    wd = st.session_state.r_list[st.session_state.idx]
    st.subheader(f"テスト ({st.session_state.idx+1}/3)")
    st.markdown(f"<h1 style='color:#FF4B4B;text-align:center;'>{wd['meaning']}</h1>", unsafe_allow_html=True)
    if st.session_state.is_ok:
        st.success("✨ 正解！！ ✨")
        if st.button("次へ ➡️"): st.session_state.is_ok = False; st.session_state.idx += 1; st.rerun()
    else:
        with st.form(key=f"tf_{st.session_state.idx}"):
            ans = st.text_input("英語で？").strip().lower()
            if st.form_submit_button("判定"):
                if ans == str(wd['word']).lower(): st.session_state.is_ok = True
                elif ans != "": st.session_state.update({"t_word":wd, "phase":"tokkun"})
                st.rerun()

elif st.session_state.phase == "tokkun":
    wd = st.session_state.t_word
    st.error(f"特訓！ 正解: {wd['word']}")
    t = [st.text_input(f"{i+1}回目", key=f"t{i}").strip().lower() for i in range(5)]
    if all(x == str(wd['word']).lower() for x in t) and st.button("完了"):
        st.session_state.r_list.append(wd); st.session_state.idx += 1; st.session_state.phase = "test"; st.rerun()

elif st.session_state.phase == "goal":
    today = str(datetime.date.today())
    if st.session_state.last_lc != today:
        st.session_state.streak += 1; st.session_state.last_lc = today
        save_user(st.session_state.uid, st.session_state.unm, st.session_state.streak, st.session_state.last_lc, st.session_state.learned_ids)
    st.balloons(); st.success("🎉 クリア！")
    if st.session_state.neta:
        st.info(f"💡 豆知識: {st.session_state.neta.get('comedian','')} \n\n {st.session_state.neta.get('fact','')}")
    if st.button("終了"): st.session_state.clear(); st.rerun()
