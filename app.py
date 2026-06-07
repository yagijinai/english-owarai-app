import streamlit as st
import streamlit.components.v1 as components
import random
import json
import os
import gspread
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials

st.set_page_config(layout="centered", page_title="英単語マスター", page_icon="📝")

# スマホの画面の上下余白をギリギリまで削ってコンパクトにする魔法の設定
st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
        h3 { font-size: 1.2rem !important; margin-bottom: 0.5rem !important; }
        div.stButton > button { padding: 0.25rem 0.5rem !important; }
        .stTextInput { margin-top: -10px !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 【Part 1: バックエンド処理・データ連携と初期化】
# ==========================================

def init_firebase():
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        if not firebase_admin._apps:
            if "FIREBASE_SECRET" in st.secrets:
                key_dict = json.loads(st.secrets["FIREBASE_SECRET"])
                cred = credentials.Certificate(key_dict)
                firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception:
        return None

db = init_firebase()

def init_session():
    if 'page' not in st.session_state:
        st.session_state.update({
            'page': 'start', 
            'logged_in': False, 
            'grade': "中2", 
            'user_id': "daughter_user",
            'session_words': [], 
            'training_counts': {}, 
            'test_queue': [],
            'test_idx': 0, 
            'wrong_target': None, 
            'wrong_retry_count': 0, 
            'input_key': 0, 
            'hint_shown': False,
            'last_train_status': None, 
            'last_test_status': None,
            'streak_count': 1,
            'current_train_word': None,
            'show_correct_msg': False,
            'start_mode': None
        })

init_session()

def update_login_streak(user_id):
    if db is None:
        return 1
    try:
        today_str = datetime.now().strftime('%Y-%m-%d')
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        user_ref = db.collection('users').document(user_id)
        doc = user_ref.get()
        if doc.exists:
            user_data = doc.to_dict()
            last_login = user_data.get('last_login_date', '')
            current_streak = user_data.get('streak_count', 1)
            if last_login == today_str:
                return current_streak
            elif last_login == yesterday_str:
                new_streak = current_streak + 1
                user_ref.update({'last_login_date': today_str, 'streak_count': new_streak})
                return new_streak
            else:
                user_ref.update({'last_login_date': today_str, 'streak_count': 1})
                return 1
        else:
            user_ref.set({'last_login_date': today_str, 'streak_count': 1})
            return 1
    except Exception:
        return 1

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
# ==========================================
# 【Part 2: メニュー画面と救済機能付き練習画面】
# ==========================================

def load_data_from_sheets(sheet_name, selected_grade=None):
    data = []
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(GOOGLE_KEY_DATA, scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open("英単語学習アプリ")
        worksheet = spreadsheet.worksheet(sheet_name)
        all_records = worksheet.get_all_values()
        
        if not all_records or len(all_records) <= 1:
            return data
        rows = all_records[1:]

        if sheet_name == "RewardList":
            for row in rows:
                if len(row) >= 4:
                    title_val = row[2].strip()
                    story_val = row[3].strip()
                    if title_val and title_val != "タイトル" and story_val:
                        data.append({"title": title_val, "story": story_val})
            return data

        elif sheet_name == "WordList":
            grade_str = "1"
            if selected_grade == "中2":
                grade_str = "2"
            elif selected_grade == "中3":
                grade_str = "3"
            for row in rows:
                if len(row) >= 5:
                    word_val = row[1].strip()
                    meaning_val = row[2].strip()
                    grade_val = row[4].strip()
                    if grade_val == grade_str and word_val and meaning_val:
                        data.append({
                            "grade": selected_grade,
                            "q": meaning_val,
                            "a": word_val.lower().strip()
                        })
            return data
    except Exception as e:
        st.error(f"スプレッドシート通信エラー: {str(e)}")
    return data

def apply_rescue_autofocus():
    components.html(
        """
        <script>
        (function() {
            function grabFocus() {
                var inputs = window.parent.document.querySelectorAll('input[type="text"]');
                if (inputs.length > 0) {
                    var targetInput = inputs[inputs.length - 1];
                    if (window.parent.document.activeElement !== targetInput) {
                        targetInput.focus();
                        targetInput.select();
                    }
                    targetInput.setAttribute("autocomplete", "off");
                    targetInput.setAttribute("autocorrect", "off");
                    targetInput.setAttribute("autocapitalize", "off");
                    targetInput.setAttribute("spellcheck", "false");
                    targetInput.setAttribute("type", "text");
                    targetInput.setAttribute("name", "one-time-code");
                }
            }
            var attempts = 0;
            var focusTimer = setInterval(function() {
                grabFocus();
                attempts++;
                if (attempts >= 30) { clearInterval(focusTimer); }
            }, 40);
            window.parent.document.removeEventListener('keydown', window.handleRescueKey);
            window.handleRescueKey = function(e) {
                var activeEl = window.parent.document.activeElement;
                if (activeEl.tagName !== 'INPUT') {
                    if (e.key === ' ' || e.key === 'Spacebar' || e.key === 'Enter') {
                        e.preventDefault(); grabFocus();
                    }
                }
            };
            window.parent.document.addEventListener('keydown', window.handleRescueKey);
        })();
        </script>
        """,
        height=0,
    )

def show_start():
    st.title("English Master")
    st.subheader("アプリの開始方法を選んでください")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("同じIDでつづける", use_container_width=True):
            st.session_state.start_mode = "continue"
            st.session_state.logged_in = True
            st.session_state.streak_count = update_login_streak(st.session_state.user_id)
            st.session_state.page = 'menu'
            st.rerun()
    with col2:
        if st.button("新しいIDではじめる", use_container_width=True):
            st.session_state.start_mode = "new"
            st.session_state.logged_in = True
            st.session_state.streak_count = update_login_streak(st.session_state.user_id)
            st.session_state.page = 'menu'
            st.rerun()

def show_menu():
    st.title("メインメニュー")
    st.markdown(f"### 🔥 連続学習 **{st.session_state.streak_count}** 日目！")
    st.write("---")
    st.session_state.grade = st.selectbox("学年を選択", ["中1", "中2", "中3"], index=1)
    if st.button("🚀 練習開始", use_container_width=True):
        words = load_data_from_sheets('WordList', st.session_state.grade)
        if words:
            st.session_state.session_words = random.sample(words, min(3, len(words)))
            st.session_state.training_counts = {w['a']: 0 for w in st.session_state.session_words}
            st.session_state.last_train_status = None
            st.session_state.current_train_word = None
            st.session_state.show_correct_msg = False
            st.session_state.page = 'train'
            st.rerun()
        else:
            st.error(f"スプレッドシートの『WordList』から {st.session_state.grade} の単語データを取得できませんでした。")
# ==========================================
# 【Part 3: 復習画面・テスト画面とメインルーター】
# ==========================================

def show_train():
    pending = [w for w in st.session_state.session_words if st.session_state.training_counts.get(w['a'], 0) < 3]
    if not pending:
        st.session_state.test_queue = list(st.session_state.session_words)
        st.session_state.test_idx = 0
        st.session_state.page = 'test'
        st.session_state.last_train_status = None
        st.session_state.current_train_word = None
        st.session_state.hint_shown = False
        st.rerun()
        return

    if st.session_state.current_train_word is None or st.session_state.current_train_word not in pending:
        st.session_state.current_train_word = random.choice(pending)
        st.session_state.last_train_status = None

    target = st.session_state.current_train_word
    current_count = st.session_state.training_counts[target['a']]
    
    # ヒント要求ボタンは一番上にすっきり配置
    if st.button("❓ ヒントをみる", key="hint_btn", use_container_width=True):
        st.session_state.hint_shown = True

    if st.session_state.show_correct_msg:
        st.success("⭕ 正解！ 次へ！")
        st.session_state.show_correct_msg = False 
    elif st.session_state.last_train_status == "wrong":
        st.error("❌ もう一度入力してみよう。")

    # 【修正箇所】ヒントが要求されたら、入力欄のすぐ上のラベルに直接・横幅一杯にドッキングして表示
    if st.session_state.hint_shown:
        input_label = f"【練習】 {target['q']} (正解: {current_count}/3) ⇒ 💡正解：{target['a']}"
    else:
        input_label = f"【練習】 {target['q']} (正解: {current_count}/3)"

    u_in = st.text_input(input_label, key=f"t_{st.session_state.input_key}")
    apply_rescue_autofocus()
    
    if u_in:
        if u_in.lower().strip() == target['a']:
            st.session_state.training_counts[target['a']] += 1
            st.session_state.last_train_status = "correct"
            st.session_state.show_correct_msg = True
            st.session_state.hint_shown = False
            st.session_state.current_train_word = None 
            st.session_state.input_key += 1
        else:
            st.session_state.last_train_status = "wrong"
            st.session_state.show_correct_msg = False
            st.session_state.input_key += 1 
        st.rerun()

def show_retry():
    target = st.session_state.wrong_target
    if target is None:
        st.session_state.page = 'test'
        st.rerun()
        return
        
    if st.session_state.last_test_status == "retry_correct_step":
        st.success("⭕ 正解！その調子！")
    elif st.session_state.last_test_status == "retry_wrong":
        st.warning(f"❌ お手本をよく見て入力！")

    retry_label = f"⚠️復習({st.session_state.wrong_retry_count}/5回) {target['q']} ⇒ 👉正解：{target['a']}"
    u_in = st.text_input(retry_label, key=f"r_{st.session_state.input_key}")
    apply_rescue_autofocus()
    
    if u_in:
        if u_in.lower().strip() == target['a']:
            st.session_state.wrong_retry_count += 1
            if st.session_state.wrong_retry_count >= 5:
                st.session_state.wrong_target = None
                st.session_state.test_idx += 1 
                st.session_state.last_test_status = None
                st.session_state.page = 'test'
            else:
                st.session_state.last_test_status = "retry_correct_step"
            st.session_state.input_key += 1
        else:
            st.session_state.last_test_status = "retry_wrong"
            st.session_state.input_key += 1
        st.rerun()

def show_test():
    if st.session_state.test_idx >= len(st.session_state.test_queue):
        st.balloons()
        st.success("テストクリア！")
        neta_list = load_data_from_sheets('RewardList')
        if neta_list:
            neta = random.choice(neta_list)
            st.subheader(f"🎁 ご褒美: {neta['title']}")
            st.info(neta['story'])
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
            st.session_state.last_test_status = "test_correct"
            st.session_state.input_key += 1
        else:
            st.session_state.last_test_status = None
            st.session_state.wrong_target = target
            st.session_state.wrong_retry_count = 0
            st.session_state.page = 'retry'
            st.session_state.input_key += 1
        st.rerun()

# メインルーター制御
if not st.session_state.logged_in:
    show_start()
elif st.session_state.page == 'menu':
    show_menu()
elif st.session_state.page == 'train':
    show_train()
elif st.session_state.page == 'retry':
    show_retry()
elif st.session_state.page == 'test':
    show_test()
