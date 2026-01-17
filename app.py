import streamlit as st
import random

# --- 1. ページ設定 (正しい関数名) ---
st.set_page_config(layout="centered", page_title="英単語練習アプリ")

# --- 2. セッション状態の初期化 ---
def init_session_state():
    # 画面の状態管理
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'page' not in st.session_state: st.session_state.page = "login"
    
    # ユーザー情報
    if 'user_name' not in st.session_state: st.session_state.user_name = "お父様"
    if 'streak' not in st.session_state: st.session_state.streak = 10
    
    # 単語マスターリスト（ここから問題が出ます）
    if 'master_words' not in st.session_state:
        st.session_state.master_words = [
            {"q": "りんご", "a": "apple"}, {"q": "本", "a": "book"},
            {"q": "猫", "a": "cat"}, {"q": "犬", "a": "dog"},
            {"q": "鳥", "a": "bird"}, {"q": "卵", "a": "egg"},
            {"q": "太陽", "a": "sun"}, {"q": "月", "a": "moon"}
        ]
    
    # 練習とテストの進捗 (IndexError対策のため空にしない)
    if 'session_words' not in st.session_state:
        st.session_state.session_words = st.session_state.master_words[:3]
    if 'test_words' not in st.session_state:
        st.session_state.test_words = st.session_state.master_words[:4]
    if 'word_index' not in st.session_state: st.session_state.word_index = 0
    if 'repeat_count' not in st.session_state: st.session_state.repeat_count = 1
    
    # 特訓（ペナルティ）管理
    if 'penalty_word' not in st.session_state: st.session_state.penalty_word = None
    if 'penalty_count' not in st.session_state: st.session_state.penalty_count = 0
    
    # 入力フォームリセット用
    if 'input_key' not in st.session_state: st.session_state.input_key = 0
    if 'current_neta' not in st.session_state: st.session_state.current_neta = ""

# 初期化実行
init_session_state()

# --- 3. ログイン画面 ---
if not st.session_state.logged_in:
    st.title("英単語練習アプリ")
    st.subheader("同じ端末でアプリをスタートしますか？")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("同じIDでつづける", use_container_width=True):
            st.session_state.user_name = "お父様"
            st.session_state.logged_in = True
            st.session_state.page = "main_menu" # 確実にメインメニューへ
            st.rerun()
            
    with col2:
        if st.button("新しいIDではじめる", use_container_width=True):
            st.session_state.user_name = "新規ユーザー"
            st.session_state.streak = 0
            st.session_state.logged_in = True
            st.session_state.page = "main_menu"
            st.rerun()
    st.stop()

# --- 4. サイドバー (常に表示) ---
st.sidebar.markdown(f"### 👤 {st.session_state.user_name}")
st.sidebar.markdown(f"### 🔥 連続学習: {st.session_state.streak}日")

# --- 5. メインメニュー ＆ 練習ロジック ---
if st.session_state.page == "main_menu":
    st.header("今日の練習メニュー")
    st.write("3つの単語を3回ずつ書いて覚えましょう！")
    if st.button("🚀 学習スタート", use_container_width=True):
        st.session_state.session_words = random.sample(st.session_state.master_words, 3)
        st.session_state.word_index = 0
        st.session_state.repeat_count = 1
        st.session_state.page = "training"
        st.rerun()

elif st.session_state.page == "training":
    idx = st.session_state.word_index
    rep = st.session_state.repeat_count
    word = st.session_state.session_words[idx]
    
    st.header(f"練習 {idx+1}/3 ({rep}回目)")
    st.subheader(f"「{word['q']}」のスペルは？")
    u_in = st.text_input("入力:", key=f"t_{st.session_state.input_key}").strip().lower()
    
    if st.button("判定", use_container_width=True):
        if u_in == word['a']:
            st.session_state.input_key += 1
            if st.session_state.repeat_count < 3:
                st.session_state.repeat_count += 1
            else:
                st.session_state.repeat_count = 1
                st.session_state.word_index += 1
            
            if st.session_state.word_index >= 3:
                # 復習テストの準備 (今日の3語 + 過去1語)
                past = random.choice([w for w in st.session_state.master_words if w not in st.session_state.session_words])
                st.session_state.test_words = st.session_state.session_words + [past]
                random.shuffle(st.session_state.test_words)
                st.session_state.word_index = 0
                st.session_state.page = "test"
            st.rerun()
        else:
            st.error(f"正解は {word['a']} です。落ち着いて入力しましょう！")

# --- 6. 復習テスト ＆ 特訓（5回ペナルティ） ---
elif st.session_state.page == "test":
    idx = st.session_state.word_index
    word = st.session_state.test_words[idx]
    st.header(f"🔥 復習テスト ({idx+1}/{len(st.session_state.test_words)})")
    st.subheader(f"「{word['q']}」を英語で！")
    t_in = st.text_input("テスト回答:", key=f"v_{st.session_state.input_key}").strip().lower()
    
    if st.button("テスト判定", use_container_width=True):
        if t_in == word['a']:
            st.session_state.word_index += 1
            st.session_state.input_key += 1
            if st.session_state.word_index >= len(st.session_state.test_words):
                st.session_state.page = "result"
            st.rerun()
        else:
            st.session_state.penalty_word = word
            st.session_state.penalty_count = 1
            st.session_state.page = "penalty"
            st.rerun()

elif st.session_state.page == "penalty":
    word = st.session_state.penalty_word
    st.error(f"【特訓】「{word['q']}」をあと {6-st.session_state.penalty_count} 回書いて覚えましょう！")
    p_in = st.text_input(f"{st.session_state.penalty_count}回目:", key=f"p_{st.session_state.input_key}").strip().lower()
    if st.button("特訓送信", use_container_width=True):
        if p_in == word['a']:
            st.session_state.input_key += 1
            if st.session_state.penalty_count < 5:
                st.session_state.penalty_count += 1
            else:
                st.session_state.word_index = 0
                st.session_state.page = "test" # テストの最初へ
            st.rerun()

elif st.session_state.page == "result":
    st.header("お見事！テスト合格です 🎉")
    st.balloons()
    st.info(random.choice(["伊達：カロリーは熱に弱いから0kcal","ノブ：昔、ノブ小池だった","出川：実家は明治創業の海苔屋"]))
    if st.button("もう一度練習する", use_container_width=True):
        st.session_state.streak += 1
        st.session_state.page = "main_menu"
        st.rerun()
