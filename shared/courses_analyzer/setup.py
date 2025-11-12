 #!/usr/bin/env python3
"""
Script setup để cài đặt dependencies và kiểm tra cấu hình
"""
 
import subprocess
import sys
import os
from pathlib import Path
 
def install_requirements():
    """Cài đặt các dependencies từ requirements.txt"""
    print("🔧 Đang cài đặt dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Đã cài đặt thành công tất cả dependencies!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi khi cài đặt dependencies: {e}")
        return False
 
def check_env_file():
    """Kiểm tra file .env"""
    env_file = Path(__file__).resolve().parent.parent / ".env"
    
    if not env_file.exists():
        print("⚠️ File .env không tồn tại")
        return False
   
    # Đọc và kiểm tra API key
    with open(env_file, 'r') as f:
        content = f.read()
   
    if "your_openai_api_key_here" in content:
        print("⚠️ Bạn cần cập nhật OPENAI_API_KEY trong file .env")
        print("📝 Mở file .env và thay thế 'your_openai_api_key_here' bằng API key thực")
        return False
   
    print("✅ File .env đã được cấu hình")
    return True
 
def check_data_file():
    """Kiểm tra file dữ liệu"""
    data_file = Path(__file__).resolve().parent.parent / "data" / "UDEMY_2025.csv"
    if not data_file.exists():
        print("⚠️ File /data/UDEMY_2025.csv không tồn tại")
        print("📁 Đảm bảo file dữ liệu CSV có trong thư mục /data")
        return False
   
    print("✅ File dữ liệu CSV /data/UDEMY_2025.csv đã sẵn sàng")
    return True
 
def test_imports():
    """Test import các thư viện cần thiết"""
    print("🧪 Đang kiểm tra imports...")
   
    import_tests = [
        ('pandas', 'pandas'),
        ('chromadb', 'chromadb'),
        ('openai', 'openai'),
        ('python-dotenv', 'from dotenv import load_dotenv')
    ]
   
    failed_imports = []
   
    for package_name, import_statement in import_tests:
        try:
            if 'from' in import_statement:
                exec(import_statement)
            else:
                __import__(import_statement)
            print(f"  ✅ {package_name}")
        except ImportError:
            print(f"  ❌ {package_name}")
            failed_imports.append(package_name)
   
    if failed_imports:
        print(f"\n❌ Một số module không import được: {failed_imports}")
        return False
   
    print("✅ Tất cả modules đã sẵn sàng!")
    return True
 
def main():
    """Hàm main"""
    print("🚀 Udemy Course AI Chatbot - Setup Script")
    print("=" * 50)
   
    # Kiểm tra Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Cần Python 3.8 trở lên")
        return
   
    print(f"✅ Python version: {python_version.major}.{python_version.minor}")
   
    # Cài đặt dependencies
    if not install_requirements():
        return
   
    # Test imports
    if not test_imports():
        print("\n🔄 Thử cài đặt lại dependencies:")
        print("pip install -r requirements.txt")
        return
   
    # Kiểm tra các file cần thiết
    env_ok = check_env_file()
    data_ok = check_data_file()
   
    print("\n" + "=" * 50)
    print("📋 TỔNG KẾT SETUP:")
   
    if env_ok and data_ok:
        print("✅ Setup hoàn tất! Bạn có thể chạy:")
        print("   1. python data_analyzer.py  (để xử lý dữ liệu)")
        print("   2. python chatbot_demo.py   (để test chatbot)")
    else:
        print("⚠️ Cần hoàn thành các bước sau:")
        if not env_ok:
            print("   - Cập nhật OPENAI_API_KEY trong file .env")
        if not data_ok:
            print("   - Đảm bảo file UDEMY_2025.csv có trong thư mục")
       
        print("\nSau khi hoàn thành, chạy lại script này để kiểm tra.")
 
if __name__ == "__main__":
    main()