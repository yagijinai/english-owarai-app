import streamlit as st
import random

# --- 1. ページ設定 (正しい関数名に修正) ---
st.set_page_config(layout="centered", page_title="英単語練習アプリ")

# --- 2. セッション状態の初期化 (すべての変数をここで網羅) ---
def init_session_state():
    # ログイン状態
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
    
    # 英単語データと入力キー（エラーの直接原因をここで解決）
    if 'input_key' not in st.session_state:
        st.session_state.input_key = 0
    if 'word_list' not in st.session_state:
        st.session_state.word_list = [
            {"q": "りんご", "a": "apple"},
            {"q": "本", "a": "book"},
            {"q": "猫", "a": "cat"},
            {"q": "犬", "a": "dog"},
            {"q": "幸福な", "a": "happy"}
        ]
    if 'current_word' not in st.session_state:
        st.session_state.current_word = st.session_state.word_list[0]
    
    # 判定・ネタ関連
    if 'feedback' not in st.session_state:
        st.session_state.feedback = ""
    if 'current_neta' not in st.session_state:
        st.session_state.current_neta = ""

# 初期化を実行
init_session_state()

# --- 3. ログイン・ID選択画面 ---
if not st.session_state.logged_in:
    st.title("英単語練習アプリ")
    st.write("同じ端末でアプリをスタートしますか？")
    
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
        st.session_state.input_key += 1 # 毎回入力欄をリフレッシュ
        st.rerun()

elif st.session_state.page == "training":
    st.header("✍️ スペル練習")
    word = st.session_state.current_word
    st.subheader(f"「{word['q']}」を英語で書くと？")
    
    # 画像2のエラーを解決した入力欄
    user_input = st.text_input(
        "ここに入力してください：", 
        key=f"input_{st.session_state.input_key}"
    ).strip().lower()
    
    if st.button("判定する", use_container_width=True):
        if user_input == word['a']:
            st.session_state.feedback = "correct"
        else:
            st.session_state.feedback = "wrong"
            st.error("おしい！スペルを確認してみて。")

    if st.session_state.feedback == "correct":
        st.success(f"正解！ 答えは {word['a'].upper()} です。")
        if st.button("次へ進んで豆知識を見る", use_container_width=True):
            st.session_state.streak += 1
            neta_list = [
                "サンドウィッチマン伊達の持論：カロリーは足が速いから逃げていく。",
                "千鳥ノブの嘆き：昔『ノブ小池』に改名させられそうになった時が一番辛かった。",
                "出川哲朗の家系：実は100年以上続く横浜の老舗海苔問屋の御曹司。"
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
    
    if st.button("もう一問 練習する", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()
