 #!/usr/bin/env python3
"""
Demo script để test chunking strategy với một course mẫu
"""
 
import json
from typing import List, Tuple, Dict, Any
 
def create_course_chunks_demo(course_data: Dict) -> List[Tuple[str, Dict[str, Any]]]:
    """Demo version của create_course_chunks function"""
    chunks = []
    base_metadata = {
        'course_id': 0,
        'title': course_data['title'],
        'instructor': course_data['instructor'],
        'level': course_data['level'],
        'rating': course_data['rating'],
        'duration': course_data['duration'],
        'link': course_data['link'],
    }
   
    # Chunk 1: Title + Description (Main content)
    if course_data['title'] and course_data['description']:
        title_desc_text = f"Course: {course_data['title']}\n\nDescription: {course_data['description']}"
        if course_data['level']:
            title_desc_text += f"\n\nLevel: {course_data['level']}"
        if course_data['instructor']:
            title_desc_text += f"\nInstructor: {course_data['instructor']}"
       
        chunk_metadata = base_metadata.copy()
        chunk_metadata.update({
            'chunk_type': 'title_description',
            'content_focus': 'main_info'
        })
        chunks.append((title_desc_text, chunk_metadata))
   
    # Chunk 2: Learning Outcomes (What you'll learn)
    if course_data['what_you_learn']:
        learning_text = f"Course: {course_data['title']}\n\nWhat you will learn:\n"
        learning_text += "\n".join([f"• {item}" for item in course_data['what_you_learn']])
       
        chunk_metadata = base_metadata.copy()
        chunk_metadata.update({
            'chunk_type': 'learning_outcomes',
            'content_focus': 'skills_knowledge',
            'what_you_learn': json.dumps(course_data['what_you_learn'])
        })
        chunks.append((learning_text, chunk_metadata))
   
    # Chunk 3: Prerequisites & Target Audience
    if course_data['requirements'] or course_data['target_audience']:
        prereq_text = f"Course: {course_data['title']}\n\n"
       
        if course_data['requirements']:
            prereq_text += "Requirements:\n"
            prereq_text += "\n".join([f"• {item}" for item in course_data['requirements']])
            prereq_text += "\n\n"
       
        if course_data['target_audience']:
            prereq_text += "Target Audience:\n"
            prereq_text += "\n".join([f"• {item}" for item in course_data['target_audience']])
       
        chunk_metadata = base_metadata.copy()
        chunk_metadata.update({
            'chunk_type': 'prerequisites_audience',
            'content_focus': 'requirements_targeting',
            'requirements': json.dumps(course_data['requirements']),
            'target_audience': json.dumps(course_data['target_audience'])
        })
        chunks.append((prereq_text.strip(), chunk_metadata))
   
    # Chunk 4: Technical Details (Aggregated info)
    tech_text = f"Course: {course_data['title']}\n\n"
    tech_text += f"Level: {course_data['level']}\n"
    tech_text += f"Duration: {course_data['duration']}\n"
    tech_text += f"Rating: {course_data['rating']}/5\n"
    tech_text += f"Instructor: {course_data['instructor']}"
   
    # Extract keywords từ title
    keywords = extract_keywords_from_title(course_data['title'])
    if keywords:
        tech_text += f"\n\nKey Topics: {', '.join(keywords)}"
   
    chunk_metadata = base_metadata.copy()
    chunk_metadata.update({
        'chunk_type': 'technical_summary',
        'content_focus': 'course_specs',
        'keywords': keywords
    })
    chunks.append((tech_text, chunk_metadata))
   
    return chunks
 
def extract_keywords_from_title(title: str) -> List[str]:
    """Extract key technology keywords from course title"""
    if not title:
        return []
   
    tech_keywords = {
        'python', 'javascript', 'java', 'react', 'angular', 'vue', 'node', 'nodejs',
        'django', 'flask', 'laravel', 'spring', 'express', 'mongodb', 'mysql',
        'postgresql', 'html', 'css', 'typescript', 'php', 'ruby', 'go', 'rust',
        'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'machine learning', 'ml',
        'artificial intelligence', 'ai', 'data science', 'blockchain', 'flutter',
        'swift', 'kotlin', 'android', 'ios', 'unity', 'tensorflow', 'pytorch',
        'react native', 'vue.js', 'angular.js', 'next.js', 'nuxt.js', 'web', 'development'
    }
   
    title_lower = title.lower()
    found_keywords = []
   
    for keyword in tech_keywords:
        if keyword in title_lower:
            found_keywords.append(keyword)
   
    return found_keywords[:5]
 
def demo_chunking():
    """Demo chunking strategy với sample data"""
   
    # Sample course data
    sample_course = {
        'title': 'Complete Python Web Development with Django Framework',
        'description': 'Learn to build full-stack web applications using Python and Django. This comprehensive course covers everything from basic Django concepts to advanced features like REST APIs, authentication, and deployment.',
        'what_you_learn': [
            'Build web applications with Django framework',
            'Create REST APIs using Django REST Framework',
            'Implement user authentication and authorization',
            'Deploy Django applications to production',
            'Work with databases using Django ORM',
            'Create responsive frontend with Bootstrap'
        ],
        'requirements': [
            'Basic Python programming knowledge',
            'Understanding of HTML and CSS',
            'Familiarity with web development concepts'
        ],
        'target_audience': [
            'Python developers wanting to learn web development',
            'Web developers looking to learn Django',
            'Students interested in full-stack development',
            'Anyone wanting to build scalable web applications'
        ],
        'instructor': 'John Smith',
        'level': 'Intermediate',
        'rating': 4.5,
        'duration': '40 total hours',
        'link': 'https://example.com/django-course'
    }
    print("🧩 DEMO CHUNKING STRATEGY")
    print("=" * 60)
   
    print(f"📚 Original Course: {sample_course['title']}")
    print(f"📖 Description: {sample_course['description'][:100]}...")
    print()
   
    # Tạo chunks
    chunks = create_course_chunks_demo(sample_course)
   
    print(f"🔧 Generated {len(chunks)} chunks:")
    print()
   
    for i, (chunk_text, metadata) in enumerate(chunks, 1):
        print(f"## Chunk {i}: {metadata['chunk_type'].title().replace('_', ' ')}")
        print(f"🎯 Content Focus: {metadata['content_focus']}")
        print(f"📝 Text Preview:")
        print(f"```")
        #print(chunk_text[:200] + "..." if len(chunk_text) > 200 else chunk_text)
        print(chunk_text)
        print(f"```")
       
        # Show specific metadata for each chunk type
        if metadata['chunk_type'] == 'learning_outcomes':
            print(f"📚 Learning Items: {len(json.loads(metadata.get('what_you_learn', '[]')))}")
        elif metadata['chunk_type'] == 'prerequisites_audience':
            req_count = len(json.loads(metadata.get('requirements', '[]')))
            aud_count = len(json.loads(metadata.get('target_audience', '[]')))
            print(f"📋 Requirements: {req_count} items")
            print(f"🎯 Target Audiences: {aud_count} items")
        elif metadata['chunk_type'] == 'technical_summary':
            keywords = metadata.get('keywords', [])
            print(f"🔖 Extracted Keywords: {', '.join(keywords) if keywords else 'None'}")
       
        print(f"📏 Chunk Length: {len(chunk_text)} characters")
        print("-" * 40)
   
    print()
    print("💡 CHUNKING BENEFITS:")
    print("✅ Each chunk focuses on specific aspects (content, learning, requirements)")
    print("✅ Better semantic search - query 'python requirements' will match prerequisites chunk")
    print("✅ Query 'what will I learn' will match learning outcomes chunk")
    print("✅ Query 'django web development' will match title/description chunk")
    print("✅ Reduced noise - each embedding captures focused information")
    print()
    print("🎯 SEARCH OPTIMIZATION:")
    print(f"• Total chunks per course: {len(chunks)}")
    print(f"• Average chunk size: {sum(len(text) for text, _ in chunks) // len(chunks)} chars")
    print("• Each chunk optimized for different query types")
 
def test_extract_keywords():
    """Test function extract_keywords_from_title với các ví dụ thực tế"""
   
    test_cases = [
        "Complete Python Web Development with Django Framework",
        "React and Node.js Full Stack Development",
        "Machine Learning with TensorFlow and Python",
        "JavaScript ES6+ Modern Web Development",
        "Docker and Kubernetes for DevOps",
        "AWS Cloud Computing and MongoDB Database",
        "Angular + TypeScript Web Applications",
        "iOS Development with Swift Programming",
        "Vue.js and Laravel PHP Framework",
        "Artificial Intelligence and Data Science Course"
    ]
   
    print("🔍 KEYWORD EXTRACTION DEMO")
    print("=" * 60)
   
    for i, title in enumerate(test_cases, 1):
        keywords = extract_keywords_from_title(title)
       
        print(f"\n📚 Test Case {i}:")
        print(f"Title: {title}")
        print(f"🔖 Extracted Keywords: {keywords}")
        print(f"📊 Count: {len(keywords)} keywords found")
       
        # Analyze why certain keywords were found
        print(f"💡 Analysis:")
        title_lower = title.lower()
        for keyword in keywords:
            print(f"   ✅ '{keyword}' found in: '{title_lower}'")
       
        print("-" * 40)
if __name__ == "__main__":
    #demo_chunking()
    test_extract_keywords()