import streamlit as st
import pandas as pd
import datetime
import random
import requests
import json
import streamlit.components.v1 as components
import hashlib

# --- 基本設定 ---
st.set_page_config(page_title="お笑い英語マスター", page_icon="📝")
FB_URL = "https://firestore.googleapis.com/v1/projects/english-ap/databases/(default)/documents/users"

def get_uid(name, pw):
    val = name + "_" + hashlib.sha256(pw.encode()).hexdigest()
    return val[:50]

def play_sound(txt):
    t = str(txt).replace("'", "")
    code = "<script>var m=new SpeechSynthesisUtterance();m.text='"+t+"';m.lang='en-US';window.speechSynthesis.speak(m);</script>"
    components.html(code, height=0)

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

def load_user(uid):
    try:
        r = requests.get(FB_URL + "/" + uid, timeout=5)
        if r.status_code == 200:
            f = r.json().get("fields", {})
            nm = f.get("display_name", {}).get("stringValue", "User")
            sk = int(f.get("streak", {}).get("integerValue", 0))
            lc = f.get("last_clear", {}).get("stringValue", "")
            ids = []
            v_list = f.get("learned_ids", {}).get("arrayValue", {}).get("values", [])
            for v in v_list:
                s = v.get("stringValue")
                if s: ids.append(s)
            return {"nm": nm, "sk": sk, "lc": lc, "ids": ids}
    except:
        pass
    return None

def save_user(uid, nm, sk, lc, ids):
    iv = [{"stringValue": str(i)} for i in ids]
    pay = {"fields": {"display_name": {"stringValue": str(nm)}, "streak": {"integerValue": int(sk)}, "last_clear": {"stringValue": str(lc)}, "learned_ids": {"arrayValue": {"values": iv}}}}
    try:
        requests.patch(FB_URL + "/" + uid, json=pay, timeout=5)
    except:
        pass

# --- セッション初期化 (AttributeError対策) ---
if "phase" not in st.session_state:
    st.session_state.update({"phase":"login","uid":None,"unm":"Guest","streak":0,"last_lc":"","learned_ids":[],"p_list":[],"r_list":[],"idx":0,"show_hint":False,"is_ok":False,"t_word":None})
    # --- メインロジック ---
if st.session_state.phase == "login":
    st.title("English Master Pro")
    if "chk_store" not in st.session_state:
        components.html("<script>var id=localStorage.getItem('eid');var nm=localStorage.getItem('enm');if(id && nm && !window.location.hash.includes('id=')){parent.window.location.hash='id='+id+'&nm='+encodeURIComponent(nm);}</script>", height=0)
        st.session_state.chk_store = True
    p = st.query_params
    if "id" in p and "nm" in p:
        u_id, u_nm = p["id"], p["nm"]
        st.success(u_nm + " さん、こんにちは！")
        if st.button("🔥 学習をはじめる", use_container_width=True):
            d = load_user(u_id)
            if d:
                st.session_state.update({"uid":u_id,"unm":u_nm,"streak":d["sk"],"last_lc":d["lc"],"learned_ids":d["ids"],"phase":"init"})
                st.rerun()
        if st.button("👤 別の人でログイン"):
            st.query_params.clear()
            components.html("<script>localStorage.clear();</script>", height=0)
            st.rerun()
    else:
        name_in = st.text_input("なまえ").strip()
        pass_in = st.text_input("パスワード", type="password")
        if st.button("🚀 はじめる", use_container_width=True):
            if name_in and pass_in:
                u_id = get_uid(name_in, pass_in)
                d = load_user(u_id) or {"nm": name_in, "sk": 0, "lc": "", "ids": []}
                st.session_state.update({"uid":u_id,"unm":name_in,"streak":d["sk"],"last_lc":d["lc"],"learned_ids":d["ids"],"phase":"init"})
                components.html("<script>localStorage.setItem('eid','"+u_id+"');localStorage.setItem('enm','"+name_in+"');</script>", height=0)
                st.query_params["id"], st.query_params["nm"] = u_id, name_in
                st.rerun()
    st.stop()

if st.session_state.phase == "init":
    if W_DF is None:
        st.error("CSVエラー"); st.stop()
    today = str(datetime.date.today())
    yst = str(datetime.date.today() - datetime.timedelta(days=1))
    if st.session_state.last_lc not in [yst, today]:
        st.session_state.streak = 0
    random.seed(int(today.replace("-", "")))
    not_l = W_DF[~W_DF['id'].isin(st.session_state.learned_ids)]
    if len(not_l) < 3: not_l = W_DF
    st.session_state.update({"p_list":not_l.sample(n=min(3, len(not_l))).to_dict('records'), "r_list":W_DF.sample(n=min(3, len(W_DF))).to_dict('records'), "neta":N_DF.sample(n=1).iloc[0], "idx":0, "phase":"practice"})
    st.rerun()

st.sidebar.write("👤 " + str(st.session_state.unm))
st.sidebar.write("🔥 " + str(st.session_state.streak) + " 日目")

if st.session_state.phase == "practice":
    if st.session_state.idx >= len(st.session_state.p_list):
        st.session_state.update({"idx":0, "phase":"test"}); st.rerun()
    wd = st.session_state.p_list[st.session_state.idx]
    st.subheader("Step 1: 練習 (" + str(st.session_state.idx+1) + "/3)")
    st.markdown("<h1 style='color:#FF4B4B;text-align:center;'>"+str(wd['meaning'])+"</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔊 音を聞く"): play_sound(wd['word'])
    with c2:
        if st.button("👀 見本"): st.session_state.show_hint = not st.session_state.show_hint
    if st.session_state.show_hint: st.info("こたえ: " + str(wd['word']))
    a1 = st.text_input("1回目", key="a1_"+str(st.session_state.idx)).strip().lower()
    a2 = st.text_input("2回目", key="a2_"+str(st.session_state.idx)).strip().lower()
    a3 = st.text_input("3回目", key="a3_"+str(st.session_state.idx)).strip().lower()
    if a1 == a2 == a3 == str(wd['word']).lower() and a1 != "":
        if st.button("できた！次へ"):
            if wd['id'] not in st.session_state.learned_ids: st.session_state.learned_ids.append(wd['id'])
            st.session_state.idx += 1; st.session_state.show_hint = False; st.rerun()

elif st.session_state.phase == "test":
    if st.session_state.idx >= len(st.session_state.r_list):
        st.session_state.phase = "goal"; st.rerun()
    wd = st.session_state.r_list[st.session_state.idx]
    st.subheader("Step 2: テスト (" + str(st.session_state.idx+1) + "/" + str(len(st.session_state.r_list)) + ")")
    st.markdown("<h1 style='color:#FF4B4B;text-align:center;'>"+str(wd['meaning'])+"</h1>", unsafe_allow_html=True)
    if st.session_state.is_ok:
        st.success("✨ 正解！！ ✨")
        if st.button("次へ ➡️"): st.session_state.is_ok = False; st.session_state.idx += 1; st.rerun()
    else:
        with st.form(key="f_"+str(st.session_state.idx)):
            ans = st.text_input("英語で？").strip().lower()
            if st.form_submit_button("判定"):
                if ans == str(wd['word']).lower(): st.session_state.is_ok = True
                elif ans != "": st.session_state.update({"t_word":wd, "phase":"tokkun"})
                st.rerun()

elif st.session_state.phase == "tokkun":
    wd = st.session_state.t_word
    st.error("特訓！ 5回書いて覚えよう。 正解: " + str(wd['word']))
    t = [st.text_input(str(i+1)+"回目", key="t"+str(i)).strip().lower() for i in range(5)]
    if all(x == str(wd['word']).lower() for x in t):
        if st.button("特訓完了！"):
            st.session_state.r_list.append(wd); st.session_state.idx += 1; st.session_state.phase = "test"; st.rerun()

elif st.session_state.phase == "goal":
    today = str(datetime.date.today())
    if st.session_state.last_lc != today:
        st.session_state.streak += 1; st.session_state.last_lc = today
        save_user(st.session_state.uid, st.session_state.unm, st.session_state.streak, st.session_state.last_lc, st.session_state.learned_ids)
    st.balloons(); st.success("🎉 クリア！")
    n = st.session_state.neta
    st.info("💡 豆知識: " + str(n.get('comedian','')) + "\n\n" + str(n.get('fact','')))
    if st.button("終わる"):
        st.query_params.clear(); components.html("<script>localStorage.clear();</script>", height=0); st.session_state.clear(); st.rerun()
else:
    st.session_state.phase = "login"; st.rerun()
