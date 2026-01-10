# --- 修正箇所のイメージ ---
else:
    # 通常のテスト入力
    user_ans = st.text_input("答えを入力", key=f"rev_{r_idx}").lower().strip()
    if user_ans != "":
        if user_ans == str(word['word']).lower():
            st.success("正解！")
            # （省略）
        else:
            # 【高品質な演出】
            # 画面をガタガタ揺らすCSS（スタイル）を一時的に注入する
            st.markdown("""
                <style>
                @keyframes shake {
                    0% { transform: translate(1px, 1px) rotate(0deg); }
                    10% { transform: translate(-1px, -2px) rotate(-1deg); }
                    20% { transform: translate(-3px, 0px) rotate(1deg); }
                    30% { transform: translate(3px, 2px) rotate(0deg); }
                    40% { transform: translate(1px, -1px) rotate(1deg); }
                    50% { transform: translate(-1px, 2px) rotate(-1deg); }
                    100% { transform: translate(1px, 1px) rotate(0deg); }
                }
                .stApp {
                    animation: shake 0.5s; /* 0.5秒間画面を揺らす */
                    background-color: #ffe6e6; /* 背景を薄赤くする */
                }
                </style>
                """, unsafe_allow_html=True)
            
            st.error("つづりが違います！特訓を開始します。")
            st.session_state.wrong_word_id = word['id']
            st.session_state.review_queue.append(word)
            if st.button("特訓を始める"):
                st.rerun()
