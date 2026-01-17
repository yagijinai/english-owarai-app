import streamlit as st
import random
import streamlit.components.v1 as components
from datetime import datetime

# --- 1. ページ設定 ---
st.set_page_config(layout="centered", page_title="英単語練習アプリ")

# --- 2. セッション状態の初期化 ---
def init_session_state():
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'page' not in st.session_state: st.session_state.page = "login"
    if 'user_db' not in st.session_state: st.session_state.user_db = {"お父様": "1234", "娘さん": "1234"}
    if 'current_user' not in st.session_state: st.session_state.current_user = ""
    
    # ストリーク（連続日数）
    if 'streak' not in st.session_state: st.session_state.streak = 10
    
    # 単語マスターDB
    if 'word_db' not in st.session_state:
        st.session_state.word_db = {
            "中学1年生": [{"q": "りんご", "a": "apple"}, {"q": "本", "a": "book"}, {"q": "猫", "a": "cat"}, {"q": "犬", "a": "dog"}, {"q": "ペン", "a": "pen"}],
            "中学2年生": [{"q": "経験", "a": "experience"}, {"q": "快適な", "a": "comfortable"}],
            "中学3年生": [{"q": "環境", "a": "environment"}, {"q": "影響", "a": "influence"}]
        }
    
    # 【新機能】その学年で「練習済み」の単語を記録するリスト
    if 'learned_words' not in st.session_state: st.session_state.learned_words = []

    # 進捗管理変数
    if 'session_words' not in st.session_state: st.session_state.session_words = []
    if 'test_words' not in st.session_state: st.session_state.test_words = []
    if 'word_index' not in st.session_state: st.session_state.word_index = 0
    if 'repeat_count' not in st.session_state: st.session_state.repeat_count = 1
    if 'penalty_word' not in st.session_state: st.session_state.penalty_word = None
    if 'penalty_count' not in st.session_state: st.session_state.penalty_count = 0
    if 'show_hint' not in st.session_state: st.session_state.show_hint = False
    if 'input_key' not in st.session_state: st.session_state.input_key = 0
    if 'current_neta' not in st.session_state: st.session_state

    # --- 3. ログイン画面 ---
if not st.session_state.logged_in:
    st.title("📖 英単語練習")
    u_in = st.text_input("名前 (ID):").strip()
    p_in = st.text_input("パスワード:", type="password").strip()
    
    if st.button("ログイン / 新規登録", use_container_width=True):
        if u_in and p_in:
            if u_in in st.session_state.user_db:
                if st.session_state.user_db[u_in] == p_in:
                    st.session_state.current_user = u_in
                    st.session_state.logged_in = True
                    st.session_state.page = "main_menu"
                    st.rerun()
                else: st.error("パスワードが違います")
            else:
                st.session_state.user_db[u_in] = p_in
                st.session_state.current_user = u_in
                st.session_state.logged_in = True
                st.session_state.page = "main_menu"
                st.rerun()
    st.stop()

# ログイン後の表示
st.sidebar.title(f"👤 {st.session_state.current_user}")
st.sidebar.metric("🔥 連続学習", f"{st.session_state.streak}日")
st.sidebar.info(f"学年: {get_current_grade()}")

# --- 4. メイン画面 ＆ 練習 ---
if st.session_state.page == "main_menu":
    st.header(f"今日も頑張ろう！ {st.session_state.streak}日目")
    if st.button("🚀 学習スタート", use_container_width=True):
        grade = get_current_grade()
        all_grade_words = st.session_state.word_db[grade]
        
        # 【重要】未習の単語（learned_wordsに含まれていないもの）を探す
        unlearned = [w for w in all_grade_words if w['a'] not in st.session_state.learned_words]
        
        # もし未習がなくなったらリストをリセットして一巡させる
        if not unlearned:
            st.session_state.learned_words = []
            unlearned = all_grade_words
            st.toast("すべての単語を一巡しました！最初から復習します。")
            
        count = min(len(unlearned), 3)
        st.session_state.session_words = random.sample(unlearned, count)
        st.session_state.word_index = 0
        st.session_state.repeat_count = 1
        st.session_state.page = "training"
        st.rerun()

elif st.session_state.page == "training":
    word = st.session_state.session_words[st.session_state.word_index]
    st.header(f"練習 {st.session_state.word_index+1}/3")
    st.subheader(f"「{word['q']}」")
    
    c1, c2 = st.columns(2)
    with c1: 
        if st.button("📢 音声"): speak_word(word['a'])
    with c2:
        if st.button("💡 答え"): st.session_state.show_hint = True
    if st.session_state.show_hint: st.info(f"正解： {word['a']}")

    u_in = st.text_input("入力:", key=f"t_{st.session_state.input_key}").strip().lower()
    if st.button("判定", use_container_width=True):
        if u_in == word['a']:
            st.session_state.show_hint = False
            st.session_state.input_key += 1
            if st.session_state.repeat_count < 3: st.session_state.repeat_count += 1
            else:
                # 3回正解したら「練習済み」に追加
                if word['a'] not in st.session_state.learned_words:
                    st.session_state.learned_words.append(word['a'])
                st.session_state.repeat_count = 1
                st.session_state.word_index += 1
                
            if st.session_state.word_index >= len(st.session_state.session_words):
                # 復習テスト作成：今日の3語 ＋ 今まで復習してきた単語から1語
                st.session_state.test_words = list(st.session_state.session_words)
                
                # 「今まで復習してきた単語」＝「練習済みリストから今日の3語を除いたもの」
                past_learned = [w for w in st.session_state.word_db[get_current_grade()] 
                                if w['a'] in st.session_state.learned_words and w not in st.session_state.session_words]
                
                if past_learned:
                    st.session_state.test_words.append(random.choice(past_learned))
                
                random.shuffle(st.session_state.test_words)
                st.session_state.page = "test"
            st.rerun()

elif st.session_state.page == "test":
    if not st.session_state.test_words:
        neta_list = [
            "サンドウィッチマン伊達：カステラはギュッと潰せばカロリーも潰れるから0kcal。",
            "千鳥ノブ：昔、バラエティ番組の企画で1ヶ月だけ『ノブ小池』に改名していた。",
            "出川哲朗：実家は老舗海苔問屋『蔦金商店』でお金持ち。",
            "やす子：実は元自衛官で、ブルドーザーの運転ができる。"
        ]
        st.session_state.current_neta = random.choice(neta_list)
        # 合格したのでストリークをカウントアップ
        st.session_state.streak += 1
        st.session_state.page = "result"
        st.rerun()

    word = st.session_state.test_words[0]
    st.header(f"🔥 復習テスト (残り {len(st.session_state.test_words)}問)")
    st.subheader(f"「{word['q']}」")
    
    t_in = st.text_input("回答:", key=f"v_{st.session_state.input_key}").strip().lower()
    if st.button("判定", use_container_width=True):
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
    st.error(f"【特訓】あと {6-st.session_state.penalty_count} 回！(正解:{word['a']})")
    p_in = st.text_input(f"{st.session_state.penalty_count}回目:", key=f"p_{st.session_state.input_key}").strip().lower()
    if st.button("送信", use_container_width=True):
        if p_in == word['a']:
            st.session_state.input_key += 1
            if st.session_state.penalty_count < 5: st.session_state.penalty_count += 1
            else:
                failed = st.session_state.test_words.pop(0)
                st.session_state.test_words.append(failed)
                st.session_state.page = "test"
            st.rerun()

elif st.session_state.page == "result":
    st.header("✨ 全問正解！ ✨")
    st.balloons()
    
    # 連続日数を大きく表示
    st.info(f"🔥 連続学習 {st.session_state.streak}日達成！")
    
    st.success("🎁 ご褒美：お笑い芸人豆知識")
    st.markdown(f"### {st.session_state.current_neta}")
    
    if st.button("メインメニューへ戻る", use_container_width=True):
        st.session_state.page = "main_menu"
        st.rerun()
