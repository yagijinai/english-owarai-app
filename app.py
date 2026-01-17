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
    
    # ユーザー情報
    if 'user_name' not in st.session_state:
        st.session_state.user_name = ""
    if 'streak' not in st.session_state:
        st.session_state.streak = 10
    
    # 練習とテストの管理
    if 'word_index' not in st.session_state:
        st.session_state.word_index = 0
    if 'repeat_count' not in st.session_state:
        st.session_state.repeat_count = 1
    if 'session_words' not in st.session_state:
        st.session_state.session_words = [] # 今日の3語
    if 'test_words' not in st.session_state:
        st.session_state.test_words = []    # 復習テスト用リスト
    
    # ペナルティ（5回入力）用
    if 'penalty_word' not in st.session_state:
        st.session_state.penalty_word = None
    if 'penalty_count' not in st.session_state:
        st.session_state.penalty_count = 0

    # 単語リスト
    if 'master_words' not in st.session_state:
        st.session_state.master_words = [
            {"q": "りんご", "a": "apple"}, {"q": "本", "a": "book"},
            {"q": "猫", "a": "cat"}, {"q": "犬", "a": "dog"},
            {"q": "ペン", "a": "pen"}, {"q": "机", "a": "desk"},
            {"q": "鳥", "a": "bird"}, {"q": "卵", "a": "egg"}
        ]
    
    if 'input_key' not in st.session_state:
        st.session_state.input_key = 0
    if 'feedback' not in st.session_state:
        st.session_state.feedback = ""
    if 'current_neta' not in st.session_state:
        st.session_state.current_neta = ""

init_session_state()

# --- 3. ログイン画面（省略版：前回のパート2と同じ） ---
if not st.session_state.logged_in:
    st.title("英単語練習アプリ")
    if st.button("同じIDでつづける", use_container_width=True):
        st.session_state.user_name = "お父様"
        st.session_state.logged_in = True
        st.session_state.page = "main_menu"
        st.rerun()
    st.stop()

# --- 4. 練習ロジック ---
st.sidebar.markdown(f"### 👤 {st.session_state.user_name}\n### 🔥 継続: {st.session_state.streak}日")

if st.session_state.page == "main_menu":
    st.header("本日のメニュー：練習 ＋ 復習テスト")
    if st.button("🚀 学習スタート", use_container_width=True):
        st.session_state.session_words = random.sample(st.session_state.master_words, 3)
        st.session_state.word_index = 0
        st.session_state.repeat_count = 1
        st.session_state.page = "training"
        st.session_state.input_key += 1
        st.rerun()

elif st.session_state.page == "training":
    idx = st.session_state.word_index
    rep = st.session_state.repeat_count
    word = st.session_state.session_words[idx]
    st.header(f"練習 {idx+1}/3 ({rep}回目)")
    st.subheader(f"「{word['q']}」のスペルは？")
    user_input = st.text_input("入力：", key=f"tr_{st.session_state.input_key}").strip().lower()
    
    if st.button("判定", use_container_width=True):
        if user_input == word['a']:
            st.session_state.input_key += 1
            if st.session_state.repeat_count < 3:
                st.session_state.repeat_count += 1
            else:
                st.session_state.repeat_count = 1
                st.session_state.word_index += 1
            
            if st.session_state.word_index >= 3:
                # 練習終了 -> 復習テストの準備
                past_word = random.choice([w for w in st.session_state.master_words if w not in st.session_state.session_words])
                st.session_state.test_words = st.session_state.session_words + [past_word]
                random.shuffle(st.session_state.test_words)
                st.session_state.word_index = 0
                st.session_state.page = "test"
            st.rerun()
        else:
            st.error(f"不正解！答えは {word['a']}")

# --- 5. 復習テスト ＆ 特訓ロジック ---
elif st.session_state.page == "test":
    idx = st.session_state.word_index
    word = st.session_state.test_words[idx]
    st.header(f"🔥 復習テスト ({idx+1}/{len(st.session_state.test_words)})")
    st.subheader(f"「{word['q']}」を英語で！")
    
    test_input = st.text_input("回答：", key=f"ts_{st.session_state.input_key}").strip().lower()
    
    if st.button("テスト判定", use_container_width=True):
        if test_input == word['a']:
            st.success("正解！")
            st.session_state.word_index += 1
            st.session_state.input_key += 1
            if st.session_state.word_index >= len(st.session_state.test_words):
                # テキスト全問正解！
                st.session_state.page = "result"
            st.rerun()
        else:
            # 間違えたら特訓モードへ
            st.session_state.penalty_word = word
            st.session_state.penalty_count = 1
            st.session_state.page = "penalty"
            st.rerun()

elif st.session_state.page == "penalty":
    word = st.session_state.penalty_word
    count = st.session_state.penalty_count
    st.error(f"【特訓】「{word['q']}」をあと {6-count} 回正解してください！")
    st.subheader(f"正解スペル： {word['a']}")
    
    pen_input = st.text_input(f"{count}回目：", key=f"pen_{st.session_state.input_key}").strip().lower()
    if st.button("特訓入力", use_container_width=True):
        if pen_input == word['a']:
            st.session_state.input_key += 1
            if st.session_state.penalty_count < 5:
                st.session_state.penalty_count += 1
            else:
                # 特訓完了 -> テストを最初からやり直し（間違えた単語はリストに残っている）
                st.session_state.word_index = 0
                random.shuffle(st.session_state.test_words)
                st.session_state.page = "test"
            st.rerun()

# --- 6. 結果・豆知識画面 ---
elif st.session_state.page == "result":
    st.header("テスト合格！完璧です！ 🎉")
    st.balloons()
    
    # 豆知識リスト
    neta_list = [
        "サンドウィッチマン伊達：アイスは冷たいからカロリーが凍って消えるので0kcal。",
        "千鳥ノブ：昔、ノブ小池として活動していた時期、子供に本気で泣かれたことがある。",
        "出川哲朗：リアクションの神様だが、プライベートでは超真面目で礼儀正しい。"
    ]
    st.session_state.current_neta = random.choice(neta_list)
    
    st.subheader("💡 今日のお笑い芸人豆知識")
    st.info(st.session_state.current_neta)
    
    if st.button("もう一度最初から練習する", use_container_width=True):
        st.session_state.streak += 1
        st.session_state.page = "main_menu"
        st.rerun()
