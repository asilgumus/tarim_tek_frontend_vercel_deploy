import cv2
import socket
import threading
import numpy as np
import random
import string
import subprocess
import sys
from flask import Flask, Response, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

streams = {}
streams_lock = threading.Lock()

registered_devices = set()

def generate_unique_id():
    while True:
        new_id = ''.join(random.choices(string.digits, k=4))
        if new_id not in registered_devices:
            registered_devices.add(new_id)
            return new_id

def handle_client(client_socket, addr):
    print(f"Yeni cihaz bağlantısı: {addr}")
    try:
        device_id_raw = client_socket.recv(4)
        if not device_id_raw:
            return
        
        device_id = device_id_raw.decode('utf-8').strip()
        print(f"CİHAZ ONAYLANDI -> ID: {device_id} | Adres: {addr}")

        data = b""
        while True:
            packet = client_socket.recv(8192)
            if not packet:
                break
            data += packet
            
            while len(data) >= 4:
                frame_size = int.from_bytes(data[:4], byteorder='big')
                if len(data) >= 4 + frame_size:
                    frame_data = data[4:4+frame_size]
                    data = data[4+frame_size:]
                    
                    with streams_lock:
                        streams[device_id] = frame_data
                else:
                    break
    except Exception as e:
        print(f"Cihaz hatası ({addr}): {e}")
    finally:
        print(f"Cihaz ayrıldı: {addr}")
        client_socket.close()

def socket_listener():
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('127.0.0.1', 12347))
        server_socket.listen(10)
        print("Backend Socket sunucusu dinlemede... (Adres: 127.0.0.1, Port: 12347)")
        
        while True:
            client_socket, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True)
            client_thread.start()
    except Exception as e:
        print(f"KRİTİK HATA: Socket sunucusu başlatılamadı: {e}")

def generate_frames(device_id):
    while True:
        with streams_lock:
            frame = streams.get(device_id)
        
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            import time
            time.sleep(0.1)

@app.route('/')
def health_check():
    return jsonify({
        "status": "online",
        "message": "AgriSense Backend API is running.",
        "endpoints": ["/register", "/video_feed/<id>"]
    })

@app.route('/register', methods=['POST', 'GET'])
def register():
    new_id = generate_unique_id()
    print(f"Yeni ID oluşturuldu: {new_id}")

    return jsonify({
        "status": "success",
        "device_id": new_id,
        "message": "ID başarıyla oluşturuldu. Cihazınızdan bu ID ile bağlanın.",
        "stream_url": f"/video_feed/{new_id}"
    })

@app.route('/upload_frame/<device_id>', methods=['POST'])
def upload_frame(device_id):
    if device_id not in registered_devices:
        registered_devices.add(device_id) 
    frame_data = request.data
    if frame_data:
        with streams_lock:
            streams[device_id] = frame_data
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error", "message": "No data received"}), 400

@app.route('/video_feed/<device_id>')
def video_feed(device_id):
    return Response(generate_frames(device_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_frame/<device_id>')
def video_frame_fallback(device_id):
    return video_feed(device_id)

if __name__ == '__main__':
    t = threading.Thread(target=socket_listener, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=5050, debug=False, threaded=True)


