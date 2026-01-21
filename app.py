import streamlit as st
import random
import streamlit.components.v1 as components
from datetime import datetime
import time

# --- 1. ページ設定 ---
st.set_page_config(layout="centered", page_title="英単語練習アプリ")

# --- 2. セッション状態の初期化 ---
def init_session_state():
    if 'user_db' not in st.session_state:
        st.session_state.user_db = {"お父様": "1234", "娘さん": "1234"}
    
    defaults = {
        'logged_in': False,
        'page': "login",
        'last_user': None,
        'current_user': "",
        'streak': 10,
        'learned_words': [], 
        'session_words': [], # 今回練習する3単語
        'success_counts': {}, # 各単語の成功回数を記録
        'test_words': [],
        'penalty_word': None,
        'penalty_count': 0,
        'show_hint': False,
        'input_key': 0,
        'current_neta': "",
        'confirm_register': False,
        'word_db': {
            "中学1年生": [
                {"q": "りんご", "a": "apple"}, {"q": "本", "a": "book"}, {"q": "猫", "a": "cat"}, 
                {"q": "犬", "a": "dog"}, {"q": "ペン", "a": "pen"}, {"q": "机", "a": "desk"},
                {"q": "学校", "a": "school"}, {"q": "生徒", "a": "student"}, {"q": "先生", "a": "teacher"}
            ]
        }
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

def speak_word(word):
    js = f"<script>var m=new SpeechSynthesisUtterance('{word}');m.lang='en-US';window.speechSynthesis.speak(m);</script>"
    components.html(js, height=0)

def get_current_grade():
    try:
        today = datetime.now()
        school_year = today.year if today.month >= 4 else today.year - 1
        grade_diff = school_year - 2025
        grades = ["中学1年生", "中学2年生", "中学3年生"]
        return grades[grade_diff] if 0 <= grade_diff < len(grades) else "中学1年生"
    except: return "中学1年生"

    # --- 3. ログイン管理 ---
if not st.session_state.logged_in:
    st.title("🔐 ログイン")
    
    if st.session_state.last_user:
        st.subheader("同じ端末でアプリをスタートします。")
        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"同じID ({st.session_state.last_user}) で続ける", use_container_width=True):
                st.session_state.current_user = st.session_state.last_user
                st.session_state.logged_in = True
                st.session_state.page = "main_menu"
                st.rerun()
        with c2:
            if st.button("違うIDではじめる", use_container_width=True):
                st.session_state.last_user = None
                st.rerun()
    else:
        u_in = st.text_input("名前 (ID):", key="u_field").strip()
        p_in = st.text_input("パスワード:", type="password", key="p_field").strip()
        if st.button("ログイン", use_container_width=True):
            if u_in in st.session_state.user_db and st.session_state.user_db[u_in] == p_in:
                st.session_state.current_user = u_in
                st.session_state.last_user = u_in
                st.session_state.logged_in = True
                st.session_state.page = "main_menu"
                st.rerun()
            else: st.error("名前またはパスワードが違います")
        if st.button("新規登録", use_container_width=True):
            if u_in and p_in:
                st.session_state.confirm_register = True
        
        if st.session_state.confirm_register:
            if st.button(f"「{u_in}」を新規登録します"):
                st.session_state.user_db[u_in] = p_in
                st.session_state.current_user = u_in
                st.session_state.last_user = u_in
                st.session_state.logged_in = True
                st.session_state.page = "main_menu"
                st.session_state.confirm_register = False
                st.rerun()
    st.stop()

# --- 4. メインメニュー ---
if st.session_state.page == "main_menu":
    st.header(f"🔥 連続 {st.session_state.streak}日目")
    st.subheader(f"こんにちは、{st.session_state.current_user}さん！")
    
    if st.button("🚀 学習スタート", use_container_width=True):
        grade = get_current_grade()
        all_words = st.session_state.word_db.get(grade, [])
        unlearned = [w for w in all_words if w['a'] not in st.session_state.learned_words]
        
        if len(unlearned) < 3:
            st.session_state.learned_words = []
            unlearned = all_words
            
        st.session_state.session_words = random.sample(unlearned, 3)
        # 各単語の成功回数を0で初期化
        st.session_state.success_counts = {w['a']: 0 for w in st.session_state.session_words}
        st.session_state.page = "training"
        st.rerun()

# --- 5. 練習中 (ランダム出題モード) ---
elif st.session_state.page == "training":
    # まだ3回成功していない単語だけをリストアップ
    active_words = [w for w in st.session_state.session_words if st.session_state.success_counts[w['a']] < 3]
    
    if not active_words:
        # 全単語3回成功したらテストへ
        st.session_state.test_words = list(st.session_state.session_words)
        st.session_state.page = "test"
        st.rerun()

    # 残っている単語から1つランダムに選ぶ（ここがポイント！）
    if 'current_target_word' not in st.session_state or st.session_state.current_target_word not in [w['a'] for w in active_words]:
        st.session_state.current_target_word = random.choice(active_words)['a']
    
    # 表示用の単語データを取得
    word = next(w for w in st.session_state.session_words if w['a'] == st.session_state.current_target_word)
    current_count = st.session_state.success_counts[word['a']]

    st.header(f"練習中：残り {len(active_words)} 単語")
    st.subheader(f"「{word['q']}」")
    st.write(f"成功回数: **{current_count} / 3回**") # 何回目かを表示
    
    c1, c2 = st.columns(2)
    with c1: 
        if st.button("📢 音声"): speak_word(word['a'])
    with c2:
        if st.button("💡 答え"): st.session_state.show_hint = True
    if st.session_state.show_hint: st.info(f"正解： {word['a']}")

    u_in = st.text_input("スペル入力:", key=f"t_{st.session_state.input_key}").strip().lower()
    if st.button("判定", use_container_width=True):
        if u_in == word['a']:
            st.session_state.success_counts[word['a']] += 1
            st.session_state.show_hint = False
            st.session_state.input_key += 1
            # 次の判定のためにターゲットをクリア（次もランダムに選ばれる）
            del st.session_state.current_target_word
            st.rerun()
        else:
            st.error("おしい！もう一度。")

# --- 6. 復習テスト ---
elif st.session_state.page == "test":
    if not st.session_state.test_words:
        neta_list = ["サンドウィッチマン伊達：カステラは潰せば0kcal。", "千鳥ノブ：昔『ノブ小池』だった。", "やす子：元自衛官。"]
        st.session_state.current_neta = random.choice(neta_list)
        st.session_state.streak += 1
        st.session_state.page = "result"
        st.rerun()

    word = st.session_state.test_words[0]
    st.header(f"復習テスト (残り {len(st.session_state.test_words)}問)")
    st.subheader(f"「{word['q']}」は？")
    
    t_in = st.text_input("回答:", key=f"v_{st.session_state.input_key}").strip().lower()
    if st.button("判定", use_container_width=True):
        if t_in == word['a']:
            st.success("✨ 正解！ ✨")
            time.sleep(0.5)
            # 習得リストに追加
            if word['a'] not in st.session_state.learned_words:
                st.session_state.learned_words.append(word['a'])
            st.session_state.test_words.pop(0)
            st.session_state.input_key += 1
            st.rerun()
        else:
            st.session_state.penalty_word = word
            st.session_state.penalty_count = 1
            st.session_state.page = "penalty"
            st.rerun()

# --- 7. 特訓 ＆ 結果 ---
elif st.session_state.page == "penalty":
    word = st.session_state.penalty_word
    st.error(f"【特訓】あと {6-st.session_state.penalty_count} 回！(正解:{word['a']})")
    p_in = st.text_input(f"{st.session_state.penalty_count}回目:", key=f"p_{st.session_state.input_key}").strip().lower()
    if st.button("送信"):
        if p_in == word['a']:
            st.session_state.input_key += 1
            if st.session_state.penalty_count < 5: st.session_state.penalty_count += 1
            else:
                st.session_state.test_words.append(st.session_state.test_words.pop(0))
                st.session_state.page = "test"
            st.rerun()

elif st.session_state.page == "result":
    st.header("✨ 全問正解！ ✨")
    st.balloons()
    st.info(f"🔥 連続学習 {st.session_state.streak}日達成！")
    st.success(f"🎁 ご褒美：{st.session_state.current_neta}")
    if st.button("メニューへ戻る"):
        st.session_state.page = "main_menu"
        st.rerun()
