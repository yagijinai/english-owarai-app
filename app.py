import streamlit as st
import streamlit.components.v1 as components
import random
import json
import os
import gspread
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials

st.set_page_config(layout="centered", page_title="英単語マスター", page_icon="📝")

# ==========================================
# 【Part 1: バックエンド処理と認証データの合体】
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

# 【完全に埋め込まれた専用の認証キーデータ】
GOOGLE_KEY_DATA = {
    "type": "service_account",
    "project_id": "english-practice-app-495906",
    "private_key_id": "657003817d6f090b778cbdf3c3b33c1cbb981977",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDHsATzN/eB+vni\nIYKmHN1s+Sv987FoZVb/lQIi0MuPu9JM8PoAaze9ihf+MWh+YoMqgENQbkdQJRZ4\nTG2Oi4XQAAtURHv8wX5RUoRJg853I88MdIpMSBtPt1aIkMbKUGJ3VcKaLI9Yq4vU\nVZLJrP1kAjHULS7dSnBwfavguN+1U/N/g5NpP+SUat96xsAjprxs+Lhtn6L/vHRg\nf66nn6ysNsIxSmn5XuhhOCbhIQkh5SRRZbLZ6mFrG7XpB5aB0g8iWbRBG7+f8u62\nkamISPgiLqyEShEG74zcC2L0VbBvU4w3BayXORfM1KTGMjTurNb0vSh5o7Qj5Ty/\np0LcV8RRAgMBAAECggEAFb78ewQwRw5u4gpmMPLZxkFIYiqEumq207SFfAci8+8v\nUsO3Zg5HDrQYMs1spL7Tq/A15G9uArNXRBiGocxd8S3gDfg7TGZB/FcxItRgyqay\nqJeUbAQ6PS8pFEw36dZhMr+7JpENt0lPO/tptd7J5Xc7t/CHtv+hSQ7Whe18J0Hg\n1tcPvSmc0lg/ow1q9CpyrV8nUyqeyh6t03VkAPU5FA1/SYNu4zk3KMhKr3rPG/Tb\nrIpn07bU/5QYeebMYy4NPxh6g7NpjbQQR3fIhaQ/BrSTt+n774dM3GhZxBtUmXgH\nveuU/bAseEre1j4HfBU/F9F69L8lWn0SLJnfnS/ptQKBgQDyzdNSYSgXGXd3E6zK\neyXKAMMyqwza87sQDGDUN+GZvNiGoq2oXV7aTtHxcjNFNno5KZ51PfVc76DvsAMb\nZkESp+71yjhQU5IRktREfNxKDCmsStMk4NVV6tW1uZREGMCxfan49W1P5um0x4Ih\ni6pcK1wB3wWE49sRTqHIriS3GwKBgQDSik60TtCaOXNj+uGk94ukRQu1q4wTT2xS\nEO3pKpP/crOEljoHfsx/ND5pqtlMcm5pQggmrzIBfY6AIk1knktrj3tv8JiQ8JEA\nTvXRUbN2WMA5WMoJixoqLuXA3pqD8owRSIBdCJeDcUtHMHq2Oth4YY2Hg9ZRDWB7\nzP0l2WvNAwKBgAohCAXRw8hi6ZbwHS89P/BTY9FDTX/81vruaUOxKRouxKGpO7Fg\nY8qbqyp1ZyomAadM0y107j14SbB2GUsVUvWiR9e9HehL9DYDeBN7Wf1E0KA9Zt2M\n+5lf+JZiLYtBtRgyc9rM8kh5C5rdD9KybuL1dBsn4KUQlFz+eMVUbnetAoGAcPZq\nUg3zmLv4cI1cYiG7l9C//qJjTr0PdlzE+ZSxwZ5uOVZNHlZnLF0Am7tiScUf/nPC\nYdcgMnKGcbN16OWRu81JQn9JrIKWmh7Df6Khcn8d6+b6x/INgNKWzUvihacuhdtr\nm/8PJCQ2aqTVQk8CdFyLDkmrROOzf9k1fghQ8bcCgYA1iTHU0kS4C//XPldmuQLT\nb+zpEsTH337WCVp4GpI8OoSKJPYvsykrZ0+Rlsy8lkRnP35ZwyEO9OT2YFobwnGN\nnc68FEPh601luBYq+klua+7ifgopZDZMpJPWHNWW7TMK+L78w64r2Q+YbFGRCojb\nQUJCIlRWsCx9h1hcPDSJJQ==\n-----END PRIVATE KEY-----\n",
    "client_email": "english-practice-app@english-practice-app-495906.iam.gserviceaccount.com",
    "client_id": "100283173482304409523",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/english-practice-app%40english-practice-app-495906.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}
# ==========================================
# 【Part 2: スプレッドシート読み込み処理とメニュー画面】
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
    st.markdown(f"### 🔥 連続学習 **{st.session_state.streak_count}** 日目！ すごいです！毎日続けよう！")
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
# 【Part 3: 練習・復習・テスト画面とメインルーター】
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
    st.subheader(f"練習: {target['q']} (現在の正解数: {current_count}/3)")
    
    if st.button("❓ ヒント"):
        st.session_state.hint_shown = True
    if st.session_state.hint_shown:
        st.info(f"正解: {target['a']}")

    if st.session_state.show_correct_msg:
        st.success("⭕ 正解！ 次の単語にすすみます！")
        st.session_state.show_correct_msg = False 
    elif st.session_state.last_train_status == "wrong":
        st.error("❌ つづりが正しくありません！ もう一度入力してみよう。")

    u_in = st.text_input("英語を入力（入力してEnterで判定）:", key=f"t_{st.session_state.input_key}")
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
        
    st.error(f"⚠️ テストで間違えた単語の復習です。5回正解するまで練習しよう！")
    st.info(f"💡 日本語: {target['q']}  |  👉 正解のつづり: **{target['a']}**")
    st.subheader(f"復習入力 ({st.session_state.wrong_retry_count}/5 回成功)")
    
    if st.session_state.last_test_status == "retry_correct_step":
        st.success("⭕ 正解！その調子！")
    elif st.session_state.last_test_status == "retry_wrong":
        st.warning(f"❌ つづりが正しくありません。お手本のつづり【{target['a']}】をよく見て入力しよう！")

    u_in = st.text_input("お手本通りに入力（Enterで判定）:", key=f"r_{st.session_state.input_key}")
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
    st.subheader(f"テスト第 {st.session_state.test_idx + 1} 問: {target['q']}")
    
    if st.session_state.last_test_status == "test_wrong":
        st.error("❌ つづりが正しくありません！")

    u_in = st.text_input("回答を入力（Enterで確定）:", key=f"test_{st.session_state.input_key}")
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
