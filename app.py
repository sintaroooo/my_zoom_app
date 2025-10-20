from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-very-secret-key-12345' 
socketio = SocketIO(app)

ROOM = "default_room"

# サーバー側で参加者情報を記憶する辞書
# { sid: username } の形式で保存
participants = {}

@app.route('/')
def index():
    """クライアント（index.html）を返す"""
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    """クライアントがルームに参加したときの処理"""
    # クライアントから送られてきた 'username' を取得
    username = data.get('username', f"User-{request.sid[:4]}") # 名前がなければ仮の名前
    
    join_room(ROOM)
    
    # サーバーに参加者情報を保存
    participants[request.sid] = username
    
    print(f"User {username} ({request.sid}) joined room: {ROOM}")
    
    # -----------------------------------------------------
    # ★変更点 1: 既存の参加者リストを、新しく参加した人にだけ送る
    # -----------------------------------------------------
    existing_users = []
    for sid, name in participants.items():
        if sid != request.sid: # 自分自身は含めない
            existing_users.append({'sid': sid, 'username': name})
            
    emit('current_users', {'users': existing_users}, to=request.sid)
    
    # -----------------------------------------------------
    # ★変更点 2: 新参加者の名前も一緒に全員に通知
    # -----------------------------------------------------
    emit('user_joined', {
        'sid': request.sid,
        'username': username
    }, to=ROOM, skip_sid=request.sid)

@socketio.on('offer')
def handle_offer(data):
    target_sid = data.get('target_sid')
    if target_sid:
        emit('offer', { 'sdp': data.get('sdp'), 'from_sid': request.sid }, to=target_sid)
@socketio.on('answer')
def handle_answer(data):
    target_sid = data.get('target_sid')
    if target_sid:
        emit('answer', { 'sdp': data.get('sdp'), 'from_sid': request.sid }, to=target_sid)
@socketio.on('candidate')
def handle_candidate(data):
    target_sid = data.get('target_sid')
    if target_sid:
        emit('candidate', { 'candidate': data.get('candidate'), 'from_sid': request.sid }, to=target_sid)
# (中略ココまで)

# チャット機能も変更ありません
@socketio.on('send_message')
def handle_chat_message(data):
    message = data.get('message')
    username = participants.get(request.sid, request.sid[:4]) # ★名前を使うように変更
    if message:
        print(f"Chat from {username}: {message}")
        emit('receive_message', {
            'message': message,
            'from_sid': request.sid,
            'username': username # ★名前も送る
        }, to=ROOM)

@socketio.on('disconnect')
def on_disconnect():
    """切断時の処理"""
    # サーバーから参加者情報を削除
    username = participants.pop(request.sid, request.sid) # .popで削除
    
    print(f"User {username} ({request.sid}) disconnected")
    leave_room(ROOM)
    
    # ルーム内の全員に、誰が退出したかを通知
    emit('user_left', {'sid': request.sid}, to=ROOM, skip_sid=request.sid)


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)