#!/usr/bin/env python3
"""
WePlus 开发者后台管理系统
独立的可视化管理平台，用于管理用户、知识库和文件
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, send_file
from flask_cors import CORS
import sqlite3
import os
import sys
import json
from datetime import datetime, timedelta
import hashlib
import shutil
from pathlib import Path
import mimetypes
import logging
from werkzeug.utils import secure_filename

# 添加父目录到Python路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# 导入配置
try:
    from config import Config
    DATABASE_URL = Config.DATABASE_URL.replace('sqlite:///', '')
    CHROMA_DB_PATH = Config.CHROMA_DB_PATH
except ImportError:
    DATABASE_URL = os.path.join(parent_dir, 'database', 'weplus.db')
    CHROMA_DB_PATH = os.path.join(parent_dir, 'knowledge_base', 'chromadb')

app = Flask(__name__)
app.secret_key = 'admin-system-secret-key-change-in-production'
CORS(app)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 管理员配置
ADMIN_CREDENTIALS = {
    'username': 'admin',
    'password': 'admin123'  # 在生产环境中应该使用更强的密码
}

def get_db_connection():
    """获取数据库连接"""
    try:
        conn = sqlite3.connect(DATABASE_URL)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return None

def require_login(f):
    """登录验证装饰器"""
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
@require_login
def dashboard():
    """管理后台首页"""
    try:
        conn = get_db_connection()
        if not conn:
            flash('数据库连接失败', 'error')
            return render_template('dashboard.html', stats={})
        
        cursor = conn.cursor()
        
        # 获取统计数据
        stats = {}
        
        # 用户统计
        cursor.execute('SELECT COUNT(*) FROM users')
        stats['total_users'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
        stats['active_users'] = cursor.fetchone()[0]
        
        # 聊天记录统计
        cursor.execute('SELECT COUNT(*) FROM chat_history')
        stats['total_chats'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT user_id) FROM chat_history')
        stats['chatting_users'] = cursor.fetchone()[0]
        
        # 知识库统计
        cursor.execute('SELECT COUNT(*) FROM knowledge_documents')
        stats['total_documents'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(file_size) FROM knowledge_documents')
        total_size = cursor.fetchone()[0] or 0
        stats['total_storage_mb'] = round(total_size / (1024 * 1024), 2)
        
        cursor.execute('SELECT COUNT(*) FROM knowledge_chunks')
        stats['total_chunks'] = cursor.fetchone()[0]
        
        # 最近活动
        cursor.execute('''
            SELECT u.username, COUNT(ch.id) as chat_count, MAX(ch.created_at) as last_chat
            FROM users u
            LEFT JOIN chat_history ch ON u.id = ch.user_id
            GROUP BY u.id, u.username
            ORDER BY last_chat DESC
            LIMIT 5
        ''')
        stats['recent_activities'] = cursor.fetchall()
        
        conn.close()
        
        return render_template('dashboard.html', stats=stats)
        
    except Exception as e:
        logger.error(f"获取统计数据失败: {e}")
        flash(f'获取数据失败: {e}', 'error')
        return render_template('dashboard.html', stats={})

@app.route('/login', methods=['GET', 'POST'])
def login():
    """管理员登录"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if (username == ADMIN_CREDENTIALS['username'] and 
            password == ADMIN_CREDENTIALS['password']):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('登录成功！', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """登出"""
    session.clear()
    flash('已退出登录', 'info')
    return redirect(url_for('login'))

@app.route('/users')
@require_login
def users():
    """用户管理页面"""
    try:
        conn = get_db_connection()
        if not conn:
            flash('数据库连接失败', 'error')
            return render_template('users.html', users=[])
        
        cursor = conn.cursor()
        
        # 获取用户列表和聊天统计
        cursor.execute('''
            SELECT u.id, u.username, u.email, u.is_active, u.created_at,
                   COUNT(ch.id) as chat_count,
                   MAX(ch.created_at) as last_chat,
                   COUNT(kd.id) as document_count
            FROM users u
            LEFT JOIN chat_history ch ON u.id = ch.user_id
            LEFT JOIN knowledge_documents kd ON u.id = kd.user_id
            GROUP BY u.id, u.username, u.email, u.is_active, u.created_at
            ORDER BY u.created_at DESC
        ''')
        
        users_data = cursor.fetchall()
        conn.close()
        
        return render_template('users.html', users=users_data)
        
    except Exception as e:
        logger.error(f"获取用户数据失败: {e}")
        flash(f'获取用户数据失败: {e}', 'error')
        return render_template('users.html', users=[])

@app.route('/knowledge')
@require_login
def knowledge():
    """知识库管理页面"""
    try:
        conn = get_db_connection()
        if not conn:
            flash('数据库连接失败', 'error')
            return render_template('knowledge.html', documents=[])
        
        cursor = conn.cursor()
        
        # 获取文档列表
        cursor.execute('''
            SELECT kd.id, kd.filename, kd.file_type, kd.file_size, 
                   kd.processing_status, kd.chunk_count, kd.created_at,
                   u.username, kd.content_preview, kd.ai_reference_weight
            FROM knowledge_documents kd
            LEFT JOIN users u ON kd.user_id = u.id
            ORDER BY kd.created_at DESC
        ''')
        
        documents = cursor.fetchall()
        conn.close()
        
        return render_template('knowledge.html', documents=documents)
        
    except Exception as e:
        logger.error(f"获取知识库数据失败: {e}")
        flash(f'获取知识库数据失败: {e}', 'error')
        return render_template('knowledge.html', documents=[])

@app.route('/files')
@require_login
def files():
    """文件管理页面"""
    try:
        # 获取上传目录的文件列表
        uploads_dir = os.path.join(parent_dir, 'uploads')
        files_data = []
        
        if os.path.exists(uploads_dir):
            for root, dirs, files in os.walk(uploads_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, uploads_dir)
                    
                    try:
                        stat = os.stat(file_path)
                        files_data.append({
                            'name': file,
                            'path': relative_path,
                            'size': stat.st_size,
                            'modified': datetime.fromtimestamp(stat.st_mtime),
                            'type': mimetypes.guess_type(file)[0] or 'unknown'
                        })
                    except Exception as e:
                        logger.warning(f"获取文件信息失败 {file_path}: {e}")
        
        # 按修改时间排序
        files_data.sort(key=lambda x: x['modified'], reverse=True)
        
        return render_template('files.html', files=files_data)
        
    except Exception as e:
        logger.error(f"获取文件列表失败: {e}")
        flash(f'获取文件列表失败: {e}', 'error')
        return render_template('files.html', files=[])

# API路由
@app.route('/api/user/<int:user_id>/toggle', methods=['POST'])
@require_login
def toggle_user_status(user_id):
    """切换用户状态"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': '数据库连接失败'})
        
        cursor = conn.cursor()
        
        # 获取当前状态
        cursor.execute('SELECT is_active FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'success': False, 'message': '用户不存在'})
        
        # 切换状态
        new_status = 0 if result[0] else 1
        cursor.execute('UPDATE users SET is_active = ? WHERE id = ?', (new_status, user_id))
        conn.commit()
        conn.close()
        
        status_text = '启用' if new_status else '禁用'
        return jsonify({'success': True, 'message': f'用户已{status_text}', 'new_status': new_status})
        
    except Exception as e:
        logger.error(f"切换用户状态失败: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/document/<int:doc_id>/delete', methods=['POST'])
@require_login
def delete_document(doc_id):
    """删除文档"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': '数据库连接失败'})
        
        cursor = conn.cursor()
        
        # 获取文档信息
        cursor.execute('SELECT file_path FROM knowledge_documents WHERE id = ?', (doc_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'success': False, 'message': '文档不存在'})
        
        # 删除数据库记录
        cursor.execute('DELETE FROM knowledge_chunks WHERE document_id = ?', (doc_id,))
        cursor.execute('DELETE FROM knowledge_documents WHERE id = ?', (doc_id,))
        
        # 删除文件
        file_path = os.path.join(parent_dir, result[0])
        if os.path.exists(file_path):
            os.remove(file_path)
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '文档已删除'})
        
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/stats')
@require_login
def api_stats():
    """获取统计数据API"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': '数据库连接失败'})
        
        cursor = conn.cursor()
        
        # 获取过去7天的聊天统计
        cursor.execute('''
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM chat_history
            WHERE created_at >= date('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY date
        ''')
        chat_trend = cursor.fetchall()
        
        # 获取文件类型分布
        cursor.execute('''
            SELECT file_type, COUNT(*) as count
            FROM knowledge_documents
            GROUP BY file_type
            ORDER BY count DESC
        ''')
        file_types = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'chat_trend': [{'date': row[0], 'count': row[1]} for row in chat_trend],
            'file_types': [{'type': row[0], 'count': row[1]} for row in file_types]
        })
        
    except Exception as e:
        logger.error(f"获取统计数据失败: {e}")
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    # 创建模板目录
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    print("🎉 WePlus 开发者后台管理系统启动中...")
    print("=" * 50)
    print("📍 访问地址: http://localhost:9000")
    print("👤 管理员账号: admin")
    print("🔑 管理员密码: admin123")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=9000, debug=True) 