<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>学習アプリ - 継続・ヒント機能付き</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div id="app">
        <section id="start-screen">
            <h2>ようこそ</h2>
            <div class="stats-mini" id="streak-display-start"></div>
            <button onclick="handleStartMode('continue')">同じIDでつづける</button>
            <button onclick="handleStartMode('new')">新しいIDではじめる</button>
            
            <div id="id-input-area" class="hidden">
                <input type="text" id="user-id" placeholder="IDを入力してください">
                <button onclick="confirmID()">決定</button>
            </div>
        </section>

        <section id="menu-screen" class="hidden">
            <h2 id="welcome-msg"></h2>
            <div class="stats-card">
                <p>🔥 連続継続日数: <span id="streak-count">0</span>日</p>
            </div>
            <button onclick="startPractice()">練習をはじめる</button>
            <button onclick="logout()">戻る</button>
        </section>

        <section id="practice-screen" class="hidden">
            <h3>練習問題</h3>
            <div id="question-area">
                <p id="question-text">Q: 「バラスト」とは何のこと？</p>
                <button id="hint-btn" onclick="showHint()">ヒントを見る</button>
                <p id="hint-text" class="hidden">💡 ヒント：線路に敷いてあるアレです。</p>
            </div>
            <button onclick="backToMenu()">メニューに戻る</button>
        </section>
    </div>
    <script src="script.js"></script>
</body>
</html>
body { font-family: sans-serif; display: flex; justify-content: center; padding: 20px; background: #f0f2f5; }
#app { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 100%; max-width: 400px; text-align: center; }
.hidden { display: none; }
button { width: 100%; padding: 12px; margin: 10px 0; border: none; border-radius: 8px; cursor: pointer; background: #007bff; color: white; font-size: 16px; }
button:hover { background: #0056b3; }
.stats-card { background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; border: 1px solid #ffeeba; }
#hint-text { color: #666; font-style: italic; background: #e9ecef; padding: 10px; border-radius: 4px; margin-top: 10px; }
// --- 状態管理 ---
let currentUserID = localStorage.getItem('lastUserID') || "";
let streak = parseInt(localStorage.getItem('streakCount')) || 0;
let lastLoginDate = localStorage.getItem('lastLoginDate') || "";

// --- 起動時の処理 ---
window.onload = () => {
    if (streak > 0) {
        document.getElementById('streak-display-start').innerText = `現在 ${streak}日 連続中！`;
    }
};

// --- ID管理パート ---
function handleStartMode(mode) {
    if (mode === 'continue') {
        if (currentUserID) {
            // 前回のIDがあれば入力をスキップして直接ログイン
            login(currentUserID);
        } else {
            alert("保存されたIDが見つかりません。新しく作成してください。");
            document.getElementById('id-input-area').classList.remove('hidden');
        }
    } else {
        // 新しいID入力欄を表示
        document.getElementById('id-input-area').classList.remove('hidden');
        document.getElementById('user-id').value = "";
    }
}

function confirmID() {
    const inputID = document.getElementById('user-id').value;
    if (inputID) {
        login(inputID);
    } else {
        alert("IDを入力してください");
    }
}

function login(id) {
    currentUserID = id;
    localStorage.setItem('lastUserID', id);
    updateStreak();
    
    document.getElementById('start-screen').classList.add('hidden');
    document.getElementById('menu-screen').classList.remove('hidden');
    document.getElementById('welcome-msg').innerText = `ID: ${id} さん`;
    document.getElementById('streak-count').innerText = streak;
}

// --- 継続日数カウントパート ---
function updateStreak() {
    const today = new Date().toLocaleDateString();
    
    if (lastLoginDate === today) {
        // 今日すでにログイン済みなら何もしない
    } else {
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        
        if (lastLoginDate === yesterday.toLocaleDateString()) {
            streak++; // 連続更新
        } else {
            streak = 1; // 途切れた、または初回
        }
        lastLoginDate = today;
        localStorage.setItem('streakCount', streak);
        localStorage.setItem('lastLoginDate', lastLoginDate);
    }
}

// --- 練習・ヒントパート ---
function startPractice() {
    document.getElementById('menu-screen').classList.add('hidden');
    document.getElementById('practice-screen').classList.remove('hidden');
    document.getElementById('hint-text').classList.add('hidden'); // ヒントは隠しておく
}

function showHint() {
    document.getElementById('hint-text').classList.remove('hidden');
}

function backToMenu() {
    document.getElementById('practice-screen').classList.add('hidden');
    document.getElementById('menu-screen').classList.remove('hidden');
}

function logout() {
    document.getElementById('menu-screen').classList.add('hidden');
    document.getElementById('start-screen').classList.remove('hidden');
    document.getElementById('id-input-area').classList.add('hidden');
}
