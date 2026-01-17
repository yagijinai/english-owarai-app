import streamlit as st
import random

# 1. ページ設定（スマホで見やすいよう中央寄せ）
st.set_config(layout="centered", page_title="学習アプリ")

# 2. セッション状態の初期化 (AttributeError対策)
def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'page' not in st.session_state:
        st.session_state.page = "login"  # 画面遷移管理用
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
    st.write("同じ端末でアプリをスタートしますか？")
    
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
st.sidebar.title("MENU")
st.sidebar.write(f"👤 **{st.session_state.user_name}** さん")
st.sidebar.write(f"🔥 連続学習: **{st.session_state.streak}日**")

# --- 5. メインコンテンツの切り替え ---
# 「学習スタート」を押した後に画面が切り替わるよう st.session_state.page で管理します
if st.session_state.page == "login":
    st.header("ログインしました")
    st.write("今日の学習を始めましょう。")
    
    if st.button("🚀 学習スタート", use_container_width=True):
        st.session_state.page = "training" # 練習ページへ切り替え
        st.rerun()

elif st.session_state.page == "training":
    st.header("✍️ 練習中...")
    st.write("ここが学習・練習のメイン画面です。")
    
    # 練習完了後の処理
    if st.button("学習を完了する", use_container_width=True):
        st.session_state.streak += 1
        neta_list = [
            "サンドウィッチマンの伊達は、カロリーは熱に弱いから揚げ物は0キロカロリーだと言い張っている。",
            "千鳥のノブは、昔『ノブ小池』に改名させられそうになったことがある。"
        ]
        st.session_state.current_neta = random.choice(neta_list)
        st.session_state.page = "result"
        st.rerun()

# --- 6. 結果・豆知識画面 ---
elif st.session_state.page == "result":
    st.success("学習完了！おめでとうございます！")
    st.balloons()
    
    st.subheader("💡 今日の芸人豆知識")
    st.info(st.session_state.current_neta)
    
    if st.button("トップに戻る", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()
