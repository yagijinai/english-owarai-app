import streamlit as st
import streamlit.components.v1 as components
import random
import json
import os
import gspread
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials

st.set_page_config(layout="centered", page_title="英単語マスター", page_icon="📝")

# 【修正】スマホで画面が上部に隠れて真っ白になるのを防ぐため、9.0remに広げています
st.markdown("""
<style>
    .block-container { padding-top: 9.0rem !important; padding-bottom: 0rem !important; }
    h3 { font-size: 1.2rem !important; margin-bottom: 0.5rem !important; }
    div.stButton > button { padding: 0.25rem 0.5rem !important; }
    .stTextInput { margin-top: -10px !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 【認証データ】
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

SPREADSHEET_NAME = "英単語学習アプリ"
@st.cache_resource
def get_gspread_client():
    credentials_dict = {
        "type": "service_account",
        "project_id": "appsheet-425101",
        "private_key_id": "f5a0438cf15d2aef7ccb83533ecda7d6f51fc59b",
        "private_key": raw_private_key.replace('\\n', '\n'),
        "client_email": "appsheet@appsheet-425101.iam.gserviceaccount.com",
        "client_id": "115714798363749718485",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/appsheet%40appsheet-425101.iam.gserviceaccount.com"
    }
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
    return gspread.authorize(creds)

def load_data_from_sheets(sheet_name):
    try:
        client = get_gspread_client()
        sheet = client.open(SPREADSHEET_NAME).worksheet(sheet_name)
        return sheet.get_all_records()
    except Exception as e:
        st.error(f"スプレッドシート({sheet_name})の読み込みエラー: {e}")
        return []

def update_learned_status(word_id):
    try:
        client = get_gspread_client()
        sheet = client.open(SPREADSHEET_NAME).worksheet('WordList')
        cell = sheet.find(str(word_id), in_column=1)
        if cell:
            sheet.update_cell(cell.row, 7, "TRUE")
    except Exception as e:
        st.error(f"ステータス更新エラー: {e}")

def update_login_streak(user_id):
    try:
        client = get_gspread_client()
        sheet = client.open(SPREADSHEET_NAME).worksheet('UserLog')
        records = sheet.get_all_records()
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_date = datetime.strptime(today_str, "%Y-%m-%d")
        
        user_row_idx = None
        user_data = None
        
        for i, row in enumerate(records):
            if str(row.get('user_id', '')) == str(user_id):
                user_row_idx = i + 2 # Header is row 1
                user_data = row
                break
                
        if user_data:
            last_date_str = str(user_data.get('last_login_date', ''))
            streak = int(user_data.get('streak_count', 0))
            
            try:
                last_date = datetime.strptime(last_date_str, "%Y-%m-%d")
                diff = (today_date - last_date).days
                
                if diff == 0:
                    pass # 同日ログインなので維持
                elif diff == 1:
                    streak += 1 # 昨日ログインなので+1
                else:
                    streak = 1 # 途切れたのでリセット
            except ValueError:
                streak = 1
                
            sheet.update_cell(user_row_idx, 2, today_str)
            sheet.update_cell(user_row_idx, 3, streak)
            return streak
        else:
            new_row = [user_id, today_str, 1]
            sheet.append_row(new_row)
            return 1
            
    except Exception as e:
        st.error(f"ログイン記録更新エラー: {e}")
        return 1
def init_session():
    if 'page' not in st.session_state:
        st.session_state.page = 'login'
    if 'user_id' not in st.session_state:
        st.session_state.user_id = ''
    if 'streak' not in st.session_state:
        st.session_state.streak = 0
    if 'today_words' not in st.session_state:
        st.session_state.today_words = []
    if 'train_queue' not in st.session_state:
        st.session_state.train_queue = []
    if 'test_queue' not in st.session_state:
        st.session_state.test_queue = []
    if 'train_idx' not in st.session_state:
        st.session_state.train_idx = 0
    if 'test_idx' not in st.session_state:
        st.session_state.test_idx = 0
    if 'input_key' not in st.session_state:
        st.session_state.input_key = 0
    if 'retry_count' not in st.session_state:
        st.session_state.retry_count = 0
    if 'last_test_status' not in st.session_state:
        st.session_state.last_test_status = "ok"
    if 'current_retry_target' not in st.session_state:
        st.session_state.current_retry_target = None

def setup_today_words():
    words = load_data_from_sheets('WordList')
    
    # 今日の新規問題（3問）を抽出
    unlearned = [w for w in words if str(w.get('Learned', '')).upper() != "TRUE"]
    if len(unlearned) >= 3:
        today = random.sample(unlearned, 3)
    else:
        today = unlearned

    # 過去の学習済み問題（最大2問）を抽出（★今回の復習テスト拡張）
    learned = [w for w in words if str(w.get('Learned', '')).upper() == "TRUE"]
    review_words = []
    if len(learned) >= 2:
        review_words = random.sample(learned, 2)
    elif len(learned) == 1:
        review_words = learned
        
    st.session_state.today_words = [{'id': w['ID'], 'q': w['Meaning'], 'a': w['Word'].lower().strip()} for w in today]
    review_queue = [{'id': w['ID'], 'q': w['Meaning'], 'a': w['Word'].lower().strip()} for w in review_words]
    
    # 練習用のキュー作成（今日の3問のみ、各3回）
    train = st.session_state.today_words * 3
    random.shuffle(train)
    st.session_state.train_queue = train
    
    # テスト用のキュー作成（今日の3問 + 過去の2問）
    test = st.session_state.today_words + review_queue
    random.shuffle(test)
    st.session_state.test_queue = test

def apply_rescue_autofocus():
    components.html(
        f"""
        <script>
            setTimeout(function() {{
                var inputs = window.parent.document.querySelectorAll('input[type="text"]');
                if(inputs.length > 0) {{
                    inputs[inputs.length - 1].focus();
                }}
            }}, 100);
        </script>
        """,
        height=0, width=0
    )
def show_login():
    st.title("📚 英単語マスター")
    user_id = st.text_input("ユーザーIDを入力してログイン", key="login_input")
    if st.button("ログイン", use_container_width=True):
        if user_id:
            st.session_state.user_id = user_id
            st.session_state.streak = update_login_streak(user_id)
            setup_today_words()
            st.session_state.page = 'menu'
            st.rerun()

def show_menu():
    st.title("📚 メニュー")
    st.success(f"🔥 連続学習: {st.session_state.streak} 日目！")
    
    if st.session_state.today_words:
        st.write("【 今日の単語 】")
        for i, w in enumerate(st.session_state.today_words):
            st.write(f"{i+1}. {w['a']} ({w['q']})")
    
    if st.button("💪 練習を始める", use_container_width=True):
        st.session_state.page = 'train'
        st.session_state.train_idx = 0
        st.rerun()
def show_train():
    if st.session_state.train_idx >= len(st.session_state.train_queue):
        st.success("練習完了！次はテストです。")
        if st.button("テストへ進む", use_container_width=True):
            st.session_state.page = 'test'
            st.session_state.test_idx = 0
            st.session_state.last_test_status = "ok"
            st.rerun()
        return

    target = st.session_state.train_queue[st.session_state.train_idx]
    
    c1, c2 = st.columns([3,1])
    with c1:
        st.subheader(f"Q. {target['q']}")
    with c2:
        if st.button("💡ヒント", key=f"hint_{st.session_state.input_key}"):
            st.info(target['a'])
            
    u_in = st.text_input("英単語を入力", key=f"train_{st.session_state.input_key}")
    apply_rescue_autofocus()
    
    if u_in:
        if u_in.lower().strip() == target['a']:
            st.session_state.train_idx += 1
            st.session_state.input_key += 1
            st.rerun()
        else:
            st.error(f"❌ 惜しい！正解は {target['a']}")
            st.session_state.input_key += 1

def show_retry():
    target = st.session_state.current_retry_target
    remain = 5 - st.session_state.retry_count
    
    if remain <= 0:
        st.success("ペナルティクリア！テストに戻ります。")
        if st.button("テストに戻る", use_container_width=True):
            st.session_state.page = 'test'
            st.rerun()
        return
        
    st.warning(f"⚠️ 間違えた単語の復習: あと {remain} 回正解してください")
    st.subheader(f"Q. {target['q']}")
    st.info(f"正解: {target['a']}")
    
    if st.session_state.last_test_status == "retry_wrong":
        st.error("❌ つづりが正しくありません！やり直し！")
        
    u_in = st.text_input("正しく入力してください", key=f"retry_{st.session_state.input_key}")
    apply_rescue_autofocus()
    
    if u_in:
        if u_in.lower().strip() == target['a']:
            st.session_state.retry_count += 1
            st.session_state.last_test_status = "ok"
            st.session_state.input_key += 1
            st.rerun()
        else:
            st.session_state.last_test_status = "retry_wrong"
            st.session_state.retry_count = 0  # 連続正解を求める場合は0にリセット
            st.session_state.input_key += 1
            st.rerun()

def show_test():
    if st.session_state.test_idx >= len(st.session_state.test_queue):
        st.balloons()
        st.success("🎉 テストクリア！")
        
        # 学習済みフラグを更新
        for w in st.session_state.today_words:
            update_learned_status(w['id'])
            
        neta_list = load_data_from_sheets('RewardList')
        if neta_list:
            neta = random.choice(neta_list)
            st.subheader(f"🎁 ご褒美: {neta.get('タイトル', neta.get('title', '豆知識'))}")
            st.info(neta.get('内容', neta.get('story', '')))
            
        if st.button("メニューへ戻る", use_container_width=True):
            st.session_state.page = 'menu'
            st.rerun()
        return

    target = st.session_state.test_queue[st.session_state.test_idx]
    
    if st.session_state.last_test_status == "test_wrong":
        st.error("❌ つづりが正しくありません！")
        
    test_label = f"🔥 テスト第 {st.session_state.test_idx + 1} 問: 【 {target['q']} 】"
    u_in = st.text_input(test_label, key=f"test_{st.session_state.input_key}")
    apply_rescue_autofocus()
    
    if u_in:
        if u_in.lower().strip() == target['a']:
            st.session_state.test_idx += 1
            st.session_state.last_test_status = "ok"
            st.session_state.input_key += 1
            st.rerun()
        else:
            st.session_state.current_retry_target = target
            st.session_state.retry_count = 0
            st.session_state.last_test_status = "ok"
            st.session_state.page = 'retry'
            st.session_state.input_key += 1
            st.rerun()
def show_train():
    if st.session_state.train_idx >= len(st.session_state.train_queue):
        st.success("練習完了！次はテストです。")
        if st.button("テストへ進む", use_container_width=True):
            st.session_state.page = 'test'
            st.session_state.test_idx = 0
            st.session_state.last_test_status = "ok"
            st.rerun()
        return

    target = st.session_state.train_queue[st.session_state.train_idx]
    
    c1, c2 = st.columns([3,1])
    with c1:
        st.subheader(f"Q. {target['q']}")
    with c2:
        if st.button("💡ヒント", key=f"hint_{st.session_state.input_key}"):
            st.info(target['a'])
            
    u_in = st.text_input("英単語を入力", key=f"train_{st.session_state.input_key}")
    apply_rescue_autofocus()
    
    if u_in:
        if u_in.lower().strip() == target['a']:
            st.session_state.train_idx += 1
            st.session_state.input_key += 1
            st.rerun()
        else:
            st.error(f"❌ 惜しい！正解は {target['a']}")
            st.session_state.input_key += 1

def show_retry():
    target = st.session_state.current_retry_target
    remain = 5 - st.session_state.retry_count
    
    if remain <= 0:
        st.success("ペナルティクリア！テストに戻ります。")
        if st.button("テストに戻る", use_container_width=True):
            st.session_state.page = 'test'
            st.rerun()
        return
        
    st.warning(f"⚠️ 間違えた単語の復習: あと {remain} 回正解してください")
    st.subheader(f"Q. {target['q']}")
    st.info(f"正解: {target['a']}")
    
    if st.session_state.last_test_status == "retry_wrong":
        st.error("❌ つづりが正しくありません！やり直し！")
        
    u_in = st.text_input("正しく入力してください", key=f"retry_{st.session_state.input_key}")
    apply_rescue_autofocus()
    
    if u_in:
        if u_in.lower().strip() == target['a']:
            st.session_state.retry_count += 1
            st.session_state.last_test_status = "ok"
            st.session_state.input_key += 1
            st.rerun()
        else:
            st.session_state.last_test_status = "retry_wrong"
            st.session_state.retry_count = 0  # 連続正解を求める場合は0にリセット
            st.session_state.input_key += 1
            st.rerun()

def show_test():
    if st.session_state.test_idx >= len(st.session_state.test_queue):
        st.balloons()
        st.success("🎉 テストクリア！")
        
        # 学習済みフラグを更新
        for w in st.session_state.today_words:
            update_learned_status(w['id'])
            
        neta_list = load_data_from_sheets('RewardList')
        if neta_list:
            neta = random.choice(neta_list)
            st.subheader(f"🎁 ご褒美: {neta.get('タイトル', neta.get('title', '豆知識'))}")
            st.info(neta.get('内容', neta.get('story', '')))
            
        if st.button("メニューへ戻る", use_container_width=True):
            st.session_state.page = 'menu'
            st.rerun()
        return

    target = st.session_state.test_queue[st.session_state.test_idx]
    
    if st.session_state.last_test_status == "test_wrong":
        st.error("❌ つづりが正しくありません！")
        
    test_label = f"🔥 テスト第 {st.session_state.test_idx + 1} 問: 【 {target['q']} 】"
    u_in = st.text_input(test_label, key=f"test_{st.session_state.input_key}")
    apply_rescue_autofocus()
    
    if u_in:
        if u_in.lower().strip() == target['a']:
            st.session_state.test_idx += 1
            st.session_state.last_test_status = "ok"
            st.session_state.input_key += 1
            st.rerun()
        else:
            st.session_state.current_retry_target = target
            st.session_state.retry_count = 0
            st.session_state.last_test_status = "ok"
            st.session_state.page = 'retry'
            st.session_state.input_key += 1
            st.rerun()
