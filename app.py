import streamlit as st
import streamlit.components.v1 as components
import random
import json
import gspread
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials

# ページ設定
st.set_page_config(layout="centered", page_title="英単語マスター", page_icon="📝")

# CSSによるレイアウト調整（バグ排除と余白確保）
st.markdown("""
<style>
h3 { font-size: 1.2rem !important; margin-bottom: 0.5rem !important; }
div.stButton > button { padding: 0.25rem 0.5rem !important; }
.stTextInput { margin-top: -10px !important; }
.reportview-container .main .block-container { padding-top: 9.0rem !important; }
</style>
""", unsafe_allow_html=True)
# ==========================================
# 【認証データ設定】
# ※スプレッドシート接続用の鍵情報は st.secrets["GOOGLE_SECRET"] から読み込みます
# ==========================================
def get_gspread_client():
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        # st.secrets からサービスアカウント情報を取得
        if "GOOGLE_SECRET" in st.secrets:
            key_data = json.loads(st.secrets["GOOGLE_SECRET"])
        else:
            st.error("StreamlitのSecretsに 'GOOGLE_SECRET' が設定されていません。")
            return None
            
        creds = Credentials.from_service_account_info(key_data, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Google認証エラー: {str(e)}")
        return None

# ==========================================
# 【セッション状態の初期化】
# ==========================================
def init_session():
    if 'page' not in st.session_state:
        st.session_state.update({
            'page': 'start',
            'logged_in': False,
            'grade': "中2",
            'user_id': "daughter_user",  # 固定ID（必要に応じて可変にしてください）
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
# ==========================================
# 【連続学習日数（ストリーク）管理システム】
# Firestoreを使わず、スプレッドシートの「UserLog」シートで日数を管理します
# ==========================================
def update_login_streak_via_sheet(user_id):
    client = get_gspread_client()
    if client is None:
        return 1
        
    try:
        spreadsheet = client.open("英単語学習アプリ")
        
        # ログイン記録用シート「UserLog」を開く
        try:
            worksheet = spreadsheet.worksheet("UserLog")
        except gspread.exceptions.WorksheetNotFound:
            st.error("スプレッドシートに『UserLog』シートが見つかりません。シート名を確認してください。")
            return 1
            
        all_records = worksheet.get_all_values()
        
        today_str = datetime.now().strftime('%Y-%m-%d')
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        user_row_idx = None
        last_login = ""
        current_streak = 1
        
        # 2行目以降から該当ユーザーを検索（A列: user_id, B列: last_login_date, C列: streak_count）
        if len(all_records) > 1:
            for idx, row in enumerate(all_records[1:], start=2):
                if row[0].strip() == user_id:
                    user_row_idx = idx
                    last_login = row[1].strip() if len(row) > 1 else ""
                    current_streak = int(row[2].strip()) if len(row) > 2 and row[2].strip().isdigit() else 1
                    break
        
        # ストリーク判定
        if user_row_idx:
            if last_login == today_str:
                # 同日内の再アクセス：日数を維持
                new_streak = current_streak
            elif last_login == yesterday_str:
                # 前日からの継続アクセス：日数を+1してシートを更新
                new_streak = current_streak + 1
                worksheet.update_cell(user_row_idx, 2, today_str)
                worksheet.update_cell(user_row_idx, 3, str(new_streak))
            else:
                # 一おととい以前、または日数が途切れた場合：1日にリセットして更新
                new_streak = 1
                worksheet.update_cell(user_row_idx, 2, today_str)
                worksheet.update_cell(user_row_idx, 3, "1")
        else:
            # 新規ユーザーの場合：新しく行を追加
            new_streak = 1
            worksheet.append_row([user_id, today_str, "1"])
            
        return new_streak
        
    except Exception as e:
        st.error(f"ログイン日数更新エラー: {str(e)}")
        return 1
# ==========================================
# 【データ読み込み機能】
# ==========================================
def load_data_from_sheets(sheet_name, selected_grade=None):
    data = []
    client = get_gspread_client()
    if client is None:
        return data
        
    try:
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
        st.error(f"スプレッドシート通信エラー ({sheet_name}): {str(e)}")
        return data

# ==========================================
# 【入力欄の自動フォーカス】
# ==========================================
def apply_rescue_autofocus():
    components.html(
        """
        <script>
        (function() {
            var doc = window.parent.document;
            function grabFocus() {
                var inputs = doc.querySelectorAll('input[type="text"]');
                if (inputs.length > 0) {
                    var targetInput = inputs[inputs.length - 1];
                    if (doc.activeElement !== targetInput) {
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
            st.session_state.streak_count = update_login_streak_via_sheet(st.session_state.user_id)
            st.session_state.page = 'menu'
            st.rerun()
            
    with col2:
        if st.button("新しいIDではじめる", use_container_width=True):
            st.session_state.start_mode = "new"
            st.session_state.logged_in = True
            st.session_state.streak_count = update_login_streak_via_sheet(st.session_state.user_id)
            st.session_state.page = 'menu'
            st.rerun()

def show_menu():
    st.title("メインメニュー")
    st.markdown(f"### 🔥 連続学習 {st.session_state.streak_count} 日目！")
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
    
    if st.button("❓ ヒントをみる", key="hint_btn", use_container_width=True):
        st.session_state.hint_shown = True
        
    if st.session_state.show_correct_msg:
        st.success("⭕ 正解！ 次へ！")
        st.session_state.show_correct_msg = False
    elif st.session_state.last_train_status == "wrong":
        st.error("❌ もう一度入力してみよう。")
        
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
