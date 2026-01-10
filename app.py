# --- ステップ2: 徹底復習テスト ---
elif st.session_state.phase == "review":
    r_idx = st.session_state.review_idx
    queue = st.session_state.review_queue
    
    if r_idx >= len(queue):
        st.session_state.phase = "goal"
        st.rerun()

    word = queue[r_idx]
    st.subheader(f"ステップ2: 復習テスト ({r_idx + 1}/{len(queue)})")
    st.write(f"「**{word['meaning']}**」を英語で書こう！")
    
    # 以前に間違えた履歴があるかチェック（特訓モード）
    if st.session_state.wrong_word_id == word['id']:
        st.warning("⚠️ つづりを間違えました！5回入力して特訓しよう。")
        st.write(f"正解は... **{word['word']}**")
        
        # 特訓用の5つの入力欄
        t_ans = [st.text_input(f"特訓 {i+1}/5", key=f"t{i}_{r_idx}").lower().strip() for i in range(5)]
        
        if all(a == str(word['word']).lower() and a != "" for a in t_ans):
            if st.button("特訓完了！あとでまたテストに出るよ"):
                st.session_state.wrong_word_id = None
                st.session_state.review_idx += 1
                st.rerun()
    else:
        # 通常のテスト入力
        user_ans = st.text_input("答えを入力", key=f"rev_{r_idx}").lower().strip()
        
        if user_ans != "":
            if user_ans == str(word['word']).lower():
                st.success("正解！")
                if st.button("次へ進む"):
                    st.session_state.review_idx += 1
                    st.rerun()
            else:
                # 【ここを強化】画面を揺らす演出（前回の提案を採用する場合）
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
                    .stApp { animation: shake 0.5s; background-color: #ffe6e6; }
                    </style>
                    """, unsafe_allow_html=True)
                
                st.error("つづりが違います！特訓を開始します。")
                
                # 間違えた単語を「今すぐ特訓」に設定し、かつ「リストの最後」にも追加
                if st.session_state.wrong_word_id != word['id']:
                    st.session_state.wrong_word_id = word['id']
                    st.session_state.review_queue.append(word) # リストの最後に追加
                
                if st.button("特訓を始める"):
                    st.rerun()
