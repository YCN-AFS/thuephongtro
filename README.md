# 🏠 BienHoa Rentals - Nền tảng cho thuê phòng trọ Biên Hòa

Nền tảng cho thuê phòng trọ toàn diện dành cho thành phố Biên Hòa, kết nối chủ nhà và người thuê thông qua giao diện thân thiện, đa ngôn ngữ và hiện đại.

## 🌟 Tính năng chính

### Cho người thuê nhà
- 🔍 **Tìm kiếm thông minh**: Lọc theo giá, vị trí, loại phòng, tiện nghi
- 💬 **Trợ lý AI**: Chatbot hỗ trợ tìm kiếm và tư vấn bằng công nghệ Gemini AI
- ⭐ **Đánh giá & nhận xét**: Xem đánh giá từ người thuê trước đó
- ❤️ **Danh sách yêu thích**: Lưu các bất động sản quan tâm
- 📱 **Liên hệ trực tiếp**: Gửi tin nhắn cho chủ nhà ngay trên nền tảng
- 🗺️ **Bản đồ tương tác**: Xem vị trí chính xác của bất động sản

### Cho chủ nhà
- 📝 **Đăng tin dễ dàng**: Tạo tin đăng với hình ảnh và mô tả chi tiết
- 📊 **Quản lý dashboard**: Theo dõi tất cả bất động sản của bạn
- 📸 **Upload nhiều hình ảnh**: Kéo thả để sắp xếp thứ tự hình ảnh
- 💬 **Nhận tin nhắn**: Quản lý các yêu cầu từ người thuê
- ✏️ **Chỉnh sửa linh hoạt**: Cập nhật thông tin bất động sản bất cứ lúc nào

## 🚀 Công nghệ sử dụng

- **Backend**: Python Flask
- **Database**: PostgreSQL
- **Authentication**: Google OAuth 2.0 + Replit Auth
- **AI Assistant**: Google Gemini AI API
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Maps**: Leaflet.js
- **File Upload**: Drag & Drop với Sortable.js

## 📋 Yêu cầu hệ thống

- Python 3.11+
- PostgreSQL
- Google OAuth credentials
- Gemini AI API key

## ⚡ Cài đặt nhanh

### 1. Clone dự án
```bash
git clone [repository-url]
cd bienhoa-rentals
```

### 2. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 3. Thiết lập biến môi trường
Tạo file `.env` với các thông tin sau:
```env
DATABASE_URL=postgresql://username:password@localhost/bienhoa_rentals
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
GEMINI_API_KEY=your_gemini_api_key
SESSION_SECRET=your_secret_key
```

### 4. Chạy ứng dụng
```bash
python main.py
```

Truy cập http://localhost:5000 để sử dụng ứng dụng.

## 🔧 Hướng dẫn thiết lập chi tiết

### Thiết lập Google OAuth

1. Truy cập [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Tạo dự án mới hoặc chọn dự án hiện có
3. Tạo "OAuth 2.0 Client ID"
4. Thêm domain của bạn vào "Authorized redirect URIs":
   ```
   https://your-domain.com/google_login/callback
   ```

### Thiết lập Gemini AI API

1. Truy cập [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Tạo API key mới
3. Thêm key vào biến môi trường `GEMINI_API_KEY`

### Cấu hình Database

```sql
-- Tạo database
CREATE DATABASE bienhoa_rentals;

-- Ứng dụng sẽ tự động tạo tables khi khởi chạy
```

## 📖 Hướng dẫn sử dụng

### Đối với người thuê nhà

1. **Đăng nhập**: Sử dụng Google Account hoặc Replit Auth
2. **Tìm kiếm**: 
   - Sử dụng thanh tìm kiếm trên trang chủ
   - Áp dụng bộ lọc theo nhu cầu
   - Sử dụng AI chatbot để được tư vấn
3. **Xem chi tiết**: Click vào bất động sản để xem thông tin đầy đủ
4. **Liên hệ**: Nhấn nút "Liên hệ chủ nhà" để gửi tin nhắn
5. **Đánh giá**: Để lại đánh giá sau khi thuê

### Đối với chủ nhà

1. **Đăng ký tài khoản**: Đăng nhập và chọn loại tài khoản "Chủ nhà"
2. **Đăng tin**: 
   - Truy cập "Dashboard chủ nhà"
   - Nhấn "Thêm bất động sản mới"
   - Điền thông tin chi tiết
   - Upload hình ảnh (kéo thả để sắp xếp)
3. **Quản lý**: Xem, chỉnh sửa, xóa các tin đăng trong dashboard
4. **Nhận tin nhắn**: Kiểm tra và trả lời tin nhắn từ người thuê

## 🎨 Tùy chỉnh giao diện

### Màu sắc chính
```css
:root {
  --primary: #FF5A5F;      /* Đỏ chính */
  --secondary: #00A699;    /* Xanh lá */
  --background: #F7F7F7;   /* Xám nhạt */
  --text: #484848;         /* Xám đậm */
}
```

### Responsive Design
- Mobile-first approach
- Bootstrap 5 grid system
- Tối ưu cho các thiết bị di động

## 🔒 Bảo mật

- OAuth 2.0 authentication
- CSRF protection
- SQL injection prevention
- XSS protection
- Secure session management

## 📊 Database Schema

### Bảng chính:
- `users`: Thông tin người dùng
- `properties`: Bất động sản
- `property_images`: Hình ảnh bất động sản
- `reviews`: Đánh giá
- `messages`: Tin nhắn
- `favorites`: Danh sách yêu thích

## 🐛 Troubleshooting

### Lỗi thường gặp:

**1. Lỗi kết nối database**
```bash
# Kiểm tra PostgreSQL đang chạy
sudo service postgresql status

# Restart PostgreSQL
sudo service postgresql restart
```

**2. Google OAuth không hoạt động**
- Kiểm tra redirect URI trong Google Console
- Đảm bảo credentials được thiết lập đúng

**3. AI Chatbot không phản hồi**
- Kiểm tra Gemini API key
- Kiểm tra quota API

## 🚀 Deployment

### Trên Replit
1. Import dự án vào Replit
2. Thiết lập secrets trong Replit Secrets
3. Chạy lệnh `python main.py`

### Trên VPS/Cloud
1. Clone source code
2. Cài đặt dependencies
3. Thiết lập reverse proxy (Nginx)
4. Sử dụng Gunicorn cho production:
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 main:app
```

## 📱 API Endpoints

### Công khai
- `GET /` - Trang chủ
- `GET /search` - Tìm kiếm bất động sản
- `GET /property/<id>` - Chi tiết bất động sản

### Yêu cầu đăng nhập
- `POST /property/create` - Tạo bất động sản mới
- `POST /property/<id>/contact` - Liên hệ chủ nhà
- `POST /property/<id>/review` - Đánh giá bất động sản

## 🤝 Đóng góp

1. Fork dự án
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## 📄 License

Dự án này được phân phối dưới MIT License. Xem file `LICENSE` để biết thêm chi tiết.

## 📧 Liên hệ

- Email: support@bienhoa-rentals.com
- Website: https://bienhoa-rentals.replit.app
- GitHub: [Repository Link]

## 🙏 Cảm ơn

- Google cho OAuth và Gemini AI API
- Bootstrap team cho framework UI
- Leaflet cho maps integration
- Replit cho hosting platform

---

💡 **Tip**: Để được hỗ trợ tốt nhất, hãy sử dụng AI chatbot trên trang web để được tư vấn tìm kiếm bất động sản phù hợp!