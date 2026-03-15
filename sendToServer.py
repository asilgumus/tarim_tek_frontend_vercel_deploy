import camera
import socket
import sys

device_id = sys.argv[1] if len(sys.argv) > 1 else "0005"
device_id = device_id[:4].ljust(4)

import time

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

while True:
    try:
        client_socket.connect(('127.0.0.1', 12347))
        break
    except ConnectionRefusedError:
        print("Sunucu henüz hazır değil, tekrar deneniyor...")
        time.sleep(1)
    except Exception as e:
        print(f"Bağlantı hatası: {e}")
        time.sleep(2)

client_socket.send(device_id.encode('utf-8'))
for data, length in camera.streamCapture(label=device_id.strip()):
    client_socket.send(length.to_bytes(4, byteorder='big') + data)
