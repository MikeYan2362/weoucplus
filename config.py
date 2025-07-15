import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    # DeepSeek API配置
    DEEPSEEK_API_KEY = "sk-9189176321ae486c8f755145b59299eb"
    DEEPSEEK_BASE_URL = "https://api.deepseek.com"
    
    # 数据库配置
    DATABASE_URL = f"sqlite:///{os.path.abspath('database/weplus.db')}"
    
    # JWT配置
    SECRET_KEY = "your-secret-key-here-change-in-production"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # 应用配置
    DEBUG = True
    HOST = "0.0.0.0"  # 改为0.0.0.0以支持公网访问
    FRONTEND_PORT = 5000
    BACKEND_PORT = 8000
    
    # 文件上传配置
    UPLOAD_FOLDER = "uploads"
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "txt", "xlsx", "csv"}
    
    # 向量数据库配置
    CHROMA_DB_PATH = "./database/chroma_db"
    
    # 公网部署配置
    NGROK_FRONTEND_URL = os.getenv("NGROK_FRONTEND_URL", "http://localhost:5000")
    NGROK_BACKEND_URL = os.getenv("NGROK_BACKEND_URL", "http://localhost:8000") 