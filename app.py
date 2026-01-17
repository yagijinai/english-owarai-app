import streamlit as st
import random

# --- 1. ページ設定 ---
st.set_page_config(layout="centered", page_title="英単語練習アプリ")

# --- 2. セッション状態の初期化 (すべてここで宣言) ---
def init_session_state():
    # 画面遷移管理
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'page' not in st.session_state: st.session_state.page = "login"
    
    # ユーザー情報
    if 'user_name' not in st.session_state: st.session_state.user_name = "ゲスト"
    if 'streak' not in st.session_state: st.session_state.streak = 10
    
    # 練習とテストの進捗管理 (IndexError対策)
    if 'word_index' not in st.session_state: st.session_state.word_index = 0
    if 'repeat_count' not in st.session_state: st.session_state.repeat_count = 1
    if 'session_words' not in st.session_state: st.session_state.session_words = []
    if 'test_words' not in st.session_state: st.session_state.test_words = []
    
    # 特訓（ペナルティ）管理
    if 'penalty_word' not in st.session_state: st.session_state.penalty_word = None
    if 'penalty_count' not in st.session_state: st.session_state.penalty_count = 0
    
    # 単語リスト
    if 'master_words' not in st.session_state:
        st.session_state.master_words = [
            {"q": "りんご", "a": "apple"}, {"q": "本", "a": "book"},
            {"q": "猫", "a": "cat"}, {"q": "犬", "a": "dog"},
            {"q": "ペン", "a": "pen"}, {"q": "机", "a": "desk"},
            {"q": "鳥", "a": "bird"}, {"q": "卵", "a": "egg"}
        ]
    
    if 'input_key' not in st.session_state: st.session_state.input_key = 0
    if 'feedback' not in st.session_state: st.session_state.feedback = ""
    if 'current_neta' not in st.session_state: st.session_state.current_neta = ""

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
            st.session_state.page = "main_menu"
            st.rerun()
    with col2:
        if st.button("新しいIDではじめる", use_container_width=True):
            st.session_state.user_name = "新規ユーザー"
            st.session_state.streak = 0
            st.session_state.logged_in = True
            st.session_state.page = "main_menu"
            st.rerun()
    st.stop()

# --- 4. サイドバー (ログイン後常に表示) ---
st.sidebar.markdown(f"### 👤 {st.session_state.user_name}")
st.sidebar.markdown(f"### 🔥 連続学習: {st.session_state.streak}日")

# --- 5. メインメニュー ＆ 練習 ---
if st.session_state.page == "main_menu":
    st.header("今日の学習メニュー")
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
    u_input = st.text_input("スペル入力:", key=f"t_{st.session_state.input_key}").strip().lower()
    
    if st.button("判定", use_container_width=True):
        if u_input == word['a']:
            st.session_state.input_key += 1
            if st.session_state.repeat_count < 3:
                st.session_state.repeat_count += 1
            else:
                st.session_state.repeat_count = 1
                st.session_state.word_index += 1
            
            if st.session_state.word_index >= 3:
                # テスト単語の生成 (IndexError対策)
                past = random.choice([w for w in st.session_state.master_words if w not in st.session_state.session_words])
                st.session_state.test_words = st.session_state.session_words + [past]
                random.shuffle(st.session_state.test_words)
                st.session_state.word_index = 0
                st.session_state.page = "test"
            st.rerun()
        else:
            st.error(f"正解は {word['a']} です")

# --- 6. 復習テスト ＆ 特訓ロジック ---
elif st.session_state.page == "test":
    idx = st.session_state.word_index
    word = st.session_state.test_words[idx]
    st.header(f"🔥 復習テスト ({idx+1}/{len(st.session_state.test_words)})")
    st.subheader(f"「{word['q']}」を英語で！")
    t_input = st.text_input("回答:", key=f"v_{st.session_state.input_key}").strip().lower()
    
    if st.button("テスト判定", use_container_width=True):
        if t_input == word['a']:
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
    st.error(f"特訓！「{word['q']}」あと {6-st.session_state.penalty_count} 回！")
    p_input = st.text_input(f"{st.session_state.penalty_count}回目:", key=f"p_{st.session_state.input_key}").strip().lower()
    if st.button("送信", use_container_width=True):
        if p_input == word['a']:
            st.session_state.input_key += 1
            if st.session_state.penalty_count < 5:
                st.session_state.penalty_count += 1
            else:
                st.session_state.word_index = 0
                st.session_state.page = "test"
            st.rerun()

elif st.session_state.page == "result":
    st.header("合格！ 🎉")
    st.balloons()
    st.info(random.choice(["伊達：カロリーは足が速いから逃げる","ノブ：昔、ノブ小池だった","出川：実家は老舗の海苔屋"]))
    if st.button("もう一度", use_container_width=True):
        st.session_state.streak += 1
        st.session_state.page = "main_menu"
        st.rerun()
