import streamlit as st
import random

# --- 1. ページ設定 (エラー修正済み) ---
st.set_page_config(layout="centered", page_title="学習アプリ")

# --- 2. セッション状態の初期化 (AttributeError対策) ---
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

# --- 5. メインコンテンツ（ページ管理） ---
if st.session_state.page == "login":
    st.header("ログイン完了")
    st.write(f"おかえりなさい、{st.session_state.user_name}さん！")
    
    # Pixel 7で反応を良くするため、直接セッション値を書き換える
    if st.button("🚀 学習スタート", use_container_width=True):
        st.session_state.page = "training"
        st.rerun()

elif st.session_state.page == "training":
    st.header("✍️ 練習画面")
    st.write("ここに学習コンテンツが入ります。")
    
    # 学習完了処理
    if st.button("学習を完了する", use_container_width=True):
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
    st.success("学習お疲れ様でした！")
    st.balloons()
    
    st.subheader("💡 今日の芸人豆知識")
    st.info(st.session_state.current_neta)
    
    if st.button("マイページへ戻る", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()
