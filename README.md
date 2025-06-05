<h2 align="center">
    <a href="https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin">
        🎓 Khoa Công nghệ Thông tin - Đại học Đại Nam
    </a>
</h2>

<h2 align="center">
    HỆ THỐNG PHÁT HIỆN GIAN LẬN TRONG THI CỬ BẰNG TRÍ TUỆ NHÂN TẠO
</h2>

<p align="center">
  <img src="https://scontent.fhan2-4.fna.fbcdn.net/v/t39.30808-6/474727433_1139319028194954_4417819820655219281_n.jpg?_nc_cat=100&ccb=1-7&_nc_sid=a5f93a&_nc_ohc=wRS0aRu9vVYQ7kNvwE-wFHt&_nc_oc=AdnJ5FsI68ddT2kw2bM3T8CNAfNN5t9YN_KjyF8KVk8egEitB0CnEJ0Ptz6Dpt8hAQs&_nc_zt=23&_nc_ht=scontent.fhan2-4.fna&_nc_gid=mMrFbffxizzpDtuY61nJPg&oh=00_AfMFGj_tchHbBwQtwDVpZHZer9LimOPKJbrmyY6qIHZu6A&oe=68479250" alt="AI Exam Monitoring System" width="600"/>
</p>

<p align="center">
  <a href="https://www.facebook.com/DNUAIoTLab">
    <img src="https://img.shields.io/badge/AIoTLab-green?style=for-the-badge" alt="AIoTLab" />
  </a>
  <a href="https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin">
    <img src="https://img.shields.io/badge/Khoa%20Công%20nghệ%20Thông%20tin-blue?style=for-the-badge" alt="Khoa CNTT" />
  </a>
  <a href="https://dainam.edu.vn">
    <img src="https://img.shields.io/badge/Đại%20học%20Đại%20Nam-orange?style=for-the-badge" alt="Đại học Đại Nam" />
  </a>
</p>


# 🚨 Helmet Violation Detection System using YOLOv8, ESP32-CAM, Flask & Blockchain

Hệ thống này giám sát người tham gia giao thông trong thời gian thực để phát hiện các vi phạm như **không đội mũ bảo hiểm**, đồng thời ghi lại vi phạm lên **Blockchain** (Ethereum) và hiển thị thông tin trên giao diện web.

## 📌 Tính năng chính

* 📷 **Nhận diện mũ bảo hiểm** qua mô hình YOLOv8 từ ảnh, video, hoặc luồng trực tiếp từ ESP32-CAM.
* 📊 **Thống kê vi phạm** theo ngày (tổng, có mũ, không có mũ).
* ⛓️ **Lưu vi phạm lên Blockchain** (Ganache + Web3.py).
* 🌐 **Giao diện web Flask** hiển thị ảnh/video xử lý, thống kê biểu đồ, luồng camera trực tiếp.
* 🧠 Tích hợp dễ dàng mô hình `best.pt` huấn luyện từ Roboflow.

---

## 🧩 Cấu trúc thư mục

```
.
├── static/
│   ├── uploads/        # Lưu file ảnh/video đầu vào
│   ├── outputs/        # Lưu ảnh/video đã xử lý
├── logs/
│   ├── images/         # Lưu ảnh vi phạm
│   └── violations.csv  # Ghi log vi phạm (thời gian, loại vi phạm)
├── templates/
│   ├── index.html      # Trang chủ upload
│   ├── stream.html     # Xem camera trực tiếp
│   └── stats.html      # Xem thống kê biểu đồ
├── best.pt             # Mô hình YOLOv8 đã huấn luyện
├── contract_abi.json   # ABI của smart contract Ethereum
├── app.py              # Toàn bộ backend Flask
└── README.md           # File mô tả này
```

---

## ⚙️ Cài đặt

### 1. Cài đặt thư viện cần thiết:

```bash
pip install flask opencv-python ultralytics web3 pandas numpy
```

### 2. Khởi tạo Ganache (Ethereum local):

* Tải và chạy Ganache.
* Lấy địa chỉ ví và private key cho tài khoản đầu tiên.
* Deploy smart contract (đã có ABI trong `contract_abi.json`).
* Cập nhật:

  * `contract_address`
  * `sender`
  * `private_key`

### 3. Chạy ứng dụng Flask:

```bash
python app.py
```

Truy cập tại: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🎥 Kết nối ESP32-CAM

* Cập nhật IP stream ESP32-CAM trong `app.py`:

```python
ESP32_CAM_URL = "http://<ip-của-ESP32>/stream"
```

---

## 🚀 Các API chính

| Endpoint      | Mô tả                          |
| ------------- | ------------------------------ |
| `/`           | Giao diện upload ảnh/video     |
| `/upload`     | Xử lý file gửi lên (ảnh/video) |
| `/stream`     | Giao diện xem livestream ESP32 |
| `/video_feed` | API cung cấp MJPEG stream      |
| `/stats`      | Hiển thị biểu đồ thống kê      |
| `/stats_json` | Dữ liệu JSON thống kê          |

---

## 📈 Log & Blockchain

* Vi phạm không đội mũ sẽ:

  * Lưu ảnh tại `logs/images`
  * Ghi dòng log vào `logs/violations.csv`
  * Gửi mô tả lên Ethereum smart contract.

---

## 🛠️ Gợi ý mở rộng

* ✅ Kết nối IPFS để lưu ảnh vi phạm phi tập trung.
* ✅ Thêm chức năng gửi cảnh báo qua Telegram/email.
* ✅ Triển khai lên server thật (VPS) với HTTPS.
* ✅ Huấn luyện lại mô hình YOLO với tập dữ liệu lớn hơn.

---

## 📷 Demo (gợi ý thêm ảnh/video nếu cần)



