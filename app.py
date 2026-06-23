import streamlit as st
import streamlit.components.v1 as components
import random
import json
import os
import gspread
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials

# ページ設定
st.set_page_config(layout="centered", page_title="英単語マスター", page_icon="📝")

# CSS設定（上部の余白確保とデザイン調整）
st.markdown("""
    <style>
        .block-container { padding-top: 5.0rem !important; padding-bottom: 0rem !important; }
        h3 { font-size: 1.2rem !important; margin-bottom: 0.5rem !important; }
        div.stButton > button { padding: 0.25rem 0.5rem !important; }
        .stTextInput { margin-top: -10px !important; }
    </style>
""", unsafe_allow_html=True)

# ＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
# 【確定認証データ：最上部配置】
# ＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
# ※以下のプライベートキーや認証情報はご自身の環境のものに書き換えてください
raw_private_key = os.environ.get("GOOGLE_PRIVATE_KEY", "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n")
private_key = raw_private_key.replace('\\n', '\n')

credentials_dict = {
    "type": "service_account",
    "project_id": "your-project-id",
    "private_key_id": "your-private-key-id",
    "private_key": private_key,
    "client_email": "your-service-account-email",
    "client_id": "your-client-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "your-cert-url"
}
# ＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
# スプレッドシート接続・データ取得
# ＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
@st.cache_resource
def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
    return gspread.authorize(creds)

SPREADSHEET_KEY = os.environ.get("SPREADSHEET_KEY", "YOUR_SPREADSHEET_KEY_HERE")

def load_data_from_sheets(sheet_name):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SPREADSHEET_KEY).worksheet(sheet_name)
        return sheet.get_all_records()
    except Exception as e:
        st.error(f"スプレッドシート({sheet_name})の読み込みエラー: {e}")
        return []

def update_learned_status(word_ids):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SPREADSHEET_KEY).worksheet('WordList')
        data = sheet.get_all_records()
        
        updates = []
        for i, row in enumerate(data):
            if row.get('ID') in word_ids:
                row_num = i + 2 # ヘッダー分+1、0始まりで+1
                # Learned 列が何列目か（例としてG列=7とする。環境に合わせて調整してください）
                updates.append({'range': f'G{row_num}', 'values': [['TRUE']]})
        
        if updates:
            sheet.batch_update(updates)
    except Exception as e:
        st.error(f"学習状況の更新に失敗しました: {e}")

def update_user_log(user_id):
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SPREADSHEET_KEY).worksheet('UserLog')
        data = sheet.get_all_records()
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        target_row_idx = None
        user_record = None
        for i, row in enumerate(data):
            if str(row.get('user_id')) == str(user_id):
                target_row_idx = i + 2
                user_record = row
                break
                
        streak = 1
        if user_record:
            last_login = str(user_record.get('last_login_date', ''))
            current_streak = int(user_record.get('streak_count', 0))
            
            if last_login == today_str:
                streak = current_streak # 同日ログインなら維持
            elif last_login == yesterday_str:
                streak = current_streak + 1 # 昨日ログインなら+1
            else:
                streak = 1 # それ以前なら1日にリセット
                
            sheet.update(f'B{target_row_idx}:C{target_row_idx}', [[today_str, streak]])
        else:
            # 新規ユーザー
            sheet.append_row([user_id, today_str, streak])
            
        return streak
    except Exception as e:
        st.error(f"ログイン履歴(UserLog)の更新に失敗しました: {e}")
        return 1
# ＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
# セッション状態初期化・テスト問題生成
# ＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
def apply_rescue_autofocus():
    components.html("""
        <script>
            const inputs = window.parent.document.querySelectorAll('input[type="text"]');
            if (inputs.length > 0) { inputs[inputs.length - 1].focus(); }
        </script>
    """, height=0)

if "page" not in st.session_state:
    st.session_state.page = "menu"
if "train_queue" not in st.session_state:
    st.session_state.train_queue = []
if "test_queue" not in st.session_state:
    st.session_state.test_queue = []
if "train_idx" not in st.session_state:
    st.session_state.train_idx = 0
if "test_idx" not in st.session_state:
    st.session_state.test_idx = 0
if "today_words" not in st.session_state:
    st.session_state.today_words = []
if "input_key" not in st.session_state:
    st.session_state.input_key = 0
if "last_test_status" not in st.session_state:
    st.session_state.last_test_status = "first_try"
if "penalty_count" not in st.session_state:
    st.session_state.penalty_count = 0
if "user_streak" not in st.session_state:
    st.session_state.user_streak = 0
if "user_id" not in st.session_state:
    st.session_state.user_id = "guest_user"

def prepare_test():
    """【新規機能】今日の3問＋過去問2問を混ぜてテストキューを作る"""
    all_words = load_data_from_sheets('WordList')
    today_words = st.session_state.today_words
    today_ids = [w['ID'] for w in today_words]
    
    # すでに学習済み(Learned=TRUE)で、かつ今日の単語ではないものを抽出
    learned_words = [w for w in all_words if str(w.get('Learned', 'FALSE')).upper() == 'TRUE' and w['ID'] not in today_ids]
    
    past_words = []
    # 過去の単語から最大2問をランダムに選出
    if len(learned_words) >= 2:
        past_words = random.sample(learned_words, 2)
    elif len(learned_words) == 1:
        past_words = learned_words
        
    # 今日の単語 + 過去問を合わせてシャッフル
    combined_test = today_words + past_words
    random.shuffle(combined_test)
    
    st.session_state.test_queue = combined_test
    st.session_state.test_idx = 0
    st.session_state.last_test_status = "first_try"
    st.session_state.page = 'test'
# ＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
# 画面表示関数（メニュー・練習）
# ＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
def show_menu():
    st.title("📚 英単語マスター")
    
    if st.button("ログイン＆学習データ読み込み", use_container_width=True):
        st.session_state.user_streak = update_user_log(st.session_state.user_id)
        
        all_words = load_data_from_sheets('WordList')
        # 未学習の単語から3問を選ぶ
        unlearned = [w for w in all_words if str(w.get('Learned', 'FALSE')).upper() != 'TRUE']
        
        if len(unlearned) >= 3:
            today_words = random.sample(unlearned, 3)
        else:
            today_words = unlearned
            
        if not today_words:
            st.success("すべての単語を学習済みです！素晴らしい！")
            return
            
        st.session_state.today_words = today_words
        
        # 1単語につき3回ずつ練習する（計9回）
        queue = []
        for w in today_words:
            queue.extend([w, w, w])
        random.shuffle(queue)
        
        st.session_state.train_queue = queue
        st.session_state.train_idx = 0
        st.session_state.page = 'train'
        st.rerun()

    if st.session_state.user_streak > 0:
        st.info(f"🔥 現在の連続学習記録: {st.session_state.user_streak} 日！")

def show_train():
    if st.session_state.train_idx >= len(st.session_state.train_queue):
        st.success("練習が完了しました！次はテストです。")
        if st.button("テストへ進む", use_container_width=True):
            prepare_test() # ここで今日の問題＋過去問を合体させる関数を呼ぶ
            st.rerun()
        return

    target = st.session_state.train_queue[st.session_state.train_idx]
    st.write(f"### 📖 練習: 【 {target.get('Meaning', '意味')} 】")
    
    # ヒント機能
    with st.expander("💡 ヒントを見る"):
        st.write(f"最初の文字は: **{target.get('Word', '')[0]}**")
    
    u_in = st.text_input("英単語を入力してください:", key=f"train_{st.session_state.input_key}")
    apply_rescue_autofocus()
    
    if u_in:
        if u_in.lower().strip() == target.get('Word', '').lower():
            st.session_state.train_idx += 1
            st.session_state.input_key += 1
            st.rerun()
        else:
            st.error("❌ つづりが違います。もう一度入力してください。")
            st.session_state.input_key += 1
            st.rerun()
# ＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
# テスト画面・誤答時のペナルティ画面
# ＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
def show_test():
    # テストクリア時の処理（ご褒美表示）
    if st.session_state.test_idx >= len(st.session_state.test_queue):
        st.balloons()
        st.success("🎉 全問正解！テストクリア！")
        
        # 学習済みフラグの更新（今日の単語のみ）
        today_ids = [w['ID'] for w in st.session_state.today_words]
        update_learned_status(today_ids)
        
        neta_list = load_data_from_sheets('RewardList')
        if neta_list:
            neta = random.choice(neta_list)
            st.subheader(f"🎁 ご褒美: {neta.get('タイトル', neta.get('title', '豆知識'))}")
            st.info(neta.get('内容', neta.get('story', 'お疲れ様でした！')))
            
            # 在庫数警告
            unused_neta = [n for n in neta_list if str(n.get('Used', 'FALSE')).upper() != 'TRUE']
            if len(unused_neta) <= 10:
                st.warning(f"⚠️ 注意: 残りのご褒美が {len(unused_neta)} 個です！追加してください。")
        
        if st.button("メニューへ戻る", use_container_width=True):
            st.session_state.page = 'menu'
            st.rerun()
        return

    target = st.session_state.test_queue[st.session_state.test_idx]
    
    # 間違えた直後ならペナルティ画面へ移行
    if st.session_state.last_test_status == "test_wrong":
        st.session_state.penalty_count = 0
        st.session_state.page = 'retry'
        st.rerun()

    test_label = f"🔥 テスト第 {st.session_state.test_idx + 1} 問: 【 {target.get('Meaning', '意味')} 】"
    u_in = st.text_input(test_label, key=f"test_{st.session_state.input_key}")
    apply_rescue_autofocus()

    if u_in:
        if u_in.lower().strip() == target.get('Word', '').lower():
            st.session_state.test_idx += 1
            st.session_state.last_test_status = "first_try"
            st.session_state.input_key += 1
            st.rerun()
        else:
            st.error("❌ つづりが正しくありません！")
            st.session_state.last_test_status = "test_wrong"
            st.session_state.input_key += 1
            st.rerun()

def show_retry():
    target = st.session_state.test_queue[st.session_state.test_idx]
    st.error(f"⚠️ テストで間違えました。ペナルティとして正しく5回入力してください。")
    st.info(f"正解の単語: **{target.get('Word', '')}** （{target.get('Meaning', '')}）")
    st.write(f"現在の連続正解数: {st.session_state.penalty_count} / 5 回")

    u_in = st.text_input("正解を見ながら入力:", key=f"retry_{st.session_state.input_key}")
    apply_rescue_autofocus()

    if u_in:
        if u_in.lower().strip() == target.get('Word', '').lower():
            st.session_state.penalty_count += 1
            st.session_state.input_key += 1
            if st.session_state.penalty_count >= 5:
                st.session_state.last_test_status = "first_try"
                st.session_state.page = 'test'
            st.rerun()
        else:
            st.session_state.penalty_count = 0 # 間違えたら0からやり直し
            st.session_state.input_key += 1
            st.rerun()
# ＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
# メインルーチン
# ＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
def main():
    if st.session_state.page == 'menu':
        show_menu()
    elif st.session_state.page == 'train':
        show_train()
    elif st.session_state.page == 'test':
        show_test()
    elif st.session_state.page == 'retry':
        show_retry()

if __name__ == "__main__":
    main()
