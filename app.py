from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import re
import subprocess
import traceback  # デバッグ用に追加
import requests  # 追加
import sqlite3  # 追加

app = Flask(__name__)
CORS(app)

# データベースの初期化
def init_db():
    conn = sqlite3.connect('claude_texts.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS captured_texts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT UNIQUE,
            first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_displayed BOOLEAN DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# テキストが既に存在するかチェックするナリ
def is_text_exists(text):
    conn = sqlite3.connect('claude_texts.db')
    c = conn.cursor()
    c.execute('SELECT 1 FROM captured_texts WHERE text = ?', (text,))
    result = c.fetchone() is not None
    conn.close()
    return result

# 新規テキストを追加または更新するナリ
def add_or_update_text(text):
    conn = sqlite3.connect('claude_texts.db')
    c = conn.cursor()
    try:
        # 新規テキストを追加するナリ
        c.execute('''
            INSERT INTO captured_texts (text, is_displayed) 
            VALUES (?, 0) 
            ON CONFLICT(text) DO UPDATE SET 
            last_seen_at = CURRENT_TIMESTAMP
        ''', (text,))
        conn.commit()
        return True
    finally:
        conn.close()

# 未表示のテキストを取得するナリ
def get_undisplayed_texts():
    conn = sqlite3.connect('claude_texts.db')
    c = conn.cursor()
    try:
        c.execute('''
            SELECT text 
            FROM captured_texts 
            WHERE is_displayed = 0
            ORDER BY first_seen_at ASC
        ''')
        texts = [row[0] for row in c.fetchall()]
        
        # 取得したテキストを表示済みにマークするナリ
        if texts:
            c.execute('''
                UPDATE captured_texts 
                SET is_displayed = 1 
                WHERE text IN ({})
            '''.format(','.join(['?'] * len(texts))), texts)
            conn.commit()
        
        return texts
    finally:
        conn.close()

# 最近取得したテキストを取得するナリ（全履歴用）
def get_recent_texts(limit=100):
    conn = sqlite3.connect('claude_texts.db')
    c = conn.cursor()
    c.execute('''
        SELECT text 
        FROM captured_texts 
        ORDER BY last_seen_at DESC 
        LIMIT ?
    ''', (limit,))
    texts = [row[0] for row in c.fetchall()]
    conn.close()
    return texts

# アプリケーション起動時にDBを初期化するナリ
init_db()

def run_applescript():
    try:
        print("AppleScriptを実行するナリ...")  # デバッグログ
        # -eオプションを使って直接実行するナリ
        cmd = ['osascript', '-e', 
            'tell application "System Events" to tell process "Claude" to set uiElements to entire contents of window 1'
        ]
        print(f"実行するコマンド: {' '.join(cmd)}")  # デバッグログ
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(f"終了コード: {result.returncode}")  # デバッグログ
        print(f"標準出力: {result.stdout}")  # デバッグログ
        print(f"標準エラー: {result.stderr}")  # デバッグログ
        
        if result.returncode != 0:
            raise Exception(f"AppleScript実行エラー: {result.stderr}")
            
        if not result.stdout:
            raise Exception("AppleScriptの出力が空ナリ！")
            
        return result.stdout
    except Exception as e:
        print(f"エラーが発生したナリ: {str(e)}")  # デバッグログ
        print(f"詳細なエラー情報: {traceback.format_exc()}")  # スタックトレースを出力
        raise  # エラーを再発生させる

# DBの内容を取得するナリ
def get_all_texts():
    conn = sqlite3.connect('claude_texts.db')
    c = conn.cursor()
    c.execute('''
        SELECT id, text, first_seen_at, last_seen_at, is_displayed 
        FROM captured_texts 
        ORDER BY last_seen_at DESC
    ''')
    rows = c.fetchall()
    texts = [
        {
            'id': row[0],
            'text': row[1],
            'first_seen_at': row[2],
            'last_seen_at': row[3],
            'is_displayed': bool(row[4])  # SQLiteのBOOLEANを Python のboolに変換
        }
        for row in rows
    ]
    conn.close()
    return texts

@app.route('/db_status', methods=['GET'])
def db_status():
    try:
        texts = get_all_texts()
        return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head>
                <title>DB Status</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        max-width: 1200px;
                        margin: 0 auto;
                        padding: 20px;
                    }
                    table {
                        width: 100%;
                        border-collapse: collapse;
                        margin-top: 20px;
                    }
                    th, td {
                        padding: 8px;
                        border: 1px solid #ddd;
                        text-align: left;
                    }
                    th {
                        background-color: #4CAF50;
                        color: white;
                    }
                    tr:nth-child(even) {
                        background-color: #f2f2f2;
                    }
                    .text-cell {
                        max-width: 500px;
                        overflow-wrap: break-word;
                    }
                    .displayed {
                        color: #4CAF50;
                        font-weight: bold;
                    }
                    .not-displayed {
                        color: #f44336;
                    }
                </style>
            </head>
            <body>
                <h1>DB Status 📊</h1>
                <p>Total records: {{ texts|length }}</p>
                <table>
                    <tr>
                        <th>ID</th>
                        <th>Text</th>
                        <th>First Seen</th>
                        <th>Last Seen</th>
                        <th>Displayed</th>
                    </tr>
                    {% for text in texts %}
                    <tr>
                        <td>{{ text.id }}</td>
                        <td class="text-cell">{{ text.text }}</td>
                        <td>{{ text.first_seen_at }}</td>
                        <td>{{ text.last_seen_at }}</td>
                        <td class="{{ 'displayed' if text.is_displayed else 'not-displayed' }}">
                            {{ '✅ Yes' if text.is_displayed else '❌ No' }}
                        </td>
                    </tr>
                    {% endfor %}
                </table>
            </body>
            </html>
        ''', texts=texts)
    except Exception as e:
        return f"エラーが発生したナリ: {str(e)}", 500

# HTMLテンプレートを定義するナリ
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Claude Voice</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        #output {
            white-space: pre-wrap;
            margin: 20px 0;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            max-height: 300px;
            overflow-y: auto;
        }
        .controls {
            margin: 20px 0;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 10px;
        }
        button:hover {
            background-color: #45a049;
        }
        .status {
            margin-top: 10px;
            color: #666;
        }
        #newOutput {
            background-color: white;
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            border: 1px solid #ddd;
            max-height: 400px;
            overflow-y: auto;
        }
        .new-text-block {
            background-color: #e8f5e9;
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            border: 1px solid #c8e6c9;
            animation: fadeIn 0.5s ease-in;
        }
        .new-text-block .timestamp {
            color: #666;
            font-size: 0.8em;
            margin-bottom: 5px;
        }
        .new-text-block .text {
            white-space: pre-wrap;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .db-status-link {
            display: inline-block;
            margin-left: 10px;
            color: #666;
            text-decoration: none;
        }
        .db-status-link:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Claude Voice 🎤 <a href="/db_status" class="db-status-link" target="_blank">📊 DB Status</a></h1>
        <div class="controls">
            <button onclick="toggleAutoUpdate()" id="autoUpdateBtn">自動更新開始</button>
            <button onclick="captureText()">テキスト取得</button>
        </div>
        <div class="status">ステータス: <span id="status">待機中...</span></div>
        <h2>新規テキスト</h2>
        <div id="newOutput"></div>
        <h2>全テキスト履歴</h2>
        <div id="output"></div>
    </div>

    <script>
        let isAutoUpdating = false;
        let updateInterval;

        function toggleAutoUpdate() {
            const btn = document.getElementById('autoUpdateBtn');
            if (isAutoUpdating) {
                clearInterval(updateInterval);
                isAutoUpdating = false;
                btn.textContent = '自動更新開始';
                updateStatus('自動更新停止');
            } else {
                isAutoUpdating = true;
                btn.textContent = '自動更新停止';
                updateStatus('自動更新開始');
                captureText();
                updateInterval = setInterval(captureText, 3000);
            }
        }

        function updateStatus(message) {
            document.getElementById('status').textContent = message;
        }

        async function captureText() {
            try {
                updateStatus('テキスト取得中...');
                const response = await fetch('/capture', {
                    method: 'POST'
                });
                const data = await response.json();

                if (data.error) {
                    throw new Error(data.error);
                }

                const parseResponse = await fetch('/parse', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ text: data.text })
                });
                const parsedData = await parseResponse.json();

                if (parsedData.error) {
                    throw new Error(parsedData.error);
                }

                // 新規テキストを表示するナリ
                if (parsedData.new_texts.length > 0) {
                    const newOutput = document.getElementById('newOutput');
                    
                    // 新規テキストを追加表示するナリ
                    const timestamp = new Date().toLocaleTimeString('ja-JP');
                    const newContent = document.createElement('div');
                    newContent.className = 'new-text-block';
                    newContent.innerHTML = `
                        <div class="timestamp">${timestamp}</div>
                        <div class="text">${parsedData.new_texts.join('\\n')}</div>
                    `;
                    
                    // 最新のテキストを上に表示するナリ
                    if (newOutput.firstChild) {
                        newOutput.insertBefore(newContent, newOutput.firstChild);
                    } else {
                        newOutput.appendChild(newContent);
                    }

                    // 全履歴を表示するナリ
                    const output = document.getElementById('output');
                    output.textContent = parsedData.static_texts.join('\\n');
                    
                    updateStatus(`新規テキスト ${parsedData.new_texts.length}件を取得`);
                } else {
                    console.log('新規テキストなし、表示を更新しないナリ');
                    updateStatus('新規テキストなし');
                }
                
            } catch (error) {
                console.error('エラー:', error);
                updateStatus(`エラー: ${error.message}`);
            }
        }
    </script>
</body>
</html>
'''

def extract_static_text(text):
    # デバッグ用にテキストの一部を表示するナリ
    print(f"解析対象テキスト（最初の100文字）: {text[:100]}")
    
    # AppleScriptの出力から静的テキストを抽出するための正規表現パターンナリ
    patterns = [
        r'static text ([^"]+?) of (UI element|group|button)',  # クォートなしバージョン
        r'static text "([^"]+?)" of (UI element|group|button)',  # クォートありバージョン
    ]
    
    # ===== フェーズ1: テキストの抽出と初期重複チェック =====
    all_matches = []          # 抽出したテキストと位置情報を保持するリストナリ
    seen_texts = set()        # 初期段階での重複チェック用セットナリ
    
    # 各パターンでテキストを抽出するナリ
    for pattern in patterns:
        matches = re.finditer(pattern, text)  # テキストの位置情報も取得するナリ
        print(f"パターン {pattern} でマッチを探すナリ！")
        for match in matches:
            # テキストを取得して整形（前後の空白とクォートを削除）するナリ
            matched_text = match.group(1).strip().strip('"')
            
            # フェーズ1の重複チェック: 同じテキス��既に抽出されていないか確認するナリ
            if matched_text not in seen_texts:
                seen_texts.add(matched_text)
                # テキストと元の位置を保存（位置は後でソートに使用）するナリ
                all_matches.append((matched_text, match.start()))
    
    # ===== フェーズ2: 位置でソート =====
    # 画面上の表示順序を維持するために、テキストの出現位置でソートするナリ
    all_matches.sort(key=lambda x: x[1])
    
    # ===== フェーズ3: フィルタリングと最終重複チェック =====
    # 除外するキーワードのリストを定義するナリ
    exclude_keywords = [
        'of group', 'static text', 'UI element', 'button', 'image',
        'Copy', 'Edit', 'Retry', 'Font', 'Add', 'View all', 'Learn more',
        'Choose style', 'Chat styles', 'Chat controls', 'Content',
        'Projects', 'Starred', 'Recents', 'Help & support',
        'Professional plan', 'Start new chat', '⌥Space', 'Space',
        'No content added yet', 'Reply to Claude', 'mkdir', 'bash',
        'KY', '31', '-p', 'github/test', 'Please double-check responses',
        'Loading is taking longer', 'The code itself may', 'There may be an issue'
    ]
    
    # 最終的な結果を格納するリス���と重複チェック用セットナリ
    formatted_results = []    # 最終的な結果を格納するリストナリ
    seen_results = set()      # 最終段階での重複チェック用セットナリ
    
    # ソートされたテキストを順番に処理するナリ
    for text, _ in all_matches:  # 位置情報(_)は不要なので無視するナリ
        # 日本語のチャットメッセージらしい特徴をチェックするナリ
        is_chat_message = (
            # 条件1: 日本語の文末表現を含むナリ
            ('ナリ' in text or 'です' in text or 'ます' in text or 
             'だよ' in text or 'かな' in text or 'よ！' in text) or
            # 条件2: 長い日本語テキストで、かつ句読点を含むナリ
            (len(text) > 20 and 
             any(c in text for c in 'ー-んァ-ン一-龯') and  # 日本語文字を含むナリ
             any(p in text for p in '、。！？'))            # 句読点を含むナリ
        )
        
        # フィルタリング条件をすべてチェックするナリ
        if (text and                                                          # 空でない
            len(text) > 1 and                                                # 2文字以上
            not any(keyword.lower() in text.lower() for keyword in exclude_keywords) and  # 除外キーワードを含まない
            is_chat_message and                                              # 日本語メッセージの特徴がある
            text not in seen_results):                                       # まだ追加されていない
            
            # 改行で分割して各行を個別に処理するナリ
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                # 各行に対しても同様のチェックを行うナリ
                if line and len(line) > 1 and line not in seen_results:
                    seen_results.add(line)          # 重複チェック用セットに追加
                    formatted_results.append(line)   # 結果リストに追加
    
    print(f"最終的に {len(formatted_results)} 件のテキストが見つかったナリ！")
    return formatted_results

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/capture', methods=['POST'])
def capture():
    try:
        print("\n=== 文字起こし開始するナリ... ===")  # デバッグログ
        text = run_applescript()
        print("文字起こしが完了したナリ！")  # デバッグログ
        print(f"取得したテキスト: {text[:100]}...")  # 最初の100文字だけ表示
        return jsonify({'text': text})
    except Exception as e:
        error_msg = f"エラーが発生したナリ: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)  # デバッグログ
        return jsonify({'error': error_msg}), 500

@app.route('/parse', methods=['POST'])
def parse_applescript():
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'テキストがないナリ！'}), 400
            
        text = data['text']
        
        # テキストがHTML形式の場合はエラーを返すナリ
        if text.strip().startswith('<!DOCTYPE') or text.strip().startswith('<html'):
            return jsonify({'error': 'HTMLが返されたナリ！再試行してほしいナリ！'}), 400
            
        static_texts = extract_static_text(text)
        
        # 全てのテキストをDBに保存するナリ
        for text in static_texts:
            add_or_update_text(text)
        
        # 未表示のテキストを取得するナリ
        new_texts = get_undisplayed_texts()
        
        # 全履歴用のテキストを取得するナリ
        recent_texts = get_recent_texts()
        
        return jsonify({
            'static_texts': recent_texts,  # 全履歴用
            'new_texts': new_texts,        # 新規（未表示）テキスト用
            'count': len(new_texts)
        })
    except Exception as e:
        error_msg = f"パースでエラーが発生したナリ: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)  # デバッグログ
        return jsonify({'error': error_msg}), 500

# VOICEVOXのエンドポイントを追加するナリ
@app.route('/speak', methods=['POST'])
def speak_text():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'テキストが見つからないナリ！'}), 400
            
        text = data['text']
        
        # スタイルIDを取得するナリ
        speakers_response = requests.get('http://127.0.0.1:10101/speakers')
        speakers_response.raise_for_status()
        speakers_data = speakers_response.json()
        
        # korosukeの声を探すナリ
        style_id = None
        for speaker in speakers_data:
            if speaker['name'] == 'korosuke':
                style_id = speaker['styles'][0]['id']  # korosukeのノーマルスタイルを使うナリ
                break
        
        if style_id is None:
            raise Exception('korosukeの声が見つからないナリ！')
        
        # 音声合成用のクリを作成するナリ
        query_response = requests.post(
            'http://127.0.0.1:10101/audio_query',
            params={'text': text, 'speaker': style_id}
        )
        query_response.raise_for_status()
        query_data = query_response.json()
        
        # 話速を1.0倍に調するナリ
        query_data['speedScale'] = 1.0
        
        # 音声合成を実行するナ
        synthesis_response = requests.post(
            'http://127.0.0.1:10101/synthesis',
            params={'speaker': style_id},
            json=query_data
        )
        synthesis_response.raise_for_status()
        
        # 音声データを返すナリ
        return synthesis_response.content, 200, {
            'Content-Type': 'audio/wav',
            'Content-Disposition': 'attachment; filename=voice.wav'
        }
        
    except requests.exceptions.RequestException as e:
        error_msg = f"VOICEVOXとの通信でエラーが発生したナリ: {str(e)}"
        print(error_msg)
        return jsonify({'error': error_msg}), 500
    except Exception as e:
        error_msg = f"予期せぬエラーが発生したナリ: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return jsonify({'error': error_msg}), 500

# 再生済みチェックのエンドポイントを追加するナリ
@app.route('/check_played', methods=['POST'])
def check_played():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'テキストが見つからないナリ！'}), 400
    
    text = data['text']
    played = is_text_exists(text)
    return jsonify({'played': played})

# 再生済みマークのエンドポイントを追加するナリ
@app.route('/mark_played', methods=['POST'])
def mark_played():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'テキストが見つからないナリ！'}), 400
    
    text = data['text']
    add_or_update_text(text)
    return jsonify({'success': True})

if __name__ == '__main__':
    # アプリケーション起動時にDBを初期化するナリ
    print("DBを初期化するナリ！")
    init_db()
    app.run(host='127.0.0.1', port=5001, debug=True) 