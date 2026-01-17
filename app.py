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
    
    # マスターリスト
    if 'master_words' not in st.session_state:
        st.session_state.master_words = [
            {"q": "りんご", "a": "apple"}, {"q": "本", "a": "book"},
            {"q": "猫", "a": "cat"}, {"q": "犬", "a": "dog"},
            {"q": "ペン", "a": "pen"}, {"q": "机", "a": "desk"},
            {"q": "鳥", "a": "bird"}, {"q": "卵", "a": "egg"}
        ]
    
    # 練習・テスト用
    if 'session_words' not in st.session_state: st.session_state.session_words = []
    if 'test_words' not in st.session_state: st.session_state.test_words = []
    if 'word_index' not in st.session_state: st.session_state.word_index = 0
    if 'repeat_count' not in st.session_state: st.session_state.repeat_count = 1
    
    # 特訓・ヒント用
    if 'penalty_word' not in st.session_state: st.session_state.penalty_word = None
    if 'penalty_count' not in st.session_state: st.session_state.penalty_count = 0
    if 'show_hint' not in st.session_state: st.session_state.show_hint = False
    
    if 'input_key' not in st.session_state: st.session_state.input_key = 0
    if 'current_neta' not in st.session_state: st.session_state.current_neta = ""

init_session_state()

# --- 3. 音声再生用関数 ---
def speak_word(word):
    js_code = f"<script>var m=new SpeechSynthesisUtterance('{word}');m.lang='en-US';window.speechSynthesis.speak(m);</script>"
    components.html(js_code, height=0)

# --- 4. ログイン・ID選択画面 ---
if not st.session_state.logged_in:
    st.title("英単語練習アプリ")
    
    if st.session_state.page == "login":
        st.subheader(f"現在は「{st.session_state.user_name}」として設定されています。")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"同じID（{st.session_state.user_name}）でつづける", use_container_width=True):
                st.session_state.logged_in = True
                st.session_state.page = "main_menu"
                st.rerun()
        with col2:
            if st.button("他のIDに変える", use_container_width=True):
                st.session_state.page = "change_id"
                st.rerun()

    elif st.session_state.page == "change_id":
        st.subheader("新しい名前を入力してください")
        new_name = st.text_input("名前:", value="").strip()
        if st.button("この名前で始める", use_container_width=True):
            if new_name:
                st.session_state.user_name = new_name
                st.session_state.streak = 0  # 新しい人の場合は0日から
                st.session_state.logged_in = True
                st.session_state.page = "main_menu"
                st.rerun()
            else:
                st.warning("名前を入力してください。")
    st.stop()

# サイドバー表示
st.sidebar.markdown(f"### 👤 {st.session_state.user_name}\n### 🔥 継続: {st.session_state.streak}日")

# --- 5. メインメニュー ＆ 練習 ---
if st.session_state.page == "main_menu":
    st.header(f"こんにちは、{st.session_state.user_name}さん！")
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

    c1, c2 = st.columns(2)
    with c1:
        if st.button("📢 発音を聞く"): speak_word(word['a'])
    with c2:
        if st.button("💡 答えを見る"): st.session_state.show_hint = True
    
    if st.session_state.show_hint: st.info(f"答え： {word['a']}")

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

# --- 6. 復習テスト ＆ 特訓 ＆ 結果 ---
elif st.session_state.page == "test":
    if not st.session_state.test_words:
        st.session_state.page = "result"
        st.rerun()

    word = st.session_state.test_words[0]
    st.header(f"🔥 復習テスト (残り {len(st.session_state.test_words)}問)")
    st.subheader(f"「{word['q']}」を英語で！")
    if st.button("📢 発音を聞く"): speak_word(word['a'])

    t_in = st.text_input("回答:", key=f"v_{st.session_state.input_key}").strip().lower()
    if st.button("テスト判定", use_container_width=True):
        if t_in == word['a']:
            st.session_state.test_words.pop(0)
            st.session_state.input_key += 1
            st.rerun()
        else:
            st.session_state.penalty_word = word
            st.session_state.penalty_count = 1
            st.session_state.page = "penalty"
            st.rerun()

elif st.session_state.page == "penalty":
    word = st.session_state.penalty_word
    st.error(f"【特訓】「{word['q']}」あと {6-st.session_state.penalty_count} 回！(正解:{word['a']})")
    p_in = st.text_input(f"{st.session_state.penalty_count}回目:", key=f"p_{st.session_state.input_key}").strip().lower()
    if st.button("送信", use_container_width=True):
        if p_in == word['a']:
            st.session_state.input_key += 1
            if st.session_state.penalty_count < 5:
                st.session_state.penalty_count += 1
            else:
                failed = st.session_state.test_words.pop(0)
                st.session_state.test_words.append(failed)
                st.session_state.page = "test"
            st.rerun()

elif st.session_state.page == "result":
    st.header("全問正解！お疲れ様でした 🎉")
    st.balloons()
    neta = random.choice(["伊達：カロリーは足が速いから0kcal","ノブ：昔、ノブ小池だった","出川：実家は老舗の海苔屋"])
    st.info(f"💡 芸人豆知識：{neta}")
    if st.button("マイページへ戻る", use_container_width=True):
        st.session_state.streak += 1
        st.session_state.page = "main_menu"
        st.rerun()
