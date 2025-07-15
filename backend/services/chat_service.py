"""
现代化聊天服务层
包含缓存、重试机制、性能监控
"""
import asyncio
import json
import logging
import time
from typing import List, Optional, Dict, Any, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
import openai
from tenacity import retry, stop_after_attempt, wait_exponential
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.models import User, ChatHistory

logger = logging.getLogger(__name__)

class ChatModel(str, Enum):
    """聊天模型枚举"""
    DEEPSEEK_CHAT = "deepseek-chat"
    DEEPSEEK_REASONER = "deepseek-reasoner"

@dataclass
class ChatMessage:
    """聊天消息数据类"""
    role: str
    content: str
    timestamp: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass 
class ChatRequest:
    """聊天请求数据类"""
    message: str
    history: List[ChatMessage]
    model: ChatModel = ChatModel.DEEPSEEK_CHAT
    use_knowledge_base: bool = False
    stream: bool = True
    temperature: Optional[float] = None
    max_tokens: int = 4000

@dataclass
class ChatResponse:
    """聊天响应数据类"""
    content: str
    reasoning: Optional[str] = None
    model: str = ""
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class ChatService:
    """聊天服务类"""
    
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            timeout=settings.deepseek_timeout
        )
        self._request_cache = {}
        self._cache_ttl = 300  # 5分钟缓存
        
    def _get_system_prompt(self, model: ChatModel, use_knowledge_base: bool = False) -> str:
        """获取系统提示词"""
        base_prompt = {
            ChatModel.DEEPSEEK_CHAT: """你是WePlus校园智能AI助手，专门为中国海洋大学的学生提供服务。
你可以帮助学生解答关于校园生活、学习、服务等各种问题。
请用友好、专业的语调回答问题，并尽量提供准确、有用的信息。""",
            
            ChatModel.DEEPSEEK_REASONER: """你是WePlus校园智能AI助手，专门为中国海洋大学的学生提供服务。
你是一个具有强大推理能力的AI助手，会通过深度思考来提供准确答案。
请用友好、专业的语调回答问题，并尽量提供准确、有用的信息。"""
        }
        
        prompt = base_prompt.get(model, base_prompt[ChatModel.DEEPSEEK_CHAT])
        
        if use_knowledge_base:
            prompt += "\n\n你可以基于上传的知识库文档来回答更专业的问题。"
            
        return prompt
    
    def _build_messages(self, request: ChatRequest) -> List[Dict[str, str]]:
        """构建消息列表"""
        messages = []
        
        # 添加系统提示
        system_prompt = self._get_system_prompt(request.model, request.use_knowledge_base)
        messages.append({"role": "system", "content": system_prompt})
        
        # 添加历史消息
        for msg in request.history:
            messages.append({"role": msg.role, "content": msg.content})
        
        # 添加当前消息
        messages.append({"role": "user", "content": request.message})
        
        return messages
    
    def _get_cache_key(self, messages: List[Dict[str, str]], model: str) -> str:
        """生成缓存键"""
        content = json.dumps(messages, sort_keys=True) + model
        import hashlib
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """检查缓存是否有效"""
        return time.time() - cache_entry["timestamp"] < self._cache_ttl
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _call_api(self, messages: List[Dict[str, str]], model: ChatModel, stream: bool = False, **kwargs) -> Any:
        """调用DeepSeek API（带重试机制）"""
        api_params = {
            "model": model.value,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4000),
            "stream": stream
        }
        
        # 只有通用模型支持温度参数
        if model == ChatModel.DEEPSEEK_CHAT:
            api_params["temperature"] = kwargs.get("temperature", 1.0)
        
        logger.info(f"🤖 调用DeepSeek API: {model.value}, stream={stream}")
        
        try:
            response = self.client.chat.completions.create(**api_params)
            return response
        except Exception as e:
            logger.error(f"❌ DeepSeek API调用失败: {e}")
            raise
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """非流式聊天"""
        messages = self._build_messages(request)
        
        # 检查缓存
        cache_key = self._get_cache_key(messages, request.model.value)
        if cache_key in self._request_cache:
            cache_entry = self._request_cache[cache_key]
            if self._is_cache_valid(cache_entry):
                logger.info(f"💾 聊天缓存命中: {cache_key[:8]}...")
                return cache_entry["response"]
        
        # 调用API
        response = await self._call_api(
            messages, 
            request.model, 
            stream=False,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        # 解析响应
        chat_response = ChatResponse(
            content=response.choices[0].message.content,
            model=request.model.value,
            usage=response.usage.model_dump() if response.usage else None
        )
        
        # 处理推理模型的推理内容
        if (hasattr(response.choices[0].message, 'reasoning_content') and 
            response.choices[0].message.reasoning_content):
            chat_response.reasoning = response.choices[0].message.reasoning_content
        
        # 缓存响应
        self._request_cache[cache_key] = {
            "response": chat_response,
            "timestamp": time.time()
        }
        
        return chat_response
    
    async def chat_stream(self, request: ChatRequest) -> AsyncGenerator[Dict[str, Any], None]:
        """流式聊天"""
        messages = self._build_messages(request)
        
        # 调用API
        response = await self._call_api(
            messages, 
            request.model, 
            stream=True,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        assistant_response = ""
        reasoning_content = ""
        
        try:
            for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    
                    # 处理推理内容
                    if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                        reasoning = delta.reasoning_content
                        reasoning_content += reasoning
                        yield {
                            "type": "reasoning",
                            "data": reasoning,
                            "model": request.model.value
                        }
                    
                    # 处理普通内容
                    if hasattr(delta, 'content') and delta.content:
                        content = delta.content
                        assistant_response += content
                        yield {
                            "type": "content",
                            "data": content,
                            "model": request.model.value
                        }
            
            # 发送完成信号
            yield {
                "type": "done",
                "model": request.model.value,
                "total_content": assistant_response,
                "reasoning": reasoning_content if reasoning_content else None
            }
            
        except Exception as e:
            logger.error(f"❌ 流式聊天处理错误: {e}")
            yield {
                "type": "error",
                "data": f"处理请求时发生错误: {str(e)}",
                "model": request.model.value
            }
    
    async def save_chat_history(self, db: Session, user_id: int, message: str, response: str, model: str = ""):
        """保存聊天历史"""
        try:
            chat_record = ChatHistory(
                user_id=user_id,
                message=message,
                response=response,
                model=model if hasattr(ChatHistory, 'model') else None
            )
            db.add(chat_record)
            db.commit()
            logger.info(f"💾 聊天历史保存成功: user_id={user_id}")
        except Exception as e:
            logger.error(f"❌ 聊天历史保存失败: {e}")
            db.rollback()
            raise
    
    async def get_chat_history(self, db: Session, user_id: int, limit: int = 50) -> List[ChatHistory]:
        """获取聊天历史"""
        try:
            history = db.query(ChatHistory)\
                .filter(ChatHistory.user_id == user_id)\
                .order_by(ChatHistory.created_at.desc())\
                .limit(limit)\
                .all()
            
            return list(reversed(history))  # 按时间正序返回
        except Exception as e:
            logger.error(f"❌ 获取聊天历史失败: {e}")
            return []
    
    async def clear_chat_history(self, db: Session, user_id: int):
        """清空聊天历史"""
        try:
            db.query(ChatHistory)\
                .filter(ChatHistory.user_id == user_id)\
                .delete()
            db.commit()
            logger.info(f"🗑️ 聊天历史清空成功: user_id={user_id}")
        except Exception as e:
            logger.error(f"❌ 清空聊天历史失败: {e}")
            db.rollback()
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取服务指标"""
        return {
            "cache_size": len(self._request_cache),
            "cache_hit_rate": 0.0,  # 可以添加更详细的统计
            "api_timeout": settings.deepseek_timeout,
            "model_support": [model.value for model in ChatModel]
        }
    
    def clear_cache(self):
        """清理缓存"""
        self._request_cache.clear()
        logger.info("🧹 聊天服务缓存已清理")

# 全局聊天服务实例
chat_service = ChatService()

def get_chat_service() -> ChatService:
    """获取聊天服务实例"""
    return chat_service 