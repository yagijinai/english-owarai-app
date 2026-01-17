import streamlit as st
import random

# --- 1. ページ設定 ---
st.set_page_config(layout="centered", page_title="英単語練習アプリ")

# --- 2. セッション状態の初期化 ---
def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'page' not in st.session_state:
        st.session_state.page = "login"
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_name' not in st.session_state:
        st.session_state.user_name = ""
    if 'streak' not in st.session_state:
        st.session_state.streak = 10  # デフォルト値
    
    # 英単語練習用の状態
    if 'word_list' not in st.session_state:
        # 練習したい単語リスト（ここを自由に入れ替えられます）
        st.session_state.word_list = [
            {"q": "りんご", "a": "apple"},
            {"q": "本", "a": "book"},
            {"q": "猫", "a": "cat"},
            {"q": "犬", "a": "dog"},
            {"q": "幸福な", "a": "happy"}
        ]
    if 'current_word' not in st.session_state:
        st.session_state.current_word = random.choice(st.session_state.word_list)
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
            st.session_state.logged_in = True
            st.rerun()
            
    with col2:
        if st.button("新しいIDではじめる", use_container_width=True):
            st.session_state.user_id = f"user_{random.randint(1000, 9999)}"
            st.session_state.user_name = "新規ユーザー"
            st.session_state.streak = 0
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# --- 4. サイドバー表示 ---
st.sidebar.title("ステータス")
st.sidebar.write(f"👤 {st.session_state.user_name}")
st.sidebar.write(f"🔥 連続学習: {st.session_state.streak}日")

# --- 5. メインコンテンツ ---
if st.session_state.page == "login":
    st.header("準備はいいですか？")
    if st.button("🚀 学習スタート", use_container_width=True):
        st.session_state.page = "training"
        st.session_state.feedback = ""
        st.session_state.current_word = random.choice(st.session_state.word_list)
        # 入力欄をクリアするためのキーを生成
        if 'input_key' not in st.session_state:
            st.session_state.input_key = 0
        st.session_state.input_key += 1
        st.rerun()

elif st.session_state.page == "training":
    st.header("✍️ スペル練習")
    word = st.session_state.current_word
    st.subheader(f"「{word['q']}」を英語で書くと？")
    
    # テキスト入力（Pixel 7で入力しやすいよう自動修正オフを推奨するがStreamlitでは標準入力）
    user_input = st.text_input("スペルを入力：", key=f"input_{st.session_state.input_key}").strip().lower()
    
    if st.button("判定する", use_container_width=True):
        if user_input == word['a']:
            st.session_state.feedback = "correct"
        else:
            st.session_state.feedback = "wrong"
    
    if st.session_state.feedback == "correct":
        st.success(f"正解！ {word['a'].upper()}")
        if st.button("次へ進んで豆知識を見る", use_container_width=True):
            st.session_state.streak += 1
            neta_list = [
                "サンドウィッチマン伊達の『カロリーゼロ理論』では、ドーナツは形が0なので0キロカロリー。",
                "千鳥ノブは、昔『ノブ小池』という芸名にされかけたが、全力で拒否した。",
                "出川哲朗の口癖『ヤバいよヤバいよ』は、実はリアルに焦っている時にしか出ない。"
            ]
            st.session_state.current_neta = random.choice(neta_list)
            st.session_state.page = "result"
            st.rerun()
    elif st.session_state.feedback == "wrong":
        st.error("おしい！もう一度入力してみて。")

# --- 6. 結果・豆知識画面 ---
elif st.session_state.page == "result":
    st.header("Great Job! 🎉")
    st.balloons()
    
    st.subheader("💡 今日のお笑い芸人豆知識")
    st.info(st.session_state.current_neta)
    
    if st.button("もう一問 練習する", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()
