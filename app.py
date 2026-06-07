import streamlit as st
import streamlit.components.v1 as components
import random, json, os, gspread
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials

st.set_page_config(layout="centered", page_title="英単語マスター", page_icon="📝")

# スタイル設定
st.markdown("""
    <style>
        .block-container { padding-top: 6.0rem !important; }
        .stButton > button { width: 100%; }
        h3 { font-size: 1.2rem !important; }
    </style>
""", unsafe_allow_html=True)

# 認証キー定義（※以前のものを継続）
raw_private_key = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDFJ3kSDSSa4tFD
fZovTqM1bIMnorEOvo4lUkRTNPr+ylmZstVRrI/WX86m41TP/a1qmUFtF9e6dOGe
In7kFHEg8qZ9SaXd8PSmBxiEDOuFYd7P8f5bw9JvjT3/w+n0nEH7EDFOsEtAWK5t
ZERsTYsABqVoDmpLzSBia9pgMmjbJei122t15mUAJnImv7cQHKLf81/cM3OlQ0LJ
Fbjx99Kl/3577LlDFK0LoakNYxh7FP0fPPKFMT+GGJNtzQTCgtUh36n0SooW0ByP
URxbvNj8CO6J6WzPI/l5NAKBjkOmV069ukXdwdH1Nre70zWh6eviEVFPsOj3dad+
9m89QdO1AgMBAAECggEAB/mXySYk8+r24g8DnKRGr9OK3qCTHvCQWWwhfWgoOwQ+
aZw1Ss97JgXMGy4Y8SzmxegbIGmVfWJa+gWVMm6tQNLv7yN6hSbJDqo80KKhKE0U
MT8ttdKPAZoqBt2K6i0j8h7uj6tL7/dmXuBucB8W31JlgHcMz7IlfDW2qKuBWFP3
DutjVm3T8gTiQKC2kADspztDTX+fWTtJ8hzVnYbbqj+va6y3Hx1oMMWUzMz1wBSC
xgdkzNfyPub9ZizkOJz9Cvn5oDwIy99sZ7crooElopLFLPdfRuWRj5rcuEwXJrxo
WHx+vQvouK9B8o1f8BlQFcIY53WnwHiZloo3w1weZQKBgQDlfANXZBPY069YXp8B
ro4ikNL/1ZmF6qt8Rk3Cqf2pwWiwrWSYJtDIny/GSODCSn63EQxC5t4Z4JuLFHmj
jtf/uY7C9p85Ds3bEVkboavU2+YS4Quu88UgN6GrOAebg41AkxZmF+mHTvvb1rHm
/Ohk0BTKUZXqhmAwQZTDxjQgCwKBgQDb7yeHSsf8TZq1NKw63U8W8GbqCyWtI7Fx
+cX13CmORz8/0WpoAdntrUN6cCHoxm8tkl/sh480DLI2TIz9+nquAusoou3Aepzu
C2Ji3uEzqeYLfGRt+EJRLQ76X8E61qPnQpqtstrr3AUbQvZiTG30eWR3ZDg7v/IF
FWvgbLtzPwKBgH0yPPhuZs2CH0VMyd63BmAhNpvQQmNm9YtlJ4MuDm+QTrckwZ6o
fnsVLZE1rTkSPzNMn63YGg9wFCu6TepHQdwHtbTzq0YLp47+VejXONF17n0aPa+C
2maLMy4f8TaMfIFgPXYRUZw6IPl8la35CCgHxW/jNrCuAsgQ30I3XbSlAoGAMpHZ
1+zk8OlzIik7VMmgLtkWAMiRYC8t1NQmpXJ7B6DwNR9UxRdv4YuOUW/JDDncRHE8
pylATyqAK6YMYTWf0bUQFybnXfOTc9SgSbWPuI5fO9LdUL/dl8axg/ZSetHxm/If
mMLgPY04i10pQ87pFWZ4KE+d8ncfEfYr+M1niIcCgYEAgrqQPsCFA6Lgd+iH3sh6
Kc0YB3u+HNQc5wT63sIf0uQBAgiWMJwcxpO4N4v0g3xxkYoyomGl5KCs2Q7QrkNr
8x1jSJvUmli5Ph08dk/75atSSR4JgpLmpWCNegcnZlToMiOQXPHRVEmTCFPiuWPd
bk+TobPaSKZGAht68O3l2a0=
-----END PRIVATE KEY-----"""

GOOGLE_KEY_DATA = {"type": "service_account", "project_id": "english-practice-app-495906", "private_key_id": "aa03547283941b2d70424bc519ab338d8b50864d", "private_key": raw_private_key, "client_email": "english-practice-app@english-practice-app-495906.iam.gserviceaccount.com", "client_id": "100283173482304409523", "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token", "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs", "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/english-practice-app%40english-practice-app-495906.iam.gserviceaccount.com", "universe_domain": "googleapis.com"}

def init_session():
    defaults = {'page': 'start', 'logged_in': False, 'grade': "中2", 'session_words': [], 'training_counts': {}, 'test_queue': [], 'test_idx': 0, 'wrong_target': None, 'wrong_retry_count': 0, 'input_key': 0, 'hint_shown': False, 'current_train_word': None}
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

init_session()

def load_data_from_sheets(sheet_name, selected_grade=None):
    try:
        creds = Credentials.from_service_account_info(GOOGLE_KEY_DATA, scopes=['https://www.googleapis.com/auth/spreadsheets'])
        client = gspread.authorize(creds)
        rows = client.open("英単語学習アプリ").worksheet(sheet_name).get_all_values()
        if len(rows) <= 1: return []
        if sheet_name == "WordList":
            g_map = {"中1": "1", "中2": "2", "中3": "3"}
            target_g = g_map.get(selected_grade, "2")
            return [{"q": r[2], "a": r[1].lower().strip()} for r in rows[1:] if len(r) >= 5 and r[4] == target_g]
        return [{"title": r[2], "story": r[3]} for r in rows[1:] if len(r) >= 4]
    except: return []
def show_start():
    st.title("English Master")
    if st.button("同じIDでつづける"): st.session_state.update({'logged_in': True, 'page': 'menu'}); st.rerun()
    if st.button("新しいIDではじめる"): st.session_state.update({'logged_in': True, 'page': 'menu'}); st.rerun()

def show_menu():
    st.subheader("メインメニュー")
    st.session_state.grade = st.selectbox("学年選択", ["中1", "中2", "中3"], index=1)
    if st.button("🚀 練習開始"):
        words = load_data_from_sheets('WordList', st.session_state.grade)
        if words:
            st.session_state.session_words = random.sample(words, min(3, len(words)))
            st.session_state.training_counts = {w['a']: 0 for w in st.session_state.session_words}
            st.session_state.page = 'train'; st.rerun()
def show_train():
    # 注文2: ヒントボタンを最上部に配置
    if st.button("❓ ヒントをみる"): st.session_state.hint_shown = True
    if st.session_state.hint_shown and st.session_state.current_train_word:
        st.info(f"💡 正解: {st.session_state.current_train_word['a']}")

    pending = [w for w in st.session_state.session_words if st.session_state.training_counts.get(w['a'], 0) < 3]
    if not pending: st.session_state.page = 'test'; st.rerun()
    
    if st.session_state.current_train_word is None: st.session_state.current_train_word = random.choice(pending)
    
    # 練習単語の表示
    st.subheader(f"単語: {st.session_state.current_train_word['q']}")
    
    u_in = st.text_input("英語を入力:", key=f"t_{st.session_state.input_key}")
    apply_rescue_autofocus()
    
    if u_in:
        if u_in.lower().strip() == st.session_state.current_train_word['a']:
            st.session_state.training_counts[st.session_state.current_train_word['a']] += 1
            st.session_state.current_train_word = None
        st.session_state.input_key += 1; st.rerun()

# メインルーター
if not st.session_state.logged_in: show_start()
elif st.session_state.page == 'menu': show_menu()
elif st.session_state.page == 'train': show_train()
def apply_rescue_autofocus():
    components.html("""<script>(function(){ var inputs = window.parent.document.querySelectorAll('input[type="text"]'); if(inputs.length>0) inputs[inputs.length-1].focus(); })();</script>""", height=0)
