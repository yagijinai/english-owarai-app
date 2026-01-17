import streamlit as st
import random

# --- 1. ページ設定 ---
st.set_page_config(layout="centered", page_title="学習アプリ")

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
        st.session_state.streak = 0
    if 'current_neta' not in st.session_state:
        st.session_state.current_neta = ""
    # 練習用の状態保持
    if 'answer_submitted' not in st.session_state:
        st.session_state.answer_submitted = False
    if 'user_answer' not in st.session_state:
        st.session_state.user_answer = ""

init_session_state()

# --- 3. ログイン・ID選択画面 ---
if not st.session_state.logged_in:
    st.title("学習アプリ")
    st.subheader("同じ端末でアプリをスタートしますか？")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("同じIDでつづける", use_container_width=True):
            st.session_state.user_id = "user_777"
            st.session_state.user_name = "お父様"
            st.session_state.streak = 10
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

# --- 4. サイドバー表示 (常に表示) ---
st.sidebar.title("マイステータス")
st.sidebar.markdown(f"### 👤 {st.session_state.user_name}")
st.sidebar.markdown(f"### 🔥 連続学習: {st.session_state.streak}日")

# --- 5. メインコンテンツ ---
if st.session_state.page == "login":
    st.header("おかえりなさい！")
    if st.button("🚀 学習スタート", use_container_width=True):
        st.session_state.page = "training"
        st.session_state.answer_submitted = False
        st.session_state.user_answer = ""
        st.rerun()

elif st.session_state.page == "training":
    st.header("✍️ 練習入力")
    st.write("今日の課題を入力してください。")
    
    # 練習入力フォーム
    user_input = st.text_input("ここに入力：", value=st.session_state.user_answer)
    
    if st.button("回答を送信", use_container_width=True):
        if user_input:
            st.session_state.user_answer = user_input
            st.session_state.answer_submitted = True
        else:
            st.warning("何か入力してください。")

    # 送信後の処理
    if st.session_state.answer_submitted:
        st.success(f"入力内容を確認しました： {st.session_state.user_answer}")
        
        if st.button("学習を完了して豆知識を見る", use_container_width=True):
            # 完了処理
            st.session_state.streak += 1
            neta_list = [
                "サンドウィッチマンの伊達は、カロリーは熱に弱いから揚げ物は0キロカロリーだと言い張っている。",
                "千鳥のノブは、昔『ノブ小池』に改名させられそうになったことがある。",
                "出川哲朗は、実は実家が老舗の海苔問屋のお金持ちである。"
            ]
            st.session_state.current_neta = random.choice(neta_list)
            st.session_state.page = "result"
            st.rerun()

# --- 6. 結果・豆知識画面 ---
elif st.session_state.page == "result":
    st.success("学習完了！")
    st.balloons()
    
    st.subheader("💡 今日の芸人豆知識")
    st.info(st.session_state.current_neta)
    
    # このボタンで最初に戻れば、一日に何度でも練習から始められます
    if st.button("もう一度練習する / 戻る", use_container_width=True):
        st.session_state.page = "login"
        st.session_state.answer_submitted = False
        st.session_state.user_answer = ""
        st.rerun()
