 #!/usr/bin/env python3
"""
Script phân tích dữ liệu Udemy courses và lưu vào ChromaDB
Sử dụng OpenAI text-embedding-3-small để tạo embeddings
"""
 
import pandas as pd
import chromadb
from chromadb.config import Settings
from openai import AzureOpenAI
import os
from dotenv import load_dotenv
import json
import time
from typing import List, Dict, Any, Tuple
import logging
import re
from pathlib import Path
import hashlib
 
# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Load environment variables
load_dotenv()        
 
class UdemyCourseAnalyzer:
    def __init__(self):
        """Khởi tạo analyzer với các cấu hình cần thiết"""
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
       
        # Tạo hoặc lấy collection
        try:
            self.collection = self.chroma_client.get_collection(name=self.collection_name)
            logger.info(f"Đã tìm thấy collection: {self.collection_name}")
        except:
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "Udemy courses data for AI chatbot"}
            )
            logger.info(f"Đã tạo collection mới: {self.collection_name}")
   
    def clean_text(self, text: str) -> str:
        """Làm sạch text, xử lý encoding issues"""
        if pd.isna(text) or text is None:
            return ""
       
        # Convert to string
        text = str(text)
       
        # Xử lý encoding issues
        text = text.encode('utf-8', errors='ignore').decode('utf-8')
       
        # Loại bỏ các ký tự không mong muốn
        text = re.sub(r'[^\w\s\.,!?\-\(\)\[\]:]', ' ', text)
       
        # Loại bỏ whitespace thừa
        text = ' '.join(text.split())
       
        return text.strip()
   
    def parse_list_field(self, field_value: str) -> List[str]:
        """Parse các trường dạng list từ CSV"""
        if pd.isna(field_value) or field_value is None:
            return []
       
        field_value = str(field_value).strip()
       
        # Nếu bắt đầu và kết thúc bằng [], thì parse như JSON
        if field_value.startswith('[') and field_value.endswith(']'):
            try:
                # Thay thế single quotes bằng double quotes để parse JSON
                field_value = field_value.replace("'", '"')
                parsed_list = json.loads(field_value)
                return [self.clean_text(item) for item in parsed_list if item]
            except json.JSONDecodeError:
                # Nếu không parse được JSON, tách bằng comma
                pass
       
        # Fallback: tách bằng comma hoặc semicolon
        items = re.split(r'[,;]', field_value.strip('[]'))
        return [self.clean_text(item) for item in items if item.strip()]
   
    def create_course_chunks(self, course_row: pd.Series) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Tạo các chunks từ course data để tối ưu hóa embeddings
        Mỗi chunk tập trung vào một khía cạnh cụ thể của course
        """
        chunks = []
        base_metadata = {
            'course_id': course_row.name,
            'title': course_row['Title'],
            'instructor': course_row['Instructor'],
            'level': course_row['Level'],
            'rating': float(course_row['Rating']) if pd.notna(course_row['Rating']) else 0.0,
            'duration': course_row['Duration'],
            'link': course_row['Link'] if 'Link' in course_row else "",
        }
       
        # Chunk 1: Title + Description (Main content)
        if course_row['Title'] and course_row['Detailed Description']:
            title_desc_text = f"Course: {course_row['Title']}\n\nDescription: {course_row['Detailed Description']}"
            if course_row['Level']:
                title_desc_text += f"\n\nLevel: {course_row['Level']}"
            if course_row['Instructor']:
                title_desc_text += f"\nInstructor: {course_row['Instructor']}"
           
            chunk_metadata = base_metadata.copy()
            chunk_metadata.update({
                'chunk_type': 'title_description',
                'content_focus': 'main_info'
            })
            chunks.append((title_desc_text, chunk_metadata))
       
        # Chunk 2: Learning Outcomes (What you'll learn)
        if course_row['What_You_Learn'] and len(course_row['What_You_Learn']) > 0:
            learning_text = f"Course: {course_row['Title']}\n\nWhat you will learn:\n"
            learning_text += "\n".join([f"• {item}" for item in course_row['What_You_Learn']])
           
            chunk_metadata = base_metadata.copy()
            chunk_metadata.update({
                'chunk_type': 'learning_outcomes',
                'content_focus': 'skills_knowledge',
                'what_you_learn': json.dumps(course_row['What_You_Learn'])
            })
            chunks.append((learning_text, chunk_metadata))
       
        # Chunk 3: Prerequisites & Target Audience
        if course_row['Requirements'] or course_row['Target_Audience']:
            prereq_text = f"Course: {course_row['Title']}\n\n"
           
            if course_row['Requirements']:
                prereq_text += "Requirements:\n"
                prereq_text += "\n".join([f"• {item}" for item in course_row['Requirements']])
                prereq_text += "\n\n"
           
            if course_row['Target_Audience']:
                prereq_text += "Target Audience:\n"
                prereq_text += "\n".join([f"• {item}" for item in course_row['Target_Audience']])
           
            chunk_metadata = base_metadata.copy()
            chunk_metadata.update({
                'chunk_type': 'prerequisites_audience',
                'content_focus': 'requirements_targeting',
                'requirements': json.dumps(course_row['Requirements']),
                'target_audience': json.dumps(course_row['Target_Audience'])
            })
            chunks.append((prereq_text.strip(), chunk_metadata))
       
        # Chunk 4: Technical Details (Aggregated info cho search tổng quát)
        if any([course_row['Title'], course_row['Level'], course_row['Duration']]):
            tech_text = f"Course: {course_row['Title']}\n\n"
            tech_text += f"Level: {course_row['Level']}\n"
            tech_text += f"Duration: {course_row['Duration']}\n"
            tech_text += f"Rating: {course_row['Rating']}/5\n"
            tech_text += f"Instructor: {course_row['Instructor']}"
           
            # Thêm keywords từ title để tăng searchability
            title_keywords = self.extract_keywords_from_title(course_row['Title'])
            if title_keywords:
                tech_text += f"\n\nKey Topics: {', '.join(title_keywords)}"
           
            chunk_metadata = base_metadata.copy()
            chunk_metadata.update({
                'chunk_type': 'technical_summary',
                'content_focus': 'course_specs',
                'keywords': json.dumps(title_keywords)  # Convert list to JSON string
            })
            chunks.append((tech_text, chunk_metadata))
       
        return chunks
   
    def extract_keywords_from_title(self, title: str) -> List[str]:
        """Extract key technology/topic keywords from course title"""
        if not title:
            return []
       
        # Common programming languages and frameworks
        tech_keywords = {
            'python', 'javascript', 'java', 'react', 'angular', 'vue', 'node', 'nodejs',
            'django', 'flask', 'laravel', 'spring', 'express', 'mongodb', 'mysql',
            'postgresql', 'html', 'css', 'typescript', 'php', 'ruby', 'go', 'rust',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'machine learning', 'ml',
            'artificial intelligence', 'ai', 'data science', 'blockchain', 'flutter',
            'swift', 'kotlin', 'android', 'ios', 'unity', 'tensorflow', 'pytorch',
            'react native', 'vue.js', 'angular.js', 'next.js', 'nuxt.js'
        }
       
        title_lower = title.lower()
        found_keywords = []
       
        for keyword in tech_keywords:
            if keyword in title_lower:
                found_keywords.append(keyword)
       
        # Extract words that look like tech terms (CamelCase, acronyms)
        tech_pattern = r'\b[A-Z][a-z]*(?:[A-Z][a-z]*)*\b|\b[A-Z]{2,}\b'
        tech_matches = re.findall(tech_pattern, title)
       
        for match in tech_matches:
            if len(match) > 2 and match.lower() not in found_keywords:
                found_keywords.append(match.lower())
       
        return found_keywords[:5]  # Limit to 5 keywords
   
    def load_and_process_data(self, csv_file_path: str) -> pd.DataFrame:
        """Load và xử lý dữ liệu từ file CSV"""
        logger.info(f"Đang load dữ liệu từ: {csv_file_path}")
       
        try:
            # Đọc CSV với encoding tự động detect
            df = pd.read_csv(csv_file_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(csv_file_path, encoding='latin-1')
            except UnicodeDecodeError:
                df = pd.read_csv(csv_file_path, encoding='cp1252')
       
        logger.info(f"Đã load {len(df)} courses từ CSV")
       
        # Làm sạch dữ liệu
        df['Title'] = df['Title'].apply(self.clean_text)
        df['Detailed Description'] = df['Detailed Description'].apply(self.clean_text)
       
        # Parse các trường list
        df['What_You_Learn'] = df['What You\'ll Learn'].apply(self.parse_list_field)
        df['Requirements'] = df['Requirements'].apply(self.parse_list_field)
        df['Target_Audience'] = df['Target Audience'].apply(self.parse_list_field)
       
        # Làm sạch các trường khác
        df['Instructor'] = df['Instructor'].apply(self.clean_text)
        df['Level'] = df['Level'].apply(self.clean_text)
       
        # Xử lý rating và duration
        df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
        df['Duration'] = df['Duration'].apply(self.clean_text)
       
        return df
   
    def create_course_text(self, course_row: pd.Series) -> str:
        """Tạo text mô tả đầy đủ cho course để embedding"""
        parts = []
       
        # Title
        if course_row['Title']:
            parts.append(f"Course Title: {course_row['Title']}")
       
        # Description
        if course_row['Detailed Description']:
            parts.append(f"Description: {course_row['Detailed Description']}")
       
        # What you'll learn
        if course_row['What_You_Learn']:
            learning_points = '; '.join(course_row['What_You_Learn'])
            parts.append(f"What you'll learn: {learning_points}")
       
        # Requirements
        if course_row['Requirements']:
            requirements = '; '.join(course_row['Requirements'])
            parts.append(f"Requirements: {requirements}")
       
        # Target Audience
        if course_row['Target_Audience']:
            audience = '; '.join(course_row['Target_Audience'])
            parts.append(f"Target Audience: {audience}")
       
        # Instructor
        if course_row['Instructor']:
            parts.append(f"Instructor: {course_row['Instructor']}")
       
        # Level
        if course_row['Level']:
            parts.append(f"Level: {course_row['Level']}")
       
        # Rating and duration
        if pd.notna(course_row['Rating']):
            parts.append(f"Rating: {course_row['Rating']}/5")
       
        if course_row['Duration']:
            parts.append(f"Duration: {course_row['Duration']}")
       
        return '\n\n'.join(parts)
   
    def get_embedding(self, text: str, max_retries: int = 3) -> List[float]:
        """Tạo embedding từ OpenAI với retry logic"""
        for attempt in range(max_retries):
            try:
                # Giới hạn độ dài text (OpenAI có limit)
                if len(text) > 8000:
                    text = text[:8000]
               
                response = self.openai_client.embeddings.create(
                    model=os.getenv('AZURE_OPENAI_EMBED_MODEL'),
                    input=text
                )
                return response.data[0].embedding
           
            except Exception as e:
                logger.warning(f"Lỗi khi tạo embedding (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise e
   
    def process_and_store_courses(self, df: pd.DataFrame, batch_size: int = 5):
        """Xử lý và lưu courses vào ChromaDB với chunking strategy"""
        logger.info(f"Bắt đầu xử lý {len(df)} courses với chunking strategy...")
       
        documents = []
        metadatas = []
        ids = []
        embeddings = []
       
        total_chunks = 0
       
        for course_idx, row in df.iterrows():
            try:
                logger.info(f"Đang xử lý course {course_idx + 1}/{len(df)}: {row['Title'][:50]}...")
               
                # Tạo chunks cho course
                course_chunks = self.create_course_chunks(row)
               
                for chunk_idx, (chunk_text, chunk_metadata) in enumerate(course_chunks):
                    # Tạo embedding cho chunk
                    logger.info(f"  - Tạo embedding cho chunk {chunk_idx + 1}/{len(course_chunks)} ({chunk_metadata['chunk_type']})")
                    embedding = self.get_embedding(chunk_text)
                   
                    # Tạo unique ID cho chunk
                    chunk_id = f"course_{course_idx}_chunk_{chunk_idx}_{chunk_metadata['chunk_type']}"
                   
                    # Thêm thông tin chunk vào metadata
                    chunk_metadata.update({
                        'chunk_index': chunk_idx,
                        'total_chunks': len(course_chunks),
                        'chunk_id': chunk_id
                    })
                   
                    documents.append(chunk_text)
                    metadatas.append(chunk_metadata)
                    ids.append(chunk_id)
                    embeddings.append(embedding)
                    total_chunks += 1
                   
                    # Lưu theo batch để tránh memory issues
                    if len(documents) >= batch_size:
                        self._store_batch(documents, metadatas, ids, embeddings)
                        documents, metadatas, ids, embeddings = [], [], [], []
               
                # Pause để tránh rate limit
                time.sleep(0.3)
               
            except Exception as e:
                logger.error(f"Lỗi khi xử lý course {course_idx}: {e}")
                continue
       
        # Lưu batch cuối cùng
        if documents:
            self._store_batch(documents, metadatas, ids, embeddings)
       
        logger.info(f"Hoàn thành việc lưu {len(df)} courses với tổng cộng {total_chunks} chunks vào ChromaDB!")
        return total_chunks
   
    def _store_batch(self, documents: List[str], metadatas: List[Dict],
                     ids: List[str], embeddings: List[List[float]]):
        """Lưu một batch courses vào ChromaDB"""
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            logger.info(f"Đã lưu batch gồm {len(documents)} courses")
        except Exception as e:
            logger.error(f"Lỗi khi lưu batch: {e}")
   
    def get_collection_info(self):
        """Hiển thị thông tin chi tiết về collection và chunks"""
        count = self.collection.count()
        logger.info(f"Collection '{self.collection_name}' có {count} chunks")
       
        # Lấy thông tin về các loại chunks
        try:
            results = self.collection.get(limit=count, include=['metadatas'])
            chunk_types = {}
            courses_count = set()
           
            for metadata in results['metadatas']:
                chunk_type = metadata.get('chunk_type', 'unknown')
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
               
                course_id = metadata.get('course_id')
                if course_id is not None:
                    courses_count.add(course_id)
           
            logger.info(f"Thống kê chunks:")
            for chunk_type, count in chunk_types.items():
                logger.info(f"  - {chunk_type}: {count} chunks")
           
            logger.info(f"Tổng số courses được chunked: {len(courses_count)}")
           
        except Exception as e:
            logger.warning(f"Không thể lấy thông tin chi tiết: {e}")
       
        return count
 
def main():
    """Hàm main để chạy script"""
    # Kiểm tra API key
    if not os.getenv('AZURE_OPENAI_EMBEDDING_API_KEY') or os.getenv('AZURE_OPENAI_EMBEDDING_API_KEY') == 'your_openai_api_key_here':
        logger.error("Vui lòng cập nhật AZURE_OPENAI_EMBEDDING_API_KEY trong file .env")
        return
   
    # Khởi tạo analyzer
    analyzer = UdemyCourseAnalyzer()
   
    # File CSV path
    csv_file = Path(__file__).resolve().parent.parent / "data" / "UDEMY_2025.csv"
   
    if not os.path.exists(csv_file):
        logger.error(f"Không tìm thấy file: {csv_file}")
        return
   
    # Load và xử lý dữ liệu
    df = analyzer.load_and_process_data(csv_file)
   
    # Hiển thị thông tin preview
    logger.info("Preview dữ liệu:")
    print("\nSố lượng courses:", len(df))
    print("\nMột số courses đầu tiên:")
    for idx, row in df.head(3).iterrows():
        print(f"- {row['Title'][:100]}...")
   
    print(f"\n🧩 Chunking Strategy:")
    print("Mỗi course sẽ được chia thành 3-4 chunks:")
    print("  1. Title + Description (main content)")    # Luôn có (100%)
    print("  2. Learning Outcomes (skills & knowledge)")    # ~80% courses có data
    print("  3. Prerequisites & Target Audience")# ~90% courses có data  
    print("  4. Technical Summary (keywords & specs)")# Luôn có (100%)
    #print(f"\nDự kiến tạo khoảng {len(df) * 3.5:.0f} chunks để tối ưu hóa search")
   
    # Xác nhận trước khi xử lý
    response = input("\nBạn có muốn tiếp tục xử lý với chunking strategy? (y/n): ")
    if response.lower() != 'y':
        logger.info("Đã hủy xử lý.")
        return
   
    # Xử lý và lưu với chunking
    total_chunks = analyzer.process_and_store_courses(df)
   
    # Hiển thị kết quả
    analyzer.get_collection_info()
 
if __name__ == "__main__":
    main()