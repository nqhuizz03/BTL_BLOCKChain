from flask import Flask, render_template, request, jsonify, send_from_directory, Response, stream_with_context
from ultralytics import YOLO
import os
import cv2
import pandas as pd
import csv
from datetime import datetime
import json
from werkzeug.utils import secure_filename
import time
from web3 import Web3
import numpy as np

app = Flask(__name__)

# Folder cấu hình
UPLOAD_FOLDER = 'static/uploads'
OUTPUT_FOLDER = 'static/outputs'
LOG_FILE = 'logs/violations.csv'
LOG_IMG_FOLDER = 'logs/images'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(LOG_IMG_FOLDER, exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Kết nối blockchain
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))  # Gan IP Ganache

with open("contract_abi.json") as f:
    abi = json.load(f)
contract_address = "0x7C4f41c48ED29Ccc73e5b2A7272A6C288256E7d4"
contract = w3.eth.contract(address=contract_address, abi=abi)

sender = "0x7C4f41c48ED29Ccc73e5b2A7272A6C288256E7d4"
private_key = "0x6c36cc0489e440e77abae225f3807ffba3ea78207d3c6fa0c2c3f916c9bff1d5"

# Load model YOLO
model = YOLO('best.pt')

latest_stats = {'with_helmet': 0, 'no_helmet': 0}

def send_violation_to_blockchain(ipfs_hash: str, description: str):
    try:
        nonce = w3.eth.get_transaction_count(sender)
        tx = contract.functions.reportViolation(ipfs_hash, description).build_transaction({
            'chainId': 1337,
            'gas': 2000000,
            'gasPrice': Web3.to_wei(20, 'gwei'),
            'nonce': nonce,
        })
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        sent_tx = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_hash = sent_tx.hex()
        print(f"Đã gửi giao dịch blockchain, tx_hash: {tx_hash}")
        return tx_hash
    except Exception as e:
        print(f"Lỗi gửi giao dịch blockchain: {e}")
        return None

def log_violations(results, frame):
    boxes = results.boxes
    if boxes is None or len(boxes) == 0:
        return None

    with_helmet = sum(int(cls_id) == 0 for cls_id in boxes.cls)
    no_helmet = sum(int(cls_id) == 1 for cls_id in boxes.cls)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    violation = "No Helmet" if no_helmet > 0 else "With Helmet"

    with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([now_str, violation])

    tx_hash = None
    if no_helmet > 0:
        img_name = f"violation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        img_path = os.path.join(LOG_IMG_FOLDER, img_name)
        if frame is not None:
            cv2.imwrite(img_path, frame)

        description = f"Vi phạm không đội mũ lúc {now_str}"
        ipfs_hash = "no-ipfs-hash"  # Thay bằng mã hash thật nếu có IPFS
        tx_hash = send_violation_to_blockchain(ipfs_hash, description)
    return tx_hash

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({"message": "No file uploaded"}), 400

        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)

        ext = filename.rsplit('.', 1)[-1].lower()
        is_image = ext in ['jpg', 'jpeg', 'png']
        is_video = ext in ['mp4', 'avi']

        if is_image:
            output_filename = 'result_' + filename
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            success, tx_hash = process_image(input_path, output_path)
        elif is_video:
            output_filename = 'result_' + os.path.splitext(filename)[0] + '.mp4'
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            success, tx_hash = process_video(input_path, output_path)
        else:
            return jsonify({"message": "Unsupported file type"}), 400

        if not success:
            return jsonify({"message": "Processing failed"}), 500

        violation_detected = tx_hash is not None

        response_data = {
            "output_filename": output_filename,
            "violation": violation_detected,
            "tx_hash": tx_hash
        }
        return jsonify(response_data)

    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route('/image/<filename>')
def serve_image(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

@app.route('/video/<filename>')
def serve_video(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

@app.route('/stream')
def stream():
    return render_template('stream.html')

@app.route('/video_feed')
def video_feed():
    ESP32_CAM_URL = "http://172.16.70.28/stream"  # Cập nhật IP của ESP32-CAM

    def generate():
        global latest_stats
        cap = cv2.VideoCapture(ESP32_CAM_URL)

        if not cap.isOpened():
            print("Không thể mở stream ESP32-CAM, kiểm tra lại URL hoặc kết nối mạng")
            blank = 255 * np.ones(shape=[480, 640, 3], dtype=np.uint8)
            _, jpeg = cv2.imencode('.jpg', blank)
            frame_bytes = jpeg.tobytes()
            while True:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                time.sleep(1)
        else:
            # Đã mở được stream, đọc thử frame đầu tiên
            ret, frame = cap.read()
            if ret and frame is not None:
                print("Đã lấy được frame từ stream")
            else:
                print("Stream mở được nhưng không đọc được frame, kiểm tra lại nguồn stream")

        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("Không đọc được frame từ stream, đang chờ lại...")
                time.sleep(0.1)
                continue

            results = model(frame)[0]
            boxes = results.boxes

            count_with_helmet = sum(int(cls_id) == 0 for cls_id in boxes.cls) if boxes else 0
            count_without_helmet = sum(int(cls_id) == 1 for cls_id in boxes.cls) if boxes else 0
            total_people = count_with_helmet + count_without_helmet

            frame_annotated = results.plot()
            text = f'Tổng: {total_people} (Đội mũ: {count_with_helmet}, Không đội mũ: {count_without_helmet})'
            cv2.putText(frame_annotated, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            tx_hash = log_violations(results, frame)

            _, jpeg = cv2.imencode('.jpg', frame_annotated)
            frame_bytes = jpeg.tobytes()

            latest_stats['with_helmet'] = count_with_helmet
            latest_stats['no_helmet'] = count_without_helmet

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')



    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stats')
def stats():
    if not os.path.exists(LOG_FILE):
        labels, values = [], []
    else:
        try:
            df = pd.read_csv(LOG_FILE, names=['time', 'violation'])
            df['time'] = pd.to_datetime(df['time'], errors='coerce')
            df = df.dropna(subset=['time'])
            df['date'] = df['time'].dt.date
            grouped = df.groupby('date').size()
            labels = [str(x) for x in grouped.index]
            values = grouped.values.tolist()
        except Exception as e:
            print("Lỗi đọc file CSV:", e)
            labels, values = [], []

    return render_template('stats.html', labels=labels, values=values)

@app.route('/stats_json')
def stats_json():
    if not os.path.exists(LOG_FILE):
        return jsonify({'labels': [], 'with_helmet': [], 'no_helmet': []})
    try:
        df = pd.read_csv(LOG_FILE, names=['time', 'violation'])
        df['time'] = pd.to_datetime(df['time'], errors='coerce')
        df = df.dropna(subset=['time'])
        df['date'] = df['time'].dt.date
        grouped = df.groupby(['date', 'violation']).size().unstack(fill_value=0)
        grouped = grouped.reindex(columns=['With Helmet', 'No Helmet'], fill_value=0)
        labels = [str(x) for x in grouped.index]
        return jsonify({
            'labels': labels,
            'with_helmet': grouped['With Helmet'].tolist(),
            'no_helmet': grouped['No Helmet'].tolist()
        })
    except Exception as e:
        print("Lỗi đọc file CSV:", e)
        return jsonify({'labels': [], 'with_helmet': [], 'no_helmet': []})

def process_image(input_path, output_path):
    try:
        img = cv2.imread(input_path)
        results = model(img)[0]
        annotated_img = results.plot()
        cv2.imwrite(output_path, annotated_img)
        tx_hash = log_violations(results, img)
        return True, tx_hash
    except Exception as e:
        print("Lỗi xử lý ảnh:", e)
        return False, None

def process_video(input_path, output_path):
    try:
        cap = cv2.VideoCapture(input_path)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = cap.get(cv2.CAP_PROP_FPS) or 20.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        tx_hash = None

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            results = model(frame)[0]
            annotated_frame = results.plot()
            out.write(annotated_frame)
            if tx_hash is None:
                tx_hash = log_violations(results, frame)

        cap.release()
        out.release()
        return True, tx_hash
    except Exception as e:
        print("Lỗi xử lý video:", e)
        return False, None

@app.route('/stats_stream')
def stats_stream():
    def event_stream():
        global latest_stats
        import time
        while True:
            data = {
                'time': datetime.now().strftime('%H:%M:%S'),
                'with_helmet': latest_stats.get('with_helmet', 0),
                'no_helmet': latest_stats.get('no_helmet', 0),
                'violation_list': []
            }
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(1)
    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
