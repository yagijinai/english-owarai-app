import streamlit as st
import random

# --- 1. ページ設定 (エラーが出た箇所を修正) ---
st.set_page_config(layout="centered", page_title="英単語練習アプリ")

# --- 2. セッション状態の初期化 ---
def init_session_state():
    # 画面遷移とログイン状態
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'page' not in st.session_state:
        st.session_state.page = "login"
    
    # ユーザー情報
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_name' not in st.session_state:
        st.session_state.user_name = ""
    if 'streak' not in st.session_state:
        st.session_state.streak = 10
    
    # 英単語・入力管理 (AttributeError対策)
    if 'input_key' not in st.session_state:
        st.session_state.input_key = 0
    if 'word_list' not in st.session_state:
        st.session_state.word_list = [
            {"q": "りんご", "a": "apple"}, {"q": "本", "a": "book"},
            {"q": "猫", "a": "cat"}, {"q": "犬", "a": "dog"}
        ]
    if 'current_word' not in st.session_state:
        st.session_state.current_word = st.session_state.word_list[0]
    
    # 判定・ネタ
    if 'feedback' not in st.session_state:
        st.session_state.feedback = ""
    if 'current_neta' not in st.session_state:
        st.session_state.current_neta = ""

init_session_state()

# --- 3. ログイン・ID選択画面 ---
if not st.session_state.logged_in:
    st.title("英単語練習アプリ")
    st.subheader("同じ端末でアプリをスタートしますか？")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("同じIDでつづける", use_container_width=True):
            st.session_state.user_id = "user_777"
            st.session_state.user_name = "お父様"
            st.session_state.logged_in = True  # ここでログイン完了
            st.session_state.page = "main_menu" # 確実にメインメニューへ
            st.rerun()
            
    with col2:
        if st.button("新しいIDではじめる", use_container_width=True):
            st.session_state.user_id = f"user_{random.randint(1000, 9999)}"
            st.session_state.user_name = "新規ユーザー"
            st.session_state.streak = 0
            st.session_state.logged_in = True
            st.session_state.page = "main_menu"
            st.rerun()
    st.stop() # ログインしていない時はここで処理を止める

# --- 4. サイドバー表示 (常に表示) ---
st.sidebar.title("ステータス")
st.sidebar.markdown(f"### 👤 {st.session_state.user_name}")
st.sidebar.markdown(f"### 🔥 連続学習: {st.session_state.streak}日")

# --- 5. メインコンテンツ ---
# メインメニュー画面
if st.session_state.page == "main_menu":
    st.header(f"ようこそ、{st.session_state.user_name}さん")
    st.write("準備ができたら下のボタンを押して練習を始めましょう！")
    
    if st.button("🚀 学習スタート", use_container_width=True):
        st.session_state.page = "training"
        st.session_state.feedback = ""
        st.session_state.current_word = random.choice(st.session_state.word_list)
        st.session_state.input_key += 1
        st.rerun()

# 実際の練習画面
elif st.session_state.page == "training":
    word = st.session_state.current_word
    st.header("✍️ 英単語スペル練習")
    st.subheader(f"「{word['q']}」を英語で書くと？")
    
    user_input = st.text_input("スペルを入力：", key=f"inp_{st.session_state.input_key}").strip().lower()
    
    if st.button("判定する", use_container_width=True):
        if user_input == word['a']:
            st.session_state.feedback = "correct"
        else:
            st.error("おしい！スペルを確認してみて。")

    if st.session_state.feedback == "correct":
        st.success(f"正解！ 答えは **{word['a'].upper()}** です！")
        if st.button("次へ（豆知識を見る）", use_container_width=True):
            st.session_state.streak += 1
            neta_list = [
                "サンドウィッチマン伊達：カステラはギュッと潰せばカロリーも潰れるから0キロカロリー。",
                "千鳥ノブ：昔、番組の企画で『ノブ小池』に改名させられ、1ヶ月間その名前で活動した。"
            ]
            st.session_state.current_neta = random.choice(neta_list)
            st.session_state.page = "result"
            st.rerun()

# --- 6. 結果・豆知識画面 ---
elif st.session_state.page == "result":
    st.header("お見事！ 🎉")
    st.balloons()
    
    st.subheader("💡 今日の芸人豆知識")
    st.info(st.session_state.current_neta)
    
    if st.button("もう一度練習する", use_container_width=True):
        st.session_state.page = "main_menu"
        st.rerun()
