from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatHistory(Base):
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class KnowledgeDocument(Base):
    """知识库文档模型 - 完整的RAG文档管理"""
    __tablename__ = "knowledge_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    sequence_number = Column(Integer, nullable=False)  # 上传序号
    
    # 文件基本信息
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)  # 原始文件名
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt, etc.
    file_size = Column(Integer, nullable=False)  # 文件大小(字节)
    file_hash = Column(String(64), nullable=False, unique=True)  # MD5哈希
    file_path = Column(String(500), nullable=False)  # 存储路径
    
    # 处理状态
    processing_status = Column(String(50), default='pending')  # pending, processing, completed, failed
    processing_progress = Column(Integer, default=0)  # 处理进度 (0-100)
    is_processed = Column(Boolean, default=False)  # 是否已录入处理
    processing_error = Column(Text)  # 处理错误信息
    
    # 内容信息
    content_preview = Column(Text)  # 内容预览（前500字符）
    content_summary = Column(Text)  # AI生成的内容摘要
    extracted_text = Column(Text)  # 提取的完整文本
    keywords = Column(Text)  # 关键词（逗号分隔）
    language = Column(String(10), default='zh')  # 文档语言
    
    # RAG相关
    chunk_count = Column(Integer, default=0)  # 文本块数量
    vector_count = Column(Integer, default=0)  # 向量数量
    ai_reference_weight = Column(Integer, default=50)  # AI可参考程度比重 (1-100)
    embedding_model = Column(String(100), default='sentence-transformers')  # 使用的嵌入模型
    
    # 元数据
    custom_tags = Column(Text)  # 自定义标签(JSON格式字符串)
    document_category = Column(String(100))  # 文档分类
    document_source = Column(String(100))  # 文档来源
    quality_score = Column(Float, default=0.0)  # 内容质量评分 (0-1)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed_at = Column(DateTime)  # 最后访问时间

class KnowledgeChunk(Base):
    """知识块模型 - 存储文档的分块信息"""
    __tablename__ = "knowledge_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # 块信息
    chunk_index = Column(Integer, nullable=False)  # 在文档中的索引
    chunk_text = Column(Text, nullable=False)  # 文本内容
    chunk_size = Column(Integer, nullable=False)  # 字符数
    
    # 向量信息
    vector_id = Column(String(100))  # 在向量数据库中的ID
    embedding_model = Column(String(100))  # 嵌入模型
    
    # 元数据
    chunk_type = Column(String(50), default='text')  # text, table, image, etc.
    page_number = Column(Integer)  # 所在页码
    section_title = Column(String(200))  # 所属章节标题
    
    created_at = Column(DateTime, default=datetime.utcnow)

class KnowledgeQuery(Base):
    """知识库查询记录 - 用于分析和优化"""
    __tablename__ = "knowledge_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # 查询信息
    query_text = Column(Text, nullable=False)
    query_type = Column(String(50), default='similarity')  # similarity, keyword, hybrid
    
    # 结果信息
    results_count = Column(Integer, default=0)
    top_document_ids = Column(Text)  # 匹配的文档ID列表(JSON格式字符串)
    response_quality = Column(Float)  # 用户反馈的质量评分
    
    # 性能指标
    search_time_ms = Column(Integer)  # 搜索耗时(毫秒)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemSettings(Base):
    """系统设置模型"""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_value = Column(Text)
    setting_type = Column(String(50), default='string')  # string, int, float, bool, json
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 