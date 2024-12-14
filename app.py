from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import re
import subprocess
import traceback  # デバッグ用に追加
import requests  # 追加

app = Flask(__name__)
CORS(app)

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
            raise Exception("AppleScriptナリ！")
            
        return result.stdout
    except Exception as e:
        print(f"エラーが発生したナリ: {str(e)}")  # デバッグログ
        print(f"詳細なエラー情報: {traceback.format_exc()}")  # スタックトレースを出力
        raise  # エラーを再発生させる

# HTMLテンプレートを定義するナリ
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>AppleScript Static Text Parser</title>
    <meta charset="utf-8">
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
        textarea {
            width: 100%;
            height: 200px;
            margin: 10px 0;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
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
        button:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
        #result {
            margin-top: 20px;
            white-space: pre-wrap;
        }
        .error {
            color: red;
            margin-top: 10px;
            padding: 10px;
            border: 1px solid red;
            border-radius: 4px;
            background-color: #fff3f3;
        }
        .success {
            color: green;
            margin-top: 10px;
            padding: 10px;
            border: 1px solid green;
            border-radius: 4px;
            background-color: #f3fff3;
        }
        .debug {
            color: #666;
            margin-top: 10px;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
            background-color: #f9f9f9;
            font-family: monospace;
        }
        .result-box {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            margin-top: 10px;
        }
        .copy-btn {
            background-color: #6c757d;
            color: white;
            padding: 5px 10px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9em;
            float: right;
        }
        .copy-btn:hover {
            background-color: #5a6268;
        }
        .text-count {
            color: #6c757d;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
        .play-btn {
            background-color: #4CAF50;
            color: white;
            padding: 5px 10px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-left: 10px;
        }
        .play-btn:hover {
            background-color: #45a049;
        }
        .play-btn:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
        .audio-player {
            margin-top: 10px;
            width: 100%;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>AppleScript Static Text Parser ナリ！</h1>
        <div>
            <button id="captureBtn">文字起こし！</button>
            <button id="parseBtn">解析開始ナリ！</button>
        </div>
        <textarea id="inputText" placeholder="ここにAppleScriptの出力を貼り付けるナリ..."></textarea>
        <div id="result"></div>
        <div id="debug"></div>
        <audio id="audioPlayer" class="audio-player" controls style="display: none;">
            Your browser does not support the audio element.
        </audio>
    </div>

    <script>
        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(() => {
                debug('クリップボ���ドにコピーしたナリ！');
            }).catch(err => {
                debug(`コピーに失敗したナリ: ${err}`);
            });
        }

        function createResultBox(title, content, showCopy = true) {
            const box = document.createElement('div');
            box.className = 'result-box';
            
            if (showCopy) {
                const copyBtn = document.createElement('button');
                copyBtn.className = 'copy-btn';
                copyBtn.textContent = 'コピー';
                copyBtn.onclick = () => copyToClipboard(content);
                box.appendChild(copyBtn);
                
                // 再生ボタンを追加するナリ
                const playBtn = document.createElement('button');
                playBtn.className = 'play-btn';
                playBtn.textContent = '再生';
                playBtn.onclick = () => playText(content);
                box.appendChild(playBtn);
            }
            
            const titleElem = document.createElement('div');
            titleElem.className = 'text-count';
            titleElem.textContent = title;
            box.appendChild(titleElem);
            
            const contentElem = document.createElement('pre');
            contentElem.textContent = content;
            box.appendChild(contentElem);
            
            return box;
        }

        function debug(message) {
            console.log(message);
            const debugDiv = document.getElementById('debug');
            const timestamp = new Date().toLocaleTimeString('ja-JP');
            debugDiv.innerHTML += `<div class="debug">${timestamp}: ${message}</div>`;
        }

        document.getElementById('captureBtn').addEventListener('click', async () => {
            debug('文字起こしボタンがクリックされたナリ！');
            
            const textarea = document.getElementById('inputText');
            const result = document.getElementById('result');
            const captureBtn = document.getElementById('captureBtn');
            
            try {
                debug('サーバーにリクエストを送信するナリ...');
                captureBtn.disabled = true;
                captureBtn.textContent = '文字起こし中...';
                result.innerHTML = '<div class="success">文字起こしを開始するナリ...</div>';
                
                const response = await fetch('/capture', {
                    method: 'POST',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    }
                });
                
                debug(`サーバーからのレスポンス: ${response.status} ${response.statusText}`);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                debug('レスポンスデータを受信したナリ');
                
                if (data.error) {
                    result.innerHTML = `<div class="error">エラーナリ: ${data.error}</div>`;
                    debug(`エラーが発生したナリ: ${data.error}`);
                } else {
                    textarea.value = data.text;
                    result.innerHTML = '';
                    result.appendChild(createResultBox('文字起こし結果', data.text));
                    debug('文字起こしが成功したナリ！');
                }
            } catch (error) {
                result.innerHTML = `<div class="error">エラーが発生したナリ: ${error.message}</div>`;
                debug(`エラーが発生したナリ: ${error.message}`);
                console.error('エラー詳細:', error);
            } finally {
                captureBtn.disabled = false;
                captureBtn.textContent = '文字��こし！';
                debug('処理が完了したナリ');
            }
        });

        document.getElementById('parseBtn').addEventListener('click', async () => {
            debug('解析開始ボタンがクリックされたナリ！');
            
            const text = document.getElementById('inputText').value;
            const result = document.getElementById('result');
            
            if (!text.trim()) {
                result.innerHTML = '<div class="error">テキストが空ナリ！まずは文字起こしするナリ！</div>';
                debug('テキストが空ナリ！');
                return;
            }
            
            try {
                debug('解析リクエストを送信するナリ...');
                const response = await fetch('/parse', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ text })
                });
                
                debug(`サーバーからのレスポンス: ${response.status} ${response.statusText}`);
                const data = await response.json();
                
                if (data.error) {
                    result.innerHTML = `<div class="error">エラーナリ: ${data.error}</div>`;
                    debug(`エラーが発生したナリ: ${data.error}`);
                } else {
                    result.innerHTML = '';
                    result.appendChild(createResultBox(
                        `見つかったテキスト (${data.count}件)`,
                        data.static_texts.join('\\n')
                    ));
                    debug(`${data.count}件のテキストが見つかったナリ！`);
                }
            } catch (error) {
                result.innerHTML = `<div class="error">エラーが発生したナリ: ${error.message}</div>`;
                debug(`エラーが発生したナリ: ${error.message}`);
                console.error('エラー詳細:', error);
            }
        });

        async function playText(text) {
            try {
                debug('VOICEVOXで音声合成を開始するナリ...');
                const response = await fetch('/speak', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ text })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const audioBlob = await response.blob();
                const audioUrl = URL.createObjectURL(audioBlob);
                const audioPlayer = document.getElementById('audioPlayer');
                audioPlayer.src = audioUrl;
                audioPlayer.style.display = 'block';
                audioPlayer.play();
                
                debug('音声合成が完了したナリ！');
            } catch (error) {
                debug(`エラーが発生したナリ: ${error.message}`);
                alert(`音声合成でエラーが発生したナリ: ${error.message}`);
            }
        }
    </script>
</body>
</html>
'''

def extract_static_text(text):
    # デバッグ用にテキストの一部を表示するナリ
    print(f"解析対象テキスト（最初の100文字）: {text[:100]}")
    
    # より緩い正規表現パターンを定義するナリ
    patterns = [
        r'static text ([^"]+?) of (UI element|group|button)',  # クォートなしバージョン
        r'static text "([^"]+?)" of (UI element|group|button)',  # クォートありバージョン
    ]
    
    # マッチした結果を順番を保持して格納するナリ
    all_matches = []
    for pattern in patterns:
        matches = re.finditer(pattern, text)  # findallの代���りにfinditerを使うナリ
        print(f"パターン {pattern} でマッチを探すナリ！")
        for match in matches:
            # タプルの最初の要素（実際のテキスト）と位置を保存するナリ
            all_matches.append((match.group(1), match.start()))
    
    # 位置でソートして重複を除去するナリ
    seen = set()
    filtered_matches = []
    # 位置でソートするナリ
    for match, position in sorted(all_matches, key=lambda x: x[1]):
        # 前後の空白とクォートを削除するナリ
        cleaned = match.strip().strip('"')
        
        # 重複チェックするナリ
        if cleaned in seen:
            continue
        seen.add(cleaned)
        
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
        
        # 日本語のチャットメッセージらしい特徴を定義するナリ
        is_chat_message = (
            # 日本語の文末表現を含むナリ
            ('ナリ' in cleaned or 'です' in cleaned or 'ます' in cleaned or 
             'だよ' in cleaned or 'かな' in cleaned or 'よ！' in cleaned) or
            # 長い日本語テキストで、かつ句読点を含むナリ
            (len(cleaned) > 20 and 
             any(c in cleaned for c in 'ー-んァ-ン一-龯') and
             any(p in cleaned for p in '、。！？'))
        )
        
        # フィルタリング条件を追加するナリ
        if (cleaned and 
            len(cleaned) > 1 and 
            not any(keyword.lower() in cleaned.lower() for keyword in exclude_keywords) and
            is_chat_message):
            filtered_matches.append(cleaned)
    
    # 結果を整形するナリ
    formatted_results = []
    for match in filtered_matches:
        # 改行を含む場合は複数行として扱うナリ
        lines = match.split('\n')
        for line in lines:
            line = line.strip()
            if line and len(line) > 1:
                formatted_results.append(line)
    
    print(f"最終的に {len(formatted_results)} 件のテキストが見つかったナリ！")
    return formatted_results

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/capture', methods=['POST'])
def capture():
    try:
        print("\n=== 文字起こしを開始するナリ... ===")  # デバッグログ
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
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({'error': 'テキストがつからないナリ！'}), 400
        
    text = data['text']
    static_texts = extract_static_text(text)
    
    # 結果をカテゴリ分けするナリ
    categorized_results = {
        'messages': [],  # 長いメッセージ（20文字以上）
        'labels': []     # 短いラベル（20文字未満）
    }
    
    for text in static_texts:
        if len(text) >= 20:
            categorized_results['messages'].append(text)
        else:
            categorized_results['labels'].append(text)
    
    return jsonify({
        'static_texts': static_texts,
        'categorized': categorized_results,
        'count': len(static_texts)
    })

# VOICEVOXのエンドポイントを追加するナリ
@app.route('/speak', methods=['POST'])
def speak_text():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'テキストが見つからないナリ！'}), 400
            
        text = data['text']
        speaker = data.get('speaker', 3)  # デフォルトはずんだもん（あまあま）
        
        # 音声合成用のクエリを作成するナリ
        query_response = requests.post(
            'http://localhost:50021/audio_query',
            params={'text': text, 'speaker': speaker}
        )
        query_response.raise_for_status()
        query_data = query_response.json()
        
        # 話速を1.5倍に調整するナリ
        query_data['speedScale'] = 1.5
        
        # 音声合成を実行するナリ
        synthesis_response = requests.post(
            'http://localhost:50021/synthesis',
            params={'speaker': speaker},
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

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001, debug=True) 