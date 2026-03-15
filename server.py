import socket
import cv2
import numpy as np

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 12345))
server_socket.listen(5)
print("Sunucu dinlemede")

client_socket, addr = server_socket.accept()
print(f"{addr} bağlandı!")

data = b""

while True:

    packet = client_socket.recv(4096)
    if not packet:
        break
    data += packet

    if len(data) >= 4:
        frame_size = int.from_bytes(data[:4], byteorder='big')
        if len(data) >= 4 + frame_size:
            frame_data = data[4:4+frame_size]
            data = data[4+frame_size:]

            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            cv2.imshow('Sunucu Goruntusu', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

client_socket.close()
server_socket.close()
cv2.destroyAllWindows()