import streamlit as st
import streamlit.components.v1 as components
import random
import json
import os
import gspread
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials

st.set_page_config(layout="centered", page_title="英単語マスター", page_icon="📝")

# CSSの適用：画面の余白を調整し見やすくする
st.markdown("""
    <style>
        .block-container { padding-top: 9.0rem !important; padding-bottom: 0rem !important; }
        h3 { font-size: 1.2rem !important; margin-bottom: 0.5rem !important; }
        div.stButton > button { padding: 0.25rem 0.5rem !important; }
        .stTextInput { margin-top: -10px !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 認証データ
# ==========================================
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

GOOGLE_KEY_DATA = {
    "type": "service_account",
    "project_id": "english-practice-app-495906",
    "private_key_id": "aa03547283941b2d70424bc519ab338d8b50864d",
    "private_key": raw_private_key,
    "client_email": "english-practice-app@english-practice-app-495906.iam.gserviceaccount.com",
    "client_id": "100283173482304409523",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/english-practice-app%40english-practice-app-495906.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}
# スプレッドシート読み込み関数
@st.cache_data(ttl=600)
def load_data_from_sheets(sheet_name):
    try:
        credentials = Credentials.from_service_account_info(
            GOOGLE_KEY_DATA,
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        gc = gspread.authorize(credentials)
        # スプレッドシートのファイル名を環境に合わせて指定（ここでは仮に指定しています）
        sh = gc.open("英単語学習アプリ") 
        worksheet = sh.worksheet(sheet_name)
        return worksheet.get_all_records()
    except Exception as e:
        st.error(f"スプレッドシート({sheet_name})の読み込みエラー: {e}")
        return []

# セッション状態の初期化
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'word_list' not in st.session_state:
    st.session_state.word_list = []
if 'today_words' not in st.session_state:
    st.session_state.today_words = []
if 'test_queue' not in st.session_state:
    st.session_state.test_queue = []
if 'test_idx' not in st.session_state:
    st.session_state.test_idx = 0
if 'input_key' not in st.session_state:
    st.session_state.input_key = 0
if 'last_test_status' not in st.session_state:
    st.session_state.last_test_status = "none"

# オートフォーカス用関数の定義
def apply_rescue_autofocus():
    components.html("""
        <script>
            setTimeout(function() {
                var inputs = window.parent.document.querySelectorAll('input[type="text"]');
                if (inputs.length > 0) {
                    inputs[inputs.length - 1].focus();
                }
            }, 100);
        </script>
    """, height=0)
def prepare_test():
    # 1. 今日の練習単語（3問）
    today_words = st.session_state.today_words
    
    # 2. 過去の単語（学習済み）を抽出
    all_words = st.session_state.word_list
    learned_words = [w for w in all_words if str(w.get('Learned', '')).strip().upper() == 'TRUE']
    
    # 3. 過去の単語からランダムに最大2問選出
    if len(learned_words) >= 2:
        review_words = random.sample(learned_words, 2)
    else:
        review_words = learned_words  # 2問未満の場合はあるだけ追加
        
    # 4. 今日の単語と過去の単語を合体させてシャッフル
    test_words = today_words + review_words
    random.shuffle(test_words)
    
    # テストキューの作成
    st.session_state.test_queue = [{'q': w['Meaning'], 'a': str(w['Word']).lower().strip()} for w in test_words]
    st.session_state.test_idx = 0
    st.session_state.last_test_status = "none"
    st.session_state.page = 'test'

def show_train():
    st.subheader("📝 今日の英単語練習")
    # ここに通常の練習表示ロジックが入ります
    # （安定版コードにある、3回ずつのループ練習などのロジックをそのまま活用してください）
    
    # 練習が終了したと仮定したあとのボタン
    if st.button("テストへ進む", use_container_width=True):
        prepare_test()
        st.rerun()
def show_test():
    # テスト終了時の処理（ご褒美表示）
    if st.session_state.test_idx >= len(st.session_state.test_queue):
        st.balloons()
        st.success("テストクリア！お疲れ様でした！")
        
        neta_list = load_data_from_sheets('RewardList')
        if neta_list:
            neta = random.choice(neta_list)
            st.subheader(f"🎁 ご褒美: {neta['タイトル']}")
            st.info(neta['内容'])
            
        if st.button("メニューへ戻る", use_container_width=True):
            st.session_state.page = 'menu'
            st.rerun()
        return

    # テスト出題
    target = st.session_state.test_queue[st.session_state.test_idx]
    
    if st.session_state.last_test_status == "test_wrong":
        st.error("❌ つづりが正しくありません！")
        
    test_label = f"🔥 テスト第 {st.session_state.test_idx + 1} 問: 【 {target['q']} 】"
    u_in = st.text_input(test_label, key=f"test_{st.session_state.input_key}")
    apply_rescue_autofocus()
    
    if u_in:
        if u_in.lower().strip() == target['a']:
            st.session_state.test_idx += 1
            st.session_state.last_test_status = "none"
            st.session_state.input_key += 1
            st.rerun()
        else:
            # 誤答時のペナルティ処理への移行
            st.session_state.last_test_status = "test_wrong"
            st.session_state.page = 'retry' # ペナルティ画面を呼び出す
            st.session_state.input_key += 1
            st.rerun()
def main():
    if st.session_state.page == 'login':
        # ログイン処理（既存コードを流用）
        st.session_state.page = 'menu'
        st.rerun()
        
    elif st.session_state.page == 'menu':
        st.title("トップメニュー")
        if st.button("今日の練習を始める"):
            # 単語リストを読み込んで今日の単語をセットする処理（既存を流用）
            st.session_state.word_list = load_data_from_sheets('WordList')
            
            # 例として、LearnedがFALSEのものを今日の単語として3つ抽出
            unlearned = [w for w in st.session_state.word_list if str(w.get('Learned', '')).strip().upper() != 'TRUE']
            if len(unlearned) >= 3:
                st.session_state.today_words = random.sample(unlearned, 3)
            else:
                st.session_state.today_words = unlearned
                
            st.session_state.page = 'train'
            st.rerun()
            
    elif st.session_state.page == 'train':
        show_train()
        
    elif st.session_state.page == 'test':
        show_test()
        
    elif st.session_state.page == 'retry':
        # ここにペナルティ(5回練習)の表示関数 show_retry() を配置
        st.warning("ペナルティ！正しく5回入力してください。")
        # ペナルティクリア後に st.session_state.page = 'test' に戻す
        if st.button("テストに戻る"):
            st.session_state.page = 'test'
            st.rerun()

if __name__ == "__main__":
    main()
