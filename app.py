from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
# 開発中は適当な文字列で構いません
app.config['SECRET_KEY'] = 'your-very-secret-key-12345' 
socketio = SocketIO(app)

# このサンプルでは、全員が 'default_room' に参加することにします
ROOM = "default_room"

@app.route('/')
def index():
    """クライアント（index.html）を返す"""
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    """クライアントがルームに参加したときの処理"""
    # dataからusernameなどを取得できますが、今回はシンプルにします
    join_room(ROOM)
    print(f"User {request.sid} joined room: {ROOM}")
    
    # ルームに参加している（自分以外の）全員に通知
    emit('user_joined', {'sid': request.sid}, to=ROOM, skip_sid=request.sid)

@socketio.on('offer')
def handle_offer(data):
    """オファーを特定の相手（またはルーム全員）に転送する"""
    print(f"Received offer from {request.sid}")
    # 自分以外の全員に転送
    emit('offer', data, to=ROOM, skip_sid=request.sid)

@socketio.on('answer')
def handle_answer(data):
    """アンサーを特定の相手（またはルーム全員）に転送する"""
    print(f"Received answer from {request.sid}")
    # 自分以外の全員に転送
    emit('answer', data, to=ROOM, skip_sid=request.sid)

@socketio.on('candidate')
def handle_candidate(data):
    """ICE候補を特定の相手（またはルーム全員）に転送する"""
    print(f"Received candidate from {request.sid}")
    # 自分以外の全員に転送
    emit('candidate', data, to=ROOM, skip_sid=request.sid)

@socketio.on('disconnect')
def on_disconnect():
    """切断時の処理"""
    leave_room(ROOM)
    print(f"User {request.sid} disconnected")
    # 必要に応じて、退出したことをルーム内の他ユーザーに通知
    emit('user_left', {'sid': request.sid}, to=ROOM)


if __name__ == '__main__':
    # host='0.0.0.0' にすることで、ローカルネットワーク内の他のPCからもアクセス可能になります
    # （注：カメラの使用はHTTPSが推奨されますが、localhost開発中はHTTPでも動作します）
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)