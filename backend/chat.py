from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator
import openai
import sys
import os
import json
import asyncio

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

router = APIRouter(prefix="/chat", tags=["chat"])

# 配置OpenAI客户端使用DeepSeek
client = openai.OpenAI(
    api_key=Config.DEEPSEEK_API_KEY,
    base_url=Config.DEEPSEEK_BASE_URL
)

# 认证
security = HTTPBearer()

# Pydantic模型
class ChatMessage(BaseModel):
    role: str  # "user" 或 "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []
    use_knowledge_base: bool = False
    model: str = "deepseek-chat"  # 新增模型选择，默认为通用模型

class ChatResponse(BaseModel):
    response: str
    history: List[ChatMessage]

# 依赖函数
def get_db():
    from app import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    from app import verify_token
    return verify_token(credentials)

# 流式聊天API
@router.post("/send-stream")
async def send_message_stream(
    chat_request: ChatRequest,
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    def generate_response():  # 注意：这里改为同步生成器
        try:
            # 构建消息历史
            messages = []
            
            # 添加系统提示
            if chat_request.model == "deepseek-reasoner":
                system_prompt = """你是WePlus校园智能AI助手，专门为中国海洋大学的学生提供服务。
                你是一个具有强大推理能力的AI助手，会通过深度思考来提供准确答案。
                请用友好、专业的语调回答问题，并尽量提供准确、有用的信息。"""
            else:
                system_prompt = """你是WePlus校园智能AI助手，专门为中国海洋大学的学生提供服务。
                你可以帮助学生解答关于校园生活、学习、服务等各种问题。
                请用友好、专业的语调回答问题，并尽量提供准确、有用的信息。"""
            
            if chat_request.use_knowledge_base:
                system_prompt += "\n\n你可以基于上传的知识库文档来回答更专业的问题。"
            
            messages.append({"role": "system", "content": system_prompt})
            
            # 添加历史对话
            for msg in chat_request.history:
                messages.append({"role": msg.role, "content": msg.content})
            
            # 添加当前用户消息
            messages.append({"role": "user", "content": chat_request.message})
            
            # 构建API调用参数
            api_params = {
                "model": chat_request.model,
                "messages": messages,
                "max_tokens": 4000,
                "stream": True
            }
            
            # 只有通用模型支持温度参数
            if chat_request.model == "deepseek-chat":
                api_params["temperature"] = 1.0
            
            print(f"开始调用DeepSeek API，模型: {chat_request.model}")  # 调试日志
            
            # 调用DeepSeek API
            response = client.chat.completions.create(**api_params)
            
            assistant_response = ""
            reasoning_content = ""
            
            print("开始处理流式响应...")  # 调试日志
            
            # 处理流式响应
            for chunk in response:
                print(f"收到chunk: {chunk}")  # 调试日志
                
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    
                    # 处理推理模型的推理内容
                    if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                        reasoning = delta.reasoning_content
                        reasoning_content += reasoning
                        print(f"推理内容: {reasoning}")  # 调试日志
                        
                        # 立即发送推理内容块
                        data = json.dumps({'type': 'reasoning', 'data': reasoning}, ensure_ascii=False)
                        yield f"data: {data}\n\n"
                    
                    # 处理普通内容
                    if hasattr(delta, 'content') and delta.content:
                        content = delta.content
                        assistant_response += content
                        print(f"内容块: {content}")  # 调试日志
                        
                        # 立即发送内容块
                        data = json.dumps({'type': 'content', 'data': content}, ensure_ascii=False)
                        yield f"data: {data}\n\n"
            
            print("流式响应处理完成")  # 调试日志
            
            # 保存聊天记录到数据库
            try:
                from app import ChatHistory, User
                
                user = db.query(User).filter(User.username == username).first()
                if user:
                    # 构建完整响应（包含推理过程）
                    full_response = assistant_response
                    if reasoning_content and chat_request.model == "deepseek-reasoner":
                        full_response = f"[推理过程]\n{reasoning_content}\n\n[最终答案]\n{assistant_response}"
                    
                    chat_record = ChatHistory(
                        user_id=user.id,
                        message=chat_request.message,
                        response=full_response
                    )
                    db.add(chat_record)
                    db.commit()
                    print("聊天记录保存成功")  # 调试日志
            except Exception as e:
                print(f"保存聊天记录失败: {e}")
            
            # 发送完成信号
            done_data = json.dumps({'type': 'done', 'model': chat_request.model}, ensure_ascii=False)
            yield f"data: {done_data}\n\n"
            print("发送完成信号")  # 调试日志
            
        except Exception as e:
            print(f"流式处理错误: {e}")  # 调试日志
            import traceback
            traceback.print_exc()
            error_data = json.dumps({'type': 'error', 'data': f'处理请求时发生错误: {str(e)}'}, ensure_ascii=False)
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        generate_response(),  # 注意：这里调用同步生成器
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream; charset=utf-8",
            "Access-Control-Allow-Origin": "*"
        }
    )

# 保留原有的非流式API用于兼容性
@router.post("/send", response_model=ChatResponse)
async def send_message(
    chat_request: ChatRequest,
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 构建消息历史
        messages = []
        
        # 添加系统提示
        if chat_request.model == "deepseek-reasoner":
            system_prompt = """你是WePlus校园智能AI助手，专门为中国海洋大学的学生提供服务。
            你是一个具有强大推理能力的AI助手，会通过深度思考来提供准确答案。
            请用友好、专业的语调回答问题，并尽量提供准确、有用的信息。"""
        else:
            system_prompt = """你是WePlus校园智能AI助手，专门为中国海洋大学的学生提供服务。
            你可以帮助学生解答关于校园生活、学习、服务等各种问题。
            请用友好、专业的语调回答问题，并尽量提供准确、有用的信息。"""
        
        if chat_request.use_knowledge_base:
            system_prompt += "\n\n你可以基于上传的知识库文档来回答更专业的问题。"
        
        messages.append({"role": "system", "content": system_prompt})
        
        # 添加历史对话
        for msg in chat_request.history:
            messages.append({"role": msg.role, "content": msg.content})
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": chat_request.message})
        
        # 构建API调用参数
        api_params = {
            "model": chat_request.model,
            "messages": messages,
            "max_tokens": 4000,
            "stream": False
        }
        
        # 只有通用模型支持温度参数
        if chat_request.model == "deepseek-chat":
            api_params["temperature"] = 1.0
        
        # 调用DeepSeek API
        response = client.chat.completions.create(**api_params)
        
        assistant_response = response.choices[0].message.content
        reasoning_content = ""
        
        # 处理推理模型的推理内容
        if (hasattr(response.choices[0].message, 'reasoning_content') and 
            response.choices[0].message.reasoning_content):
            reasoning_content = response.choices[0].message.reasoning_content
        
        # 更新历史记录
        updated_history = chat_request.history.copy()
        updated_history.append(ChatMessage(role="user", content=chat_request.message))
        updated_history.append(ChatMessage(role="assistant", content=assistant_response))
        
        # 保存聊天记录到数据库
        from app import ChatHistory, User
        
        user = db.query(User).filter(User.username == username).first()
        if user:
            # 构建完整响应（包含推理过程）
            full_response = assistant_response
            if reasoning_content and chat_request.model == "deepseek-reasoner":
                full_response = f"[推理过程]\n{reasoning_content}\n\n[最终答案]\n{assistant_response}"
            
            chat_record = ChatHistory(
                user_id=user.id,
                message=chat_request.message,
                response=full_response
            )
            db.add(chat_record)
            db.commit()
        
        return ChatResponse(
            response=assistant_response,
            history=updated_history
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {str(e)}"
        )

# 获取用户聊天历史
@router.get("/history")
async def get_chat_history(
    limit: int = 50,
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from app import ChatHistory, User
        
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        chat_history = db.query(ChatHistory).filter(
            ChatHistory.user_id == user.id
        ).order_by(ChatHistory.created_at.desc()).limit(limit).all()
        
        history_data = []
        for record in reversed(chat_history):  # 反转以获得正确的时间顺序
            history_data.extend([
                {"role": "user", "content": record.message},
                {"role": "assistant", "content": record.response}
            ])
        
        return {"history": history_data}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving chat history: {str(e)}"
        )

# 清空聊天历史
@router.delete("/history")
async def clear_chat_history(
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from app import ChatHistory, User
        
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        db.query(ChatHistory).filter(ChatHistory.user_id == user.id).delete()
        db.commit()
        
        return {"message": "Chat history cleared successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing chat history: {str(e)}"
        ) 