import streamlit as st
import random
import streamlit.components.v1 as components

# --- 1. ページ設定 ---
st.set_page_config(layout="centered", page_title="英単語練習アプリ")

# --- 2. セッション状態の初期化 ---
def init_session_state():
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'page' not in st.session_state: st.session_state.page = "login"
    if 'user_name' not in st.session_state: st.session_state.user_name = "お父様"
    if 'streak' not in st.session_state: st.session_state.streak = 10
    
    # 単語マスターリスト
    if 'master_words' not in st.session_state:
        st.session_state.master_words = [
            {"q": "りんご", "a": "apple"}, {"q": "本", "a": "book"},
            {"q": "猫", "a": "cat"}, {"q": "犬", "a": "dog"},
            {"q": "ペン", "a": "pen"}, {"q": "机", "a": "desk"},
            {"q": "鳥", "a": "bird"}, {"q": "卵", "a": "egg"}
        ]
    
    # 進捗管理
    if 'session_words' not in st.session_state: st.session_state.session_words = []
    if 'test_words' not in st.session_state: st.session_state.test_words = []
    if 'word_index' not in st.session_state: st.session_state.word_index = 0
    if 'repeat_count' not in st.session_state: st.session_state.repeat_count = 1
    
    # ペナルティ・ヒント管理
    if 'penalty_word' not in st.session_state: st.session_state.penalty_word = None
    if 'penalty_count' not in st.session_state: st.session_state.penalty_count = 0
    if 'show_hint' not in st.session_state: st.session_state.show_hint = False
    
    if 'input_key' not in st.session_state: st.session_state.input_key = 0
    if 'current_neta' not in st.session_state: st.session_state.current_neta = ""

init_session_state()

# --- 3. 音声再生用の関数 (JavaScriptを使用) ---
def speak_word(word):
    js_code = f"""
    <script>
    var msg = new SpeechSynthesisUtterance('{word}');
    msg.lang = 'en-US';
    window.speechSynthesis.speak(msg);
    </script>
    """
    components.html(js_code, height=0)

# --- 4. ログイン画面 ＆ サイドバー (前回と同様) ---
if not st.session_state.logged_in:
    st.title("英単語練習アプリ")
    if st.button("同じIDでつづける", use_container_width=True):
        st.session_state.logged_in = True
        st.session_state.page = "main_menu"
        st.rerun()
    st.stop()

st.sidebar.markdown(f"### 👤 {st.session_state.user_name}\n### 🔥 継続: {st.session_state.streak}日")

# --- 5. 練習ロジック ---
if st.session_state.page == "main_menu":
    st.header("練習 ＋ 復習テスト")
    if st.button("🚀 学習スタート", use_container_width=True):
        st.session_state.session_words = random.sample(st.session_state.master_words, 3)
        st.session_state.word_index = 0
        st.session_state.repeat_count = 1
        st.session_state.page = "training"
        st.rerun()

elif st.session_state.page == "training":
    word = st.session_state.session_words[st.session_state.word_index]
    st.header(f"練習 {st.session_state.word_index+1}/3 ({st.session_state.repeat_count}回目)")
    st.subheader(f"「{word['q']}」")

    # ヒントと音声ボタンを横並びに
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📢 発音を聞く"): speak_word(word['a'])
    with col2:
        if st.button("💡 答えを見る"): st.session_state.show_hint = True
    
    if st.session_state.show_hint:
        st.info(f"答え： {word['a']}")

    u_in = st.text_input("入力:", key=f"t_{st.session_state.input_key}").strip().lower()
    
    if st.button("判定", use_container_width=True):
        if u_in == word['a']:
            st.session_state.show_hint = False
            st.session_state.input_key += 1
            if st.session_state.repeat_count < 3:
                st.session_state.repeat_count += 1
            else:
                st.session_state.repeat_count = 1
                st.session_state.word_index += 1
            
            if st.session_state.word_index >= 3:
                past = random.choice([w for w in st.session_state.master_words if w not in st.session_state.session_words])
                st.session_state.test_words = st.session_state.session_words + [past]
                random.shuffle(st.session_state.test_words)
                st.session_state.page = "test"
            st.rerun()
        else:
            st.error("スペルが違います！ヒントボタンを使ってみてね。")

# --- 6. 復習テストロジック ---
elif st.session_state.page == "test":
    # まだ正解していない単語があるか確認
    if not st.session_state.test_words:
        st.session_state.page = "result"
        st.rerun()

    # リストの最初の単語を出す
    word = st.session_state.test_words[0]
    st.header(f"🔥 復習テスト (残り {len(st.session_state.test_words)}問)")
    st.subheader(f"「{word['q']}」を英語で！")
    
    # テスト中も音声だけは聞けるように設定（お好みで）
    if st.button("📢 発音を聞く"): speak_word(word['a'])

    t_in = st.text_input("回答:", key=f"v_{st.session_state.input_key}").strip().lower()
    
    if st.button("テスト判定", use_container_width=True):
        if t_in == word['a']:
            st.success("正解！この単語はクリアです。")
            # 正解した単語をリストから取り除く
            st.session_state.test_words.pop(0)
            st.session_state.input_key += 1
            st.rerun()
        else:
            # 間違えたら特訓モードへ
            st.session_state.penalty_word = word
            st.session_state.penalty_count = 1
            st.session_state.page = "penalty"
            st.rerun()

# --- 7. 特訓 ＆ 結果 ---
elif st.session_state.page == "penalty":
    word = st.session_state.penalty_word
    st.error(f"【特訓】「{word['q']}」をあと {6-st.session_state.penalty_count} 回！")
    st.subheader(f"正解：{word['a']}")
    
    # 特訓中も発音を確認できる
    if st.button("📢 お手本を聞く"): speak_word(word['a'])

    p_in = st.text_input(f"{st.session_state.penalty_count}回目:", key=f"p_{st.session_state.input_key}").strip().lower()
    if st.button("送信", use_container_width=True):
        if p_in == word['a']:
            st.session_state.input_key += 1
            if st.session_state.penalty_count < 5:
                st.session_state.penalty_count += 1
            else:
                # 特訓終了。間違えた単語をテストリストの最後尾に回して再挑戦
                failed_word = st.session_state.test_words.pop(0)
                st.session_state.test_words.append(failed_word)
                st.session_state.page = "test"
            st.rerun()

elif st.session_state.page == "result":
    st.header("全問正解！お疲れ様でした 🎉")
    st.balloons()
    neta = random.choice(["伊達：ドーナツは真ん中が空洞だから0kcal","ノブ：昔、ノブ小池だった","出川：実家は老舗の海苔屋"])
    st.info(f"💡 芸人豆知識：{neta}")
    if st.button("もう一度練習する", use_container_width=True):
        st.session_state.streak += 1
        st.session_state.page = "main_menu"
        st.rerun()
