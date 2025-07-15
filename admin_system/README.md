# WePlus 开发者后台管理系统

## 系统简介

WePlus 开发者后台管理系统是一个独立的可视化管理平台，专为管理校园智能助手系统而设计。提供用户管理、知识库管理、文件管理等核心功能。

## 功能特性

### 🎯 核心功能
- **用户管理**: 可视化管理所有注册用户信息，支持用户状态切换
- **知识库管理**: 完整的RAG系统数据库管理，文档处理状态监控
- **文件管理系统**: 上传、删除、分类等完整文件管理功能
- **系统监控**: 实时系统状态监控和数据统计

### 🎨 界面特性
- 现代化响应式设计
- 支持移动端访问
- 深色/浅色主题切换
- 直观的数据可视化图表

## 快速开始

### 1. 系统要求
- Python 3.8+
- Flask 3.0+
- 可选: 与主系统共享数据库

### 2. 启动方式

#### Windows用户
```bash
# 双击运行
start_admin.cmd

# 或命令行运行
python app.py
```

#### Linux/Mac用户
```bash
# 直接运行
python3 app.py

# 或使用启动脚本
python3 start_admin.py
```

### 3. 访问系统
- **访问地址**: http://localhost:9000
- **默认账号**: admin
- **默认密码**: admin123

## 页面功能详解

### 📊 仪表板 (Dashboard)
- **系统概览**: 用户总数、聊天记录、知识库文档等关键指标
- **活动趋势**: 过去7天/30天的聊天活动趋势图
- **文件分布**: 知识库中不同类型文件的分布图表
- **系统状态**: 数据库、RAG系统、文件存储状态监控
- **快速操作**: 一键跳转到各个管理模块

### 👥 用户管理 (Users)
- **用户列表**: 显示所有注册用户及其基本信息
- **状态管理**: 启用/禁用用户账户
- **搜索筛选**: 按用户名、邮箱、状态筛选
- **详情查看**: 查看用户详细信息和活动记录
- **数据导出**: 导出用户数据为JSON格式

#### 用户操作功能：
- 👁️ 查看用户详情
- 🔄 切换用户状态（启用/禁用）
- 💬 查看聊天记录
- 📊 用户活动统计

### 🗃️ 知识库管理 (Knowledge)
- **文档列表**: 显示所有上传的知识库文档
- **处理状态**: 监控文档的RAG处理状态
- **RAG系统状态**: 向量数据库、文本处理、语义搜索状态
- **文档操作**: 查看、测试、重新处理、删除文档
- **权重管理**: 调整文档在AI推理中的参考权重

#### RAG系统功能：
- 🧠 实时监控向量数据库状态
- 🔍 测试文档检索效果
- ⚡ 一键优化RAG系统性能
- 📈 知识块统计和分析

### 📁 文件管理 (Files)
- **多视图模式**: 支持网格视图和列表视图
- **完整文件操作**: 上传、下载、删除、重命名
- **智能分类**: 按文件类型自动分类显示
- **批量操作**: 支持多文件选择和批量处理
- **搜索筛选**: 按名称、类型、大小、时间筛选

#### 文件操作功能：
- 📤 拖拽上传文件
- 📂 创建文件夹
- 🔍 实时搜索文件
- 📊 文件统计分析
- 💾 批量下载/删除

## 数据库架构

### 主数据库 (SQLite)
```sql
-- 用户表
users: id, username, email, password_hash, is_active, created_at

-- 聊天记录表  
chat_history: id, user_id, message, response, created_at

-- 知识库文档表
knowledge_documents: id, user_id, filename, file_type, file_size, 
                     processing_status, chunk_count, ai_reference_weight, created_at

-- 知识块表
knowledge_chunks: id, document_id, content, vector_id, metadata
```

### 向量数据库 (ChromaDB)
- 存储文档向量嵌入
- 支持语义相似度搜索
- 用于RAG系统知识检索

## 安全配置

### 生产环境配置
1. **修改默认密码**
```python
# 在 app.py 中修改
ADMIN_CREDENTIALS = {
    'username': 'your_admin_username',
    'password': 'your_secure_password'
}
```

2. **设置安全密钥**
```python
app.secret_key = 'your-production-secret-key'
```

3. **限制访问IP**
```python
# 仅允许本地访问
app.run(host='127.0.0.1', port=9000)

# 或指定特定IP
app.run(host='your.server.ip', port=9000)
```

## API接口

### 用户管理API
- `POST /api/user/<id>/toggle` - 切换用户状态
- `GET /api/stats` - 获取系统统计数据

### 知识库管理API  
- `POST /api/document/<id>/delete` - 删除文档
- `POST /api/document/<id>/reprocess` - 重新处理文档

### 文件管理API
- `POST /api/file/upload` - 上传文件
- `DELETE /api/file/<path>` - 删除文件

## 技术栈

### 后端技术
- **Flask 3.0**: Web框架
- **SQLite**: 主数据库
- **ChromaDB**: 向量数据库
- **Flask-CORS**: 跨域支持

### 前端技术
- **Bootstrap 5**: UI框架
- **Chart.js**: 数据可视化
- **Font Awesome**: 图标库
- **Vanilla JavaScript**: 交互逻辑

## 系统集成

### 与主系统的关系
- **数据共享**: 读取主系统的用户和知识库数据
- **独立部署**: 可独立运行，不影响主系统
- **安全隔离**: 独立的认证系统和端口

### 部署建议
- **开发环境**: 直接运行 `python app.py`
- **测试环境**: 使用 `gunicorn` 或 `waitress` 部署
- **生产环境**: 配置反向代理 (Nginx) 和HTTPS

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库文件路径
   - 确认数据库文件权限

2. **页面显示异常**
   - 清除浏览器缓存
   - 检查CSS/JS资源加载

3. **功能按钮无响应**
   - 检查浏览器控制台错误
   - 确认JavaScript正常加载

### 日志查看
```bash
# 查看运行日志
python app.py > admin.log 2>&1

# 实时监控日志
tail -f admin.log
```

## 版本信息

- **版本**: v1.0.0
- **更新日期**: 2024-01-20
- **兼容性**: Python 3.8+, 现代浏览器

## 支持与反馈

如遇到问题或需要新功能，请通过以下方式联系：
- 📧 技术支持邮箱
- 💬 在线客服
- 📱 技术交流群

---

**开发团队**: WePlus Development Team  
**许可证**: MIT License 