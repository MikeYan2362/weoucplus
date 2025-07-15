from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response
import requests
import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER

# 后端API URL - 支持ngrok
BACKEND_URL = Config.NGROK_BACKEND_URL if hasattr(Config, 'NGROK_BACKEND_URL') else f"http://{Config.HOST}:{Config.BACKEND_PORT}"

@app.route('/')
def index():
    """主页 - 检查是否登录"""
    if 'access_token' in session:
        return render_template('dashboard.html')
    else:
        return render_template('login.html')

@app.route('/login')
def login_page():
    """登录页面"""
    return render_template('login.html')

@app.route('/register')
def register_page():
    """注册页面"""
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    """用户仪表板"""
    if 'access_token' not in session:
        return redirect(url_for('login_page'))
    return render_template('dashboard.html')

@app.route('/chat')
def chat_page():
    """聊天页面"""
    if 'access_token' not in session:
        return redirect(url_for('login_page'))
    return render_template('chat.html')

@app.route('/knowledge')
def knowledge_page():
    """知识库管理页面"""
    # 临时去掉登录验证，用于测试
    # if 'access_token' not in session:
    #     return redirect(url_for('login_page'))
    return render_template('knowledge.html')

# API代理路由
@app.route('/api/login', methods=['POST'])
def api_login():
    """登录API代理"""
    try:
        data = request.get_json()
        response = requests.post(f"{BACKEND_URL}/auth/login", json=data)
        
        if response.status_code == 200:
            result = response.json()
            session['access_token'] = result['access_token']
            session['user'] = result['user']
            return jsonify(result)
        else:
            return jsonify(response.json()), response.status_code
            
    except Exception as e:
        return jsonify({"detail": str(e)}), 500

@app.route('/api/register', methods=['POST'])
def api_register():
    """注册API代理"""
    try:
        data = request.get_json()
        response = requests.post(f"{BACKEND_URL}/auth/register", json=data)
        
        if response.status_code == 200:
            result = response.json()
            session['access_token'] = result['access_token']
            session['user'] = result['user']
            return jsonify(result)
        else:
            return jsonify(response.json()), response.status_code
            
    except Exception as e:
        return jsonify({"detail": str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """登出"""
    session.clear()
    return jsonify({"message": "Logged out successfully"})

@app.route('/api/chat/send', methods=['POST'])
def api_chat_send():
    """聊天API代理"""
    if 'access_token' not in session:
        return jsonify({"detail": "Not authenticated"}), 401
    
    try:
        data = request.get_json()
        headers = {"Authorization": f"Bearer {session['access_token']}"}
        response = requests.post(f"{BACKEND_URL}/chat/send", json=data, headers=headers)
        
        return jsonify(response.json()), response.status_code
        
    except Exception as e:
        return jsonify({"detail": str(e)}), 500

@app.route('/api/chat/send-stream', methods=['POST'])
def api_chat_send_stream():
    """流式聊天API代理"""
    if 'access_token' not in session:
        return jsonify({"detail": "Not authenticated"}), 401
    
    try:
        data = request.get_json()
        headers = {
            "Authorization": f"Bearer {session['access_token']}",
            "Content-Type": "application/json"
        }
        
        print(f"前端代理: 发送请求到后端，数据: {data}")  # 调试日志
        
        # 使用stream=True来获取流式响应
        response = requests.post(
            f"{BACKEND_URL}/chat/send-stream", 
            json=data, 
            headers=headers,
            stream=True
        )
        
        print(f"前端代理: 后端响应状态码: {response.status_code}")  # 调试日志
        
        def generate():
            try:
                # 直接逐行转发，保持SSE格式
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        print(f"前端代理: 转发数据行: {line}")  # 调试日志
                        yield f"{line}\n"
            except Exception as e:
                print(f"前端代理: 流式处理错误: {e}")  # 调试日志
                error_data = json.dumps({'type': 'error', 'data': f'Stream error: {str(e)}'}, ensure_ascii=False)
                yield f"data: {error_data}\n\n"
        
        return Response(
            generate(),
            content_type='text/event-stream; charset=utf-8',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*'
            }
        )
        
    except Exception as e:
        print(f"前端代理: 请求错误: {e}")  # 调试日志
        return jsonify({"detail": str(e)}), 500

@app.route('/api/chat/history')
def api_chat_history():
    """获取聊天历史API代理"""
    if 'access_token' not in session:
        return jsonify({"detail": "Not authenticated"}), 401
    
    try:
        headers = {"Authorization": f"Bearer {session['access_token']}"}
        response = requests.get(f"{BACKEND_URL}/chat/history", headers=headers)
        
        return jsonify(response.json()), response.status_code
        
    except Exception as e:
        return jsonify({"detail": str(e)}), 500

# 知识库API代理
@app.route('/api/knowledge/documents')
def api_knowledge_documents():
    """获取知识库文档列表API代理"""
    # 临时去掉验证，用于测试
    # if 'access_token' not in session:
    #     return jsonify({"detail": "Not authenticated"}), 401
    
    try:
        headers = {}
        if 'access_token' in session:
            headers = {"Authorization": f"Bearer {session['access_token']}"}
        
        # 转发查询参数
        params = request.args.to_dict()
        response = requests.get(f"{BACKEND_URL}/api/knowledge/documents", headers=headers, params=params)
        
        return jsonify(response.json()), response.status_code
        
    except Exception as e:
        return jsonify({"detail": str(e)}), 500

@app.route('/api/knowledge/supported-types')
def api_knowledge_supported_types():
    """获取支持的文件类型API代理"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/knowledge/supported-types")
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"detail": str(e)}), 500

@app.route('/api/knowledge/upload', methods=['POST'])
def api_knowledge_upload():
    """文件上传API代理"""
    try:
        # 转发文件上传请求
        files = {}
        for key, file in request.files.items():
            files[key] = (file.filename, file.read(), file.content_type)
        
        headers = {}
        if 'access_token' in session:
            headers = {"Authorization": f"Bearer {session['access_token']}"}
        
        response = requests.post(f"{BACKEND_URL}/api/knowledge/upload", files=files, headers=headers, data=request.form)
        
        return jsonify(response.json()), response.status_code
        
    except Exception as e:
        return jsonify({"detail": str(e)}), 500

@app.route('/api/knowledge/documents/<int:doc_id>', methods=['GET', 'PUT', 'DELETE'])
def api_knowledge_document_detail(doc_id):
    """单个文档的详细操作API代理"""
    try:
        headers = {}
        if 'access_token' in session:
            headers = {"Authorization": f"Bearer {session['access_token']}"}
        
        if request.method == 'GET':
            response = requests.get(f"{BACKEND_URL}/api/knowledge/documents/{doc_id}", headers=headers)
        elif request.method == 'PUT':
            data = request.get_json()
            response = requests.put(f"{BACKEND_URL}/api/knowledge/documents/{doc_id}", json=data, headers=headers)
        elif request.method == 'DELETE':
            response = requests.delete(f"{BACKEND_URL}/api/knowledge/documents/{doc_id}", headers=headers)
        
        return jsonify(response.json()), response.status_code
        
    except Exception as e:
        return jsonify({"detail": str(e)}), 500

@app.route('/api/knowledge/stats')
def api_knowledge_stats():
    """获取知识库统计信息API代理"""
    try:
        headers = {}
        if 'access_token' in session:
            headers = {"Authorization": f"Bearer {session['access_token']}"}
        
        response = requests.get(f"{BACKEND_URL}/api/knowledge/stats", headers=headers)
        
        return jsonify(response.json()), response.status_code
        
    except Exception as e:
        return jsonify({"detail": str(e)}), 500

if __name__ == '__main__':
    app.run(host=Config.HOST, port=Config.FRONTEND_PORT, debug=Config.DEBUG) 