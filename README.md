# 🎓 RAG Learning Assistant - Hệ Thống Gợi ý Khóa Học Thông Minh

## 📖 Giới Thiệu

**RAG Learning Assistant** là ứng dụng AI sử dụng kỹ thuật RAG (Retrieval-Augmented Generation) để phân tích hồ sơ người dùng và gợi ý khóa học phù hợp. Hệ thống tích hợp quiz đánh giá trình độ trước và sau khi học để đo lường sự tiến bộ.

![RAG Learning Assistant](https://img.shields.io/badge/Status-Ready%20for%20Demo-success)
![Tech Stack](https://img.shields.io/badge/Stack-React%20%7C%20FastAPI%20%7C%20OpenAI-blue)

## ✨ Tính Năng Chính

### 🎯 Đánh giá Trình Độ Thông Minh

- **Pre-Quiz**: Bài kiểm tra đầu vào được tạo tự động bằng AI dựa trên profile
- **Post-Quiz**: Bài kiểm tra sau khi học để đánh giá tiến bộ
- **So sánh kết quả**: Theo dõi sự cải thiện qua các bài quiz

### 🎓 Gợi ý Khóa Học AI-Powered

- **Phân tích profile**: Đọc và phân tích CV/profile người dùng
- **Semantic Search**: Tìm kiếm khóa học dựa trên vector embeddings
- **Đề xuất cá nhân hóa**: Khóa học phù hợp với trình độ và mục tiêu

### 🤖 Công Nghệ AI Tiên Tiến

- **OpenAI GPT-4o-mini**: Tạo quiz và xử lý văn bản thông minh
- **RAG Pipeline**: Kết hợp retrieval và generation
- **Vector Database**: Lưu trữ và tìm kiếm embeddings

## 🏗️ Kiến Trúc Hệ Thống

```
course_recomendation/
├── 📱 react/                          # Frontend React + Next.js
│   ├── src/
│   │   ├── app/                      # Next.js app router
│   │   ├── components/               # UI components
│   │   │   ├── Layout.tsx
│   │   │   ├── ProfileUpload.tsx
│   │   │   ├── QuizComponent.tsx
│   │   │   └── CourseRecommendations.tsx
│   │   └── lib/
│   │       └── api.ts               # API client
│   └── package.json
├── 🐍 backend/                       # Python FastAPI Backend
│   ├── main.py                      # FastAPI server
│   ├── requirements.txt
│   ├── services/                    # Business logic
│   │   ├── quiz_service.py
│   │   ├── course_service.py
│   │   └── rag_service.py
│   └── utils/
│       ├── openai_client.py
│       └── vector_store.py
└── 📚 shared/                       # Shared resources
    ├── data/
    │   └── courses.json            # Database khóa học
    ├── vectorstore/
    │   └── embedded_docs.json     # Vector embeddings
    ├── ingestion/                 # Data processing
    │   ├── load_data.py
    │   ├── chunking.py
    │   └── embed_documents.py
    └── profile.txt               # User profile mẫu
```

## 🚀 Cài Đặt & Chạy Ứng Dụng

### Prerequisites

- Node.js 18+
- Python 3.11+
- OpenAI API key

### 1. Clone và Thiết Lập

```bash
# Clone repository (nếu có)
git clone <repository-url>
cd course_recomendation
```

### 2. Backend Setup

```bash
# Chuyển đến thư mục backend
cd backend

# Tạo virtual environment
python -m venv venv

AZURE_OPENAI_EMBEDDING_ENDPOINT=......
AZURE_OPENAI_EMBEDDING_API_KEY=.......
AZURE_OPENAI_EMBED_MODEL=.......
AZURE_OPENAI_LLM_ENDPOINT=.......
AZURE_OPENAI_LLM_API_KEY=.......
AZURE_OPENAI_LLM_MODEL=GPT-4o-mini
 
# ChromaDB Settings
CHROMA_DB_PATH=./chroma_db
COLLECTION_NAME=udemy_courses

# Kích hoạt virtual environment
# Mac/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# Cài đặt dependencies
pip install -r requirements.txt

# Cấu hình environment variables
cp .env.example .env
# Chỉnh sửa .env với OpenAI API keys của bạn
```

### 3. Frontend Setup

```bash
# Chuyển đến thư mục react
cd ../react

# Cài đặt dependencies
npm install

# Hoặc nếu dùng yarn
yarn install
```

### 4. Chuẩn Bị Dữ Liệu

```bash
# Chuyển đến thư mục backend
cd ../backend

# Chạy script embed documents
python -c "
from utils.vector_store import load_vectorstore
data = load_vectorstore()
print(f'✅ Đã tải {len(data)} documents')
"
```

### 5. Chạy Ứng Dụng

**Terminal 1 - Backend:**

```bash
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**

```bash
cd react
npm run dev
```

### 6. Truy Cập Ứng Dụng

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📱 Hướng Dẫn Sử Dụng

### Bước 1: Nhập Thông Tin Profile

- Chọn mục tiêu nghề nghiệp (Backend Developer, Data Scientist, etc.)
- Nhập hoặc dán nội dung CV/profile
- Có thể sử dụng profile mẫu để test

### Bước 2: Làm Bài Pre-Quiz

- Hệ thống tạo bài quiz tự động dựa trên profile
- 3-5 câu hỏi về lĩnh vực đã chọn
- Nhận kết quả và đánh giá trình độ hiện tại

### Bước 3: Xem Khóa Học Được Gợi Ý

- Danh sách khóa học phù hợp với profile và kết quả quiz
- Độ tương đồng và lý do đề xuất
- Có thể xem chi tiết từng khóa học

### Bước 4: Làm Bài Post-Quiz

- Bài kiểm tra kiến thức sau khi học
- So sánh kết quả với Pre-Quiz
- Đánh giá tiến bộ và hiệu quả học tập

## 🔧 API Endpoints

### Quiz Generation

```http
POST /api/generate-quiz
Content-Type: application/json

{
  "profile_text": "string",
  "career_goal": "string",
  "quiz_type": "pre-quiz|post-quiz"
}
```

### Course Recommendations

```http
POST /api/recommend-courses
Content-Type: application/json

{
  "profile_text": "string",
  "career_goal": "string"
}
```

### Health Check

```http
GET /health
GET /
```

## 🛠️ Công Nghệ Sử Dụng

### Frontend

- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Axios** - HTTP client

### Backend

- **FastAPI** - Python web framework
- **OpenAI API** - AI capabilities
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server

### AI/ML

- **GPT-4o-mini** - Text generation
- **RAG Architecture** - Retrieval-augmented generation
- **Vector Embeddings** - Semantic search
- **Cosine Similarity** - Similarity calculation

## 🔧 Development

### Thêm Khóa Học Mới

Chỉnh sửa file `shared/data/courses.json`:

```json
{
  "id": "course_001",
  "title": "Tên khóa học",
  "description": "Mô tả khóa học",
  "keywords": ["keyword1", "keyword2"]
}
```

### Tạo Embeddings Mới

```bash
cd backend
python -c "
from ingestion.embed_documents import embed_courses_and_save
embed_courses_and_save()
"
```

### Environment Variables

```env
OPENAI_API_KEY_GPT4O=your_gpt4o_key
OPENAI_API_KEY_EMBED=your_embed_key
OPENAI_BASE_URL=your_base_url
OPENAI_API_KEY=your_api_key
```

## 🐛 Xử Lý Lỗi Thường Gặp

### Lỗi API Connection

```bash
# Kiểm tra backend đang chạy
curl http://localhost:8000/health

# Kiểm tra CORS configuration
```

### Lỗi OpenAI API

```bash
# Kiểm tra API keys
python -c "from utils.openai_client import test_openai_connection; test_openai_connection()"
```

### Lỗi Vectorstore

```bash
# Kiểm tra file embeddings
python -c "from utils.vector_store import load_vectorstore; print(f'Documents: {len(load_vectorstore())}')"
```

## 📈 Roadmap & Tính Năng Tương Lai

- [ ] **Đọc CV từ file** (PDF, DOCX)
- [ ] **User authentication** và lưu lịch sử
- [ ] **Multi-language support** (English, Vietnamese)
- [ ] **Advanced analytics** và reporting
- [ ] **Integration với LMS** (Learning Management System)
- [ ] **Mobile app** (React Native)
- [ ] **Real-time progress tracking**
- [ ] **Social features** và learning communities

## 👥 Đóng Góp

Chúng tôi hoan nghênh mọi đóng góp! Hãy:

1. Fork repository
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 🤝 Liên Hệ

**Project Link**: [https://github.com/yourusername/rag-learning-assistant](https://github.com/yourusername/rag-learning-assistant)

**Email**: your-email@example.com

## 🙏 Acknowledgments

- OpenAI cho GPT-4o-mini API
- FastAPI team cho framework tuyệt vời
- Next.js team cho React framework
- Cộng đồng open source

---

<div align="center">

**⭐ Nếu bạn thấy dự án hữu ích, hãy cho chúng tôi một star! ⭐**

_"Học tập là hành trình suốt đời - hãy để AI đồng hành cùng bạn"_ 🚀

</div>
