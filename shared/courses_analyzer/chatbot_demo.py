#!/usr/bin/env python3
"""
Demo chatbot để query ChromaDB và trả lời câu hỏi về courses
Sử dụng OpenAI để tạo embedding cho câu hỏi và tìm kiếm similarity
"""
 
import chromadb
from chromadb.config import Settings
from openai import AzureOpenAI
import os
from dotenv import load_dotenv
import json
from typing import List, Dict, Any
import logging
 
# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Load environment variables
load_dotenv()
 
class UdemyCourseChatbot:
    def __init__(self):
        """Khởi tạo chatbot"""        
        # Khởi tạo OpenAI client
        self.openai_client = AzureOpenAI(
            azure_endpoint=os.getenv('AZURE_OPENAI_EMBEDDING_ENDPOINT'),
            api_key=os.getenv('AZURE_OPENAI_EMBEDDING_API_KEY'),
            api_version="2024-02-01"
        )
       
        # Khởi tạo ChromaDB
        self.chroma_path = os.getenv('CHROMA_DB_PATH', './chroma_db')
        self.collection_name = os.getenv('COLLECTION_NAME', 'udemy_courses')
       
        # Tạo ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=self.chroma_path
        )
       
        # Lấy collection
        try:
            self.collection = self.chroma_client.get_collection(name=self.collection_name)
            logger.info(f"Đã kết nối với collection: {self.collection_name}")
            logger.info(f"Số lượng documents: {self.collection.count()}")
        except Exception as e:
            logger.error(f"Không thể kết nối với collection: {e}")
            logger.error("Vui lòng chạy data_analyzer.py trước để tạo dữ liệu")
            raise e
   
    def get_embedding(self, text: str) -> List[float]:
        """Tạo embedding từ OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model=os.getenv('AZURE_OPENAI_EMBED_MODEL', 'text-embedding-3-small'),
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Lỗi khi tạo embedding: {e}")
            raise e
   
    def group_results_by_course(self, results: Dict[str, Any]) -> List[Dict]:
        """Group chunk results by course to avoid showing duplicate courses"""
        if not results['documents'][0]:
            return []
       
        courses = {}
       
        for metadata, document, distance in zip(
            results['metadatas'][0],
            results['documents'][0],
            results['distances'][0]
        ):
            course_id = metadata.get('course_id', 'unknown')
            title = metadata.get('title', 'Unknown Course')
           
            # Keep the best (lowest distance) chunk for each course
            if course_id not in courses or distance < courses[course_id]['distance']:
                courses[course_id] = {
                    'metadata': metadata,
                    'document': document,
                    'distance': distance,
                    'title': title
                }
       
        # Sort by distance (best matches first)
        sorted_courses = sorted(courses.values(), key=lambda x: x['distance'])
        return sorted_courses
 
    def search_courses(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """Tìm kiếm courses dựa trên query"""
        logger.info(f"Đang tìm kiếm: {query}")
       
        # Tạo embedding cho query
        query_embedding = self.get_embedding(query)
       
        # Tìm kiếm trong ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )
       
        return results
   
    def calculate_similarity_info(self, distance: float) -> tuple:
        """Tính toán thông tin similarity từ distance"""
        # Vector similarity: distance 0 = hoàn toàn giống, distance càng lớn càng khác
        # Chuyển đổi thành percentage và ranking
       
        if distance <= 0.3:
            rank = "Excellent Match"
            percentage = 90 + (0.3 - distance) * 33.33  # 90-100%
        elif distance <= 0.6:
            rank = "Good Match"
            percentage = 70 + (0.6 - distance) * 66.67  # 70-90%
        elif distance <= 1.0:
            rank = "Fair Match"
            percentage = 40 + (1.0 - distance) * 75     # 40-70%
        elif distance <= 1.5:
            rank = "Poor Match"
            percentage = 10 + (1.5 - distance) * 60     # 10-40%
        else:
            rank = "Very Poor Match"
            percentage = max(0, 10 - (distance - 1.5) * 10)  # 0-10%
       
        return min(100, max(0, percentage)), rank
 
    def format_course_info(self, metadata: Dict, document: str, distance: float) -> str:
        """Format thông tin course để hiển thị"""
        info_parts = []
       
        # Title và rating
        title = metadata.get('title', 'N/A')
        rating = metadata.get('rating', 0)
        info_parts.append(f"📚 **{title}**")
        info_parts.append(f"⭐ Rating: {rating}/5")
       
        # Instructor và level
        instructor = metadata.get('instructor', 'N/A')
        level = metadata.get('level', 'N/A')
        info_parts.append(f"👨‍🏫 Instructor: {instructor}")
        info_parts.append(f"📈 Level: {level}")
       
        # Duration
        duration = metadata.get('duration', 'N/A')
        info_parts.append(f"⏱️ Duration: {duration}")
       
        # Link
        link = metadata.get('link', None)
        if link:
            info_parts.append(f"🔗 Link: {link}")
       
        # Chunk type information
        chunk_type = metadata.get('chunk_type', 'unknown')
        content_focus = metadata.get('content_focus', 'general')
        info_parts.append(f"🧩 Match Type: {chunk_type.replace('_', ' ').title()} ({content_focus})")
       
        # Content preview based on chunk type
        if chunk_type == 'learning_outcomes':
            what_you_learn = metadata.get('what_you_learn', '[]')
            try:
                learn_list = json.loads(what_you_learn)
                if learn_list:
                    info_parts.append("📝 What you'll learn:")
                    for item in learn_list[:3]:  # Chỉ hiển thị 3 items đầu
                        info_parts.append(f"  • {item}")
                    if len(learn_list) > 3:
                        info_parts.append(f"  ... và {len(learn_list) - 3} mục khác")
            except:
                pass
       
        elif chunk_type == 'prerequisites_audience':
            requirements = metadata.get('requirements', '[]')
            target_audience = metadata.get('target_audience', '[]')
            try:
                if requirements and requirements != '[]':
                    req_list = json.loads(requirements)
                    if req_list:
                        info_parts.append("📋 Requirements:")
                        for item in req_list[:2]:
                            info_parts.append(f"  • {item}")
               
                if target_audience and target_audience != '[]':
                    aud_list = json.loads(target_audience)
                    if aud_list:
                        info_parts.append("🎯 Target Audience:")
                        for item in aud_list[:2]:
                            info_parts.append(f"  • {item}")
            except:
                pass
       
        elif chunk_type == 'technical_summary':
            keywords = metadata.get('keywords', '[]')
            try:
                keywords_list = json.loads(keywords) if isinstance(keywords, str) else keywords
                if keywords_list:
                    info_parts.append(f"🔖 Key Topics: {', '.join(keywords_list[:5])}")
            except:
                # Fallback for backwards compatibility
                if keywords and not isinstance(keywords, str):
                    info_parts.append(f"🔖 Key Topics: {', '.join(keywords[:5])}")
       
        elif chunk_type == 'title_description':
            # For main content chunks, show what you'll learn if available
            what_you_learn = metadata.get('what_you_learn', '[]')
            try:
                learn_list = json.loads(what_you_learn)
                if learn_list:
                    info_parts.append("📝 What you'll learn:")
                    for item in learn_list[:2]:
                        info_parts.append(f"  • {item}")
                    if len(learn_list) > 2:
                        info_parts.append(f"  ... và {len(learn_list) - 2} mục khác")
            except:
                pass
       
        # Similarity score - Chuyển đổi distance thành similarity score
        similarity_percentage, match_rank = self.calculate_similarity_info(distance)
        info_parts.append(f"🎯 Similarity: {similarity_percentage:.1f}% | {match_rank}")
        info_parts.append(f" Vector Distance: {distance:.3f}")
       
        return '\n'.join(info_parts)
   
    def answer_question(self, question: str) -> str:
        """Trả lời câu hỏi dựa trên dữ liệu courses với chunk deduplication"""
        # Tìm kiếm với nhiều results hơn để có đủ chunks
        results = self.search_courses(question, n_results=10)
       
        if not results['documents'][0]:
            return "Xin lỗi, tôi không tìm thấy course nào phù hợp với câu hỏi của bạn."
       
        # Group results by course để tránh duplicate
        grouped_courses = self.group_results_by_course(results)
       
        if not grouped_courses:
            return "Xin lỗi, tôi không tìm thấy course nào phù hợp với câu hỏi của bạn."
       
        # Chỉ lấy top 3 courses
        top_courses = grouped_courses[:3]
       
        # Format kết quả
        response_parts = []
        response_parts.append(f"🔍 **Tìm thấy {len(top_courses)} courses liên quan đến: '{question}'**\n")
       
        for i, course_data in enumerate(top_courses):
            response_parts.append(f"## Course {i + 1}")
            response_parts.append(self.format_course_info(
                course_data['metadata'],
                course_data['document'],
                course_data['distance']
            ))
            response_parts.append("")  # Dòng trống
       
        return '\n'.join(response_parts)
   
    def get_course_recommendations(self, topic: str, level: str = None, max_rating: float = None) -> str:
        """Đưa ra recommendations dựa trên topic và criteria"""
        # Tạo query
        query_parts = [f"courses about {topic}"]
        if level:
            query_parts.append(f"{level} level")
       
        query = " ".join(query_parts)
       
        # Tìm kiếm
        results = self.search_courses(query, n_results=10)
       
        if not results['documents'][0]:
            return f"Không tìm thấy course nào về {topic}."
       
        # Lọc thêm based on criteria
        filtered_courses = []
        for metadata, document, distance in zip(
            results['metadatas'][0],
            results['documents'][0],
            results['distances'][0]
        ):
            # Lọc theo level nếu có
            if level and level.lower() not in metadata.get('level', '').lower():
                continue
           
            # Lọc theo rating nếu có
            if max_rating and metadata.get('rating', 0) < max_rating:
                continue
           
            filtered_courses.append((metadata, document, distance))
       
        if not filtered_courses:
            return f"Không tìm thấy course nào phù hợp với tiêu chí của bạn."
       
        # Format response
        response_parts = []
        response_parts.append(f"🎯 **Top recommendations cho '{topic}':**\n")
       
        for i, (metadata, document, distance) in enumerate(filtered_courses[:5]):
            response_parts.append(f"## Recommendation {i + 1}")
            response_parts.append(self.format_course_info(metadata, document, distance))
            response_parts.append("")
       
        return '\n'.join(response_parts)
   
    def explain_similarity_scoring(self):
        """Giải thích cách tính similarity score"""
        explanation = """
🎯 **HƯỚNG DẪN SIMILARITY SCORING**
 
📏 **Vector Distance** là khoảng cách giữa embedding của câu hỏi và course:
   • Distance = 0.0: Hoàn toàn giống nhau (100% similarity)
   • Distance càng nhỏ: Càng tương đồng
   • Distance càng lớn: Càng khác biệt
 
📊 **Match Ranking:**
   🟢 Excellent Match (90-100%): Distance ≤ 0.3 - Rất phù hợp
   🟡 Good Match (70-90%): Distance 0.3-0.6 - Phù hợp tốt  
   🟠 Fair Match (40-70%): Distance 0.6-1.0 - Phù hợp ở mức trung bình
   🔴 Poor Match (10-40%): Distance 1.0-1.5 - Ít phù hợp
   ⚫ Very Poor Match (0-10%): Distance >1.5 - Rất ít phù hợp
 
💡 **Lưu ý:** Similarity âm (-51.6%) có nghĩa là distance > 1, cho thấy course không liên quan lắm đến câu hỏi.
"""
        return explanation
 
    def interactive_chat(self):
        """Chế độ chat tương tác"""
        print("\n🤖 Chào bạn! Tôi là Udemy Course Assistant")
        print("Bạn có thể hỏi tôi về:")
        print("- Tìm course về một chủ đề cụ thể")
        print("- Recommend courses theo level hoặc rating")
        print("- Thông tin chi tiết về courses")
        print("\nVí dụ:")
        print("- 'Tìm course về React'")
        print("- 'Course Python cho beginner'")
        print("- 'Machine learning courses with high rating'")
        print("\nLệnh đặc biệt:")
        print("- 'help similarity' - Giải thích cách tính similarity")
        print("- 'quit' - Thoát")
        print()
       
        while True:
            try:
                user_input = input("❓ Bạn muốn hỏi gì: ").strip()
               
                if user_input.lower() in ['quit', 'exit', 'thoát']:
                    print("👋 Tạm biệt!")
                    break
               
                if user_input.lower() in ['help similarity', 'similarity help']:
                    print(self.explain_similarity_scoring())
                    continue
               
                if not user_input:
                    continue
               
                # Xử lý câu hỏi
                print("\n🔄 Đang tìm kiếm...")
                response = self.answer_question(user_input)
                print("\n" + response + "\n")
               
            except KeyboardInterrupt:
                print("\n\n👋 Tạm biệt!")
                break
            except Exception as e:
                print(f"\n❌ Lỗi: {e}\n")
 
def main():
    """Demo function"""
    # Kiểm tra API key
    load_dotenv()
    if not os.getenv('AZURE_OPENAI_EMBEDDING_API_KEY') or os.getenv('AZURE_OPENAI_EMBEDDING_API_KEY') == 'your_openai_api_key_here':
        print("❌ Vui lòng cập nhật AZURE_OPENAI_EMBEDDING_API_KEY trong file .env")
        return
   
    try:
        # Khởi tạo chatbot
        chatbot = UdemyCourseChatbot()
       
        # Demo các queries
        print("🚀 Demo Udemy Course Chatbot\n")
       
        # Demo 1: Tìm course về React
        print("=" * 60)
        print("DEMO 1: Tìm course về React")
        print("=" * 60)
        response = chatbot.answer_question("React courses for web development")
        print(response)
       
        print("\n" + "=" * 60)
        print("DEMO 2: Course Python cho beginner")
        print("=" * 60)
        response = chatbot.answer_question("Python courses for beginners")
        print(response)
       
        print("\n" + "=" * 60)
        print("DEMO 3: Machine learning courses")
        print("=" * 60)
        response = chatbot.answer_question("machine learning artificial intelligence")
        print(response)
       
        # Chế độ interactive
        print("\n" + "=" * 60)
        chatbot.interactive_chat()
       
    except Exception as e:
        logger.error(f"Lỗi khởi tạo chatbot: {e}")
        print("❌ Không thể khởi tạo chatbot. Vui lòng chạy data_analyzer.py trước.")
 
if __name__ == "__main__":
    main()