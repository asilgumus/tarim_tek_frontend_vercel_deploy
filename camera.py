import cv2

def streamCapture(label=None):
   
    cap = cv2.VideoCapture(0)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue  

            if label:
                cv2.putText(frame, f"CIHAZ ID: {label}", (30, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                cv2.rectangle(frame, (20, 20), (350, 70), (0, 255, 0), 2)

            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            
            frame_data = buffer.tobytes()
            frame_len = len(frame_data)

            yield frame_data, frame_len  

    finally:
        cap.release()