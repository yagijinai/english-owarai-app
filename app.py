import streamlit as st
import streamlit.components.v1 as components

# 画面全体のタイトル設定
st.set_page_config(page_title="学習アプリ", layout="centered")

# --- HTML/CSS パート ---
# デザインと各画面（スタート、メニュー、練習）の構造を定義します
html_start = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: sans-serif; text-align: center; background: #f0f2f5; padding: 10px; }
        .container { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .hidden { display: none; }
        button { width: 100%; padding: 12px; margin: 10px 0; border: none; border-radius: 8px; cursor: pointer; background: #007bff; color: white; font-size: 16px; font-weight: bold; }
        button:hover { background: #0056b3; }
        .stats-card { background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; border: 1px solid #ffeeba; }
        #hint-text { color: #666; font-style: italic; background: #e9ecef; padding: 10px; border-radius: 4px; margin-top: 10px; }
        .streak-info { color: #d9534f; font-weight: bold; margin-bottom: 15px; font-size: 1.1em; }
        input { width: 90%; padding: 12px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <section id="start-screen">
            <h2>学習アプリ</h2>
            <div id="streak-display-start" class="streak-info"></div>
            <button onclick="handleStartMode('continue')">同じIDでつづける</button>
            <button onclick="handleStartMode('new')">新しいIDではじめる</button>
            
            <div id="id-input-area" class="hidden">
                <input type="text" id="user-id" placeholder="ユーザーIDを入力">
                <button onclick="confirmID()">決定してはじめる</button>
            </div>
        </section>

        <section id="menu-screen" class="hidden">
            <h2 id="welcome-msg"></h2>
            <div class="stats-card">
                <p>🔥 連続継続日数: <span id="streak-count">0</span>日</p>
            </div>
            <button onclick="startPractice()">練習をはじめる</button>
            <button onclick="logout()">IDを変更する（戻る）</button>
        </section>

        <section id="practice-screen" class="hidden">
            <h3>練習問題</h3>
            <div id="question-area">
                <p><strong>Q: 電車の線路に敷いてある「石」の役割は？</strong></p>
                <button id="hint-btn" style="background:#6c757d;" onclick="showHint()">ヒントを見る</button>
                <p id="hint-text" class="hidden">💡 ヒント：重さを分散させたり、音を小さくしたりします。</p>
            </div>
            <button onclick="backToMenu()" style="background:#28a745;">メニューに戻る</button>
        </section>
    </div>
"""
# --- JavaScript パート ---
# データの保存、日数の計算、画面切り替えのロジックです
js_code = """
    <script>
        let currentUserID = localStorage.getItem('lastUserID') || "";
        let streak = parseInt(localStorage.getItem('streakCount')) || 0;
        let lastLoginDate = localStorage.getItem('lastLoginDate') || "";

        // アプリ起動時：継続日数があれば表示
        window.onload = function() {
            if (streak > 0) {
                document.getElementById('streak-display-start').innerText = "現在 " + streak + "日 連続ログイン中！";
            }
        };

        // ID選択の処理
        function handleStartMode(mode) {
            if (mode === 'continue' && currentUserID) {
                // 同じIDでつづける場合：入力を省略して直接ログイン
                login(currentUserID);
            } else {
                // 新しいIDの場合：入力欄を表示
                document.getElementById('id-input-area').classList.remove('hidden');
                document.getElementById('user-id').focus();
            }
        }

        function confirmID() {
            const id = document.getElementById('user-id').value;
            if (id) login(id);
            else alert("IDを入力してください");
        }

        function login(id) {
            currentUserID = id;
            localStorage.setItem('lastUserID', id);
            updateStreak();
            
            document.getElementById('start-screen').classList.add('hidden');
            document.getElementById('menu-screen').classList.remove('hidden');
            document.getElementById('welcome-msg').innerText = "こんにちは、" + id + " さん";
            document.getElementById('streak-count').innerText = streak;
        }

        // 継続日数の計算
        function updateStreak() {
            const today = new Date().toLocaleDateString();
            if (lastLoginDate !== today) {
                const yesterday = new Date();
                yesterday.setDate(yesterday.getDate() - 1);
                
                if (lastLoginDate === yesterday.toLocaleDateString()) {
                    streak++; // 連続成功
                } else if (lastLoginDate === "") {
                    streak = 1; // 初回
                } else {
                    streak = 1; // 途切れた
                }
                lastLoginDate = today;
                localStorage.setItem('streakCount', streak);
                localStorage.setItem('lastLoginDate', lastLoginDate);
            }
        }

        // 練習画面の制御
        function startPractice() {
            document.getElementById('menu-screen').classList.add('hidden');
            document.getElementById('practice-screen').classList.remove('hidden');
            document.getElementById('hint-text').classList.add('hidden');
        }

        function showHint() {
            document.getElementById('hint-text').classList.remove('hidden');
        }

        function backToMenu() {
            document.getElementById('practice-screen').classList.add('hidden');
            document.getElementById('menu-screen').classList.remove('hidden');
        }

        function logout() {
            location.reload(); // スタート画面に戻る
        }
    </script>
</body>
</html>
"""
# --- アプリの統合と実行 ---
# 上記のHTMLとJSを結合して、Streamlitのコンポーネントとして出力します
full_html = html_start + js_code

# heightを調整して、画面が収まるようにします
components.html(full_html, height=550, scrolling=False)
