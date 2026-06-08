import streamlit as st
import streamlit.components.v1 as components
import random
import json
import os
import gspread
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials

# ページ基本設定
st.set_page_config(layout="centered", page_title="英単語マスター", page_icon="📝")

# バグ排除のためのCSS調整（paddingを広げて表示のズレを防止）
st.markdown("""
<style>
h3 { font-size: 1.2rem !important; margin-bottom: 0.5rem !important; }
div.stButton > button { padding: 0.25rem 0.5rem !important; }
.stTextInput { margin-top: -10px !important; }
</style>
""", unsafe_allow_html=True)
def get_gspread_client():
    """Streamlit Secretsから認証情報を取得し、Googleスプレッドシートへ接続する"""
    try:
        # st.secrets の GOOGLE_SECRET から認証データを取得
        secret_info = json.loads(st.secrets["GOOGLE_SECRET"])
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        credentials = Credentials.from_service_account_info(secret_info, scopes=scopes)
        gc = gspread.authorize(credentials)
        return gc
    except Exception as e:
        st.error(f"Google接続認証エラー: {e}")
        st.info("StreamlitのSecretsに 'GOOGLE_SECRET' が正しく設定されているか確認してください。")
        return None
# スプレッドシートのURL（お使いの環境に合わせて書き換えてください）
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1C42Lw_Vn_m6A-LptwP6Nf71iR8Y34H_5B6n77u0z3c4/edit"

def load_data_from_sheets(sheet_name, selected_grade="中2"):
    """スプレッドシートから各シートのデータを読み込む"""
    gc = get_gspread_client()
    if not gc:
        return []
    
    try:
        sh = gc.open_by_url(SPREADSHEET_URL)
        worksheet = sh.worksheet(sheet_name)
        all_records = worksheet.get_all_values()
        if not all_records:
            return []
            
        data = []
        rows = all_records[1:] # ヘッダーをスキップ
        
        if sheet_name == "RewardList":
            for row in rows:
                if len(row) >= 4:
                    title_val = row[2].strip()
                    story_val = row[3].strip()
                    # E列(インデックス4)に使用済みフラグ(TRUE/FALSE)があると想定
                    used_val = row[4].strip().upper() if len(row) >= 5 else "FALSE"
                    
                    if title_val and title_val != "タイトル" and story_val:
                        data.append({
                            "title": title_val, 
                            "story": story_val,
                            "used": used_val
                        })
            return data
            
        elif sheet_name == "WordList":
            grade_str = "1"
            if selected_grade == "中2": grade_str = "2"
            elif selected_grade == "中3": grade_str = "3"
            
            for row in rows:
                if len(row) >= 5:
                    word_val = row[1].strip()
                    meaning_val = row[2].strip()
                    grade_val = row[4].strip()
                    # J列(インデックス9)がLearnedフラグ
                    learned_val = row[9].strip().upper() if len(row) >= 10 else "FALSE"
                    
                    if grade_val == grade_str and word_val and meaning_val and learned_val == "FALSE":
                        data.append({
                            "grade": selected_grade,
                            "q": meaning_val,
                            "a": word_val.lower().strip()
                        })
            return data
    except Exception as e:
        st.error(f"データ読み込みエラー ({sheet_name}): {e}")
        return []

def update_login_streak(user_id):
    """UserLogシートを用いて、連続学習日数を厳格に計算・更新する"""
    gc = get_gspread_client()
    if not gc:
        return 1
    try:
        sh = gc.open_by_url(SPREADSHEET_URL)
        worksheet = sh.worksheet("UserLog")
        all_cells = worksheet.get_all_values()
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        user_row_idx = -1
        last_login = ""
        streak = 1
        
        # 既存ユーザーの探索
        for idx, row in enumerate(all_cells):
            if idx == 0: continue
            if row[0] == user_id:
                user_row_idx = idx + 1
                last_login = row[1]
                streak = int(row[2])
                break
                
        if user_row_idx != -1:
            if last_login == today_str:
                # 今日すでにログイン済みの場合は日数を維持
                pass
            elif last_login == yesterday_str:
                # 昨日ログインしていた場合は日数を+1
                streak += 1
                worksheet.update_cell(user_row_idx, 2, today_str)
                worksheet.update_cell(user_row_idx, 3, str(streak))
            else:
                # 一一昨日以前、または途切れた場合は1にリセット
                streak = 1
                worksheet.update_cell(user_row_idx, 2, today_str)
                worksheet.update_cell(user_row_idx, 3, str(streak))
        else:
            # 新規ユーザーの追加
            streak = 1
            worksheet.append_row([user_id, today_str, "1"])
            
        return streak
    except Exception as e:
        st.error(f"連続学習日数更新エラー: {e}")
        return 1
# 各種状態を保持するセッションの初期化
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'user_id' not in st.session_state:
    st.session_state.user_id = ''
if 'streak' not in st.session_state:
    st.session_state.streak = 1
if 'train_queue' not in st.session_state:
    st.session_state.train_queue = []
if 'train_idx' not in st.session_state:
    st.session_state.train_idx = 0
if 'test_queue' not in st.session_state:
    st.session_state.test_queue = []
if 'test_idx' not in st.session_state:
    st.session_state.test_idx = 0
if 'input_key' not in st.session_state:
    st.session_state.input_key = 0
if 'hint_shown' not in st.session_state:
    st.session_state.hint_shown = False
if 'last_train_status' not in st.session_state:
    st.session_state.last_train_status = 'normal'
if 'last_test_status' not in st.session_state:
    st.session_state.last_test_status = 'normal'
if 'show_correct_msg' not in st.session_state:
    st.session_state.show_correct_msg = False

# PDF要件: 誤答時のペナルティ5回練習用セッション状態
if 'penalty_mode' not in st.session_state:
    st.session_state.penalty_mode = False
if 'penalty_word' not in st.session_state:
    st.session_state.penalty_word = None
if 'penalty_count' not in st.session_state:
    st.session_state.penalty_count = 0

def apply_rescue_autofocus():
    """入力欄への自動フォーカスをアシストするコンポーネント"""
    components.html(
        f"""
        <script>
        window.parent.document.querySelectorAll('input[type="text"]').forEach(el => {{
            el.focus();
        }});
        </script>
        """, height=0, width=0
    )
def show_login():
    st.title("🔑 ログイン画面")
    u_id = st.text_input("GoogleアカウントまたはユーザーIDを入力してください:", key="user_login_input")
    if st.button("ログイン", use_container_width=True):
        if u_id.strip():
            st.session_state.user_id = u_id.strip()
            # ログイン時、連続学習日数を集計・更新してセッションへ格納
            st.session_state.streak = update_login_streak(st.session_state.user_id)
            st.session_state.page = 'menu'
            st.rerun()
        else:
            st.error("ユーザーIDを入力してください。")

def show_menu():
    st.title("📝 メニュー画面")
    st.success(f"🔥 ようこそ！現在の連続学習日数: **{st.session_state.streak}日目** です！")
    
    grade = st.selectbox("学習する学年を選択してください:", ["中1", "中2", "中3"])
    
    if st.button("🏃 英単語練習をスタート (1日3単語)", use_container_width=True):
        with st.spinner("単語を読み込んでいます..."):
            words = load_data_from_sheets("WordList", grade)
            if len(words) < 3:
                st.warning("未学習の単語が足りないか、すべてマスターしています！")
                # 動作確認用に取得できた分だけ進むか、リセットを促す
                if not words: return
                selected = words
            else:
                # 1日3つを選出
                selected = random.sample(words, min(3, len(words)))
            
            # 各単語3回ずつ、ランダムに並べた計9回の練習キューを作成
            queue = selected * 3
            random.shuffle(queue)
            
            st.session_state.train_queue = queue
            st.session_state.train_idx = 0
            # テスト用に当日分3問のリストを保管
            st.session_state.test_queue = selected
            st.session_state.test_idx = 0
            st.session_state.page = 'train'
            st.session_state.last_train_status = 'normal'
            st.session_state.hint_shown = False
            st.rerun()

def show_train():
    if st.session_state.train_idx >= len(st.session_state.train_queue):
        st.balloons()
        st.success("🎉 本日の練習サイクル完了！次は復習テストです！")
        if st.button("🎯 復習テストに進む", use_container_width=True):
            st.session_state.page = 'test'
            st.session_state.last_test_status = 'normal'
            st.session_state.penalty_mode = False
            st.rerun()
        return

    target = st.session_state.train_queue[st.session_state.train_idx]
    st.title("🏃 英単語練習サイクル")
    st.subheader(f"第 {st.session_state.train_idx + 1} / {len(st.session_state.train_queue)} 問")
    
    # 状況に応じたメッセージ表示
    if st.session_state.show_correct_msg:
        st.success("⭕ 正解！ 次の単語へ進みます。")
        st.session_state.show_correct_msg = False
    elif st.session_state.last_train_status == "wrong":
        st.error("❌ つづりが違います。もう一度入力してみよう！")

    input_label = f"【問題】 次の意味の英単語を小文字で入力: 『 {target['q']} 』"
    if st.session_state.hint_shown:
        # ヒント機能：最初の1文字を表示
        input_label += f"  (ヒント: 最初は '{target['a'][0]}' で始まります)"

    u_in = st.text_input(input_label, key=f"train_{st.session_state.input_key}")
    apply_rescue_autofocus()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💡 ヒントを表示", use_container_width=True):
            st.session_state.hint_shown = True
            st.rerun()
    with col2:
        if st.button("🔄 パスして次へ", use_container_width=True):
            st.session_state.train_idx += 1
            st.session_state.hint_shown = False
            st.session_state.last_train_status = 'normal'
            st.session_state.input_key += 1
            st.rerun()

    if u_in:
        if u_in.lower().strip() == target['a']:
            st.session_state.train_idx += 1
            st.session_state.show_correct_msg = True
            st.session_state.last_train_status = 'normal'
            st.session_state.hint_shown = False
        else:
            st.session_state.last_train_status = 'wrong'
        st.session_state.input_key += 1
        st.rerun()
def show_test():
    st.title("🎯 復習テスト画面")
    
    # ----------------------------------------------------
    # PDF要件: 誤答したその場での「5回練習ペナルティループ」処理
    # ----------------------------------------------------
    if st.session_state.penalty_mode:
        p_target = st.session_state.penalty_word
        st.error(f"🔥 ペナルティモード: つづりミス！あと {5 - st.session_state.penalty_count} 回正解するまでテストに戻れません。")
        st.subheader(f"対象単語: 【 {p_target['q']} 】 正解のつづり: 『 {p_target['a']} 』")
        
        p_in = st.text_input(f"正解を正しく入力してください ({st.session_state.penalty_count + 1}回目):", key=f"penalty_{st.session_state.input_key}")
        apply_rescue_autofocus()
        
        if p_in:
            if p_in.lower().strip() == p_target['a']:
                st.session_state.penalty_count += 1
                if st.session_state.penalty_count >= 5:
                    st.success("👍 5回の練習をクリアしました！テストを再開します。")
                    st.session_state.penalty_mode = False
                    st.session_state.last_test_status = 'normal'
            else:
                st.error("❌ つづりが違います。連続カウントがリセットされます。")
                st.session_state.penalty_count = 0 # 間違えたら0回からやり直し
            st.session_state.input_key += 1
            st.rerun()
        return

    # テスト全問クリア時の処理
    if st.session_state.test_idx >= len(st.session_state.test_queue):
        st.balloons()
        st.success("🎉 テストクリア！おめでとうございます！")
        
        # ごほうびデータの読み込み
        neta_list = load_data_from_sheets('RewardList')
        if neta_list:
            # 在庫数カウント（FALSEの数を計算）
            unused_rewards = [r for r in neta_list if r.get('used') == 'FALSE']
            neta = random.choice(neta_list)
            
            st.subheader(f"🎁 ご褒美豆知識: {neta['title']}")
            st.info(neta['story'])
            
            # PDF要件: 残りが10個以下になったら「褒美は残り◯個になりました」と警告を表示
            if len(unused_rewards) <= 10:
                st.warning(f"⚠️ 警告: 褒美（ごほうび）は残り {len(unused_rewards)} 個になりました！")
        
        if st.button("🏠 メニューへ戻る", use_container_width=True):
            st.session_state.page = 'menu'
            st.rerun()
        return

    # 通常のテスト問題処理
    target = st.session_state.test_queue[st.session_state.test_idx]
    test_label = f"🔥 テスト第 {st.session_state.test_idx + 1} 問 / {len(st.session_state.test_queue)} 問: 【 {target['q']} 】"
    
    u_in = st.text_input(test_label, key=f"test_{st.session_state.input_key}")
    apply_rescue_autofocus()
    
    if u_in:
        if u_in.lower().strip() == target['a']:
            st.session_state.test_idx += 1
            st.session_state.last_test_status = 'correct'
        else:
            # 間違えた場合、その場で5回練習ペナルティモードを起動
            st.session_state.penalty_mode = True
            st.session_state.penalty_word = target
            st.session_state.penalty_count = 0
            st.session_state.last_test_status = 'wrong'
            
        st.session_state.input_key += 1
        st.rerun()

# --- メイン実行制御（マルチページ・ルーティング） ---
if st.session_state.page == 'login':
    show_login()
elif st.session_state.page == 'menu':
    show_menu()
elif st.session_state.page == 'train':
    show_train()
elif st.session_state.page == 'test':
    show_test()
