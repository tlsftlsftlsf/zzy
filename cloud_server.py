#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云服务器同步API服务 + 静态文件服务
适用于积分系统的云端数据同步和前端页面服务

部署说明：
1. pip install flask flask-cors
2. python cloud_server.py
3. 服务将运行在 http://localhost:5000
4. 访问 http://localhost:5000 查看积分系统前端
"""

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import json
import os
import uuid
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)  # 允许跨域访问

# 数据文件路径
DATA_FILE = '/tmp/points-data.json'
BACKUP_DIR = '/tmp/points-backups/'

# 确保目录存在
os.makedirs(BACKUP_DIR, exist_ok=True)

# API密钥验证（可选）
API_KEYS = {
    'default': 'your-secret-api-key-here',  # 默认密钥，生产环境中请更改
    # 可以添加更多密钥
}

def verify_api_key():
    """验证API密钥"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return True  # 如果没有配置密钥，则允许访问
    
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]  # 移除 'Bearer ' 前缀
        return token in API_KEYS.values()
    
    return False

@app.route('/api/upload', methods=['POST'])
def upload_data():
    """上传数据到云服务器"""
    try:
        # 验证API密钥
        if not verify_api_key():
            return jsonify({'status': 'error', 'message': 'API密钥验证失败'}), 401
        
        data = request.json
        
        data
        if not data:
            return jsonify({'status': 'error', 'message': '没有收到数据'}), 400
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 创建备份
        if os.path.exists(DATA_FILE):
            backup_path = f"{BACKUP_DIR}points-data_{timestamp}_{uuid.uuid4().hex[:8]}.json"
            try:
                os.rename(DATA_FILE, backup_path)
                logger.info(f"数据已备份到: {backup_path}")
            except Exception as e:
                logger.warning(f"备份失败: {e}")
        
        # 保存新数据
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"数据上传成功，时间戳: {timestamp}")
        return jsonify({'status': 'success', 'message': '数据上传成功', 'timestamp': timestamp})
        
    except Exception as e:
        logger.error(f"上传失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/download', methods=['GET'])
def download_data():
    """从云服务器下载数据"""
    try:
        # 验证API密钥
        if not verify_api_key():
            return jsonify({'status': 'error', 'message': 'API密钥验证失败'}), 401
        
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info("数据下载成功")
            return jsonify({'status': 'success', 'data': data})
        else:
            logger.info("没有找到数据文件，返回空数据")
            return jsonify({'status': 'success', 'data': {}})
            
    except Exception as e:
        logger.error(f"下载失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/backup', methods=['GET'])
def list_backups():
    """获取备份列表"""
    try:
        # 验证API密钥
        if not verify_api_key():
            return jsonify({'status': 'error', 'message': 'API密钥验证失败'}), 401
        
        if os.path.exists(BACKUP_DIR):
            backups = []
            for filename in os.listdir(BACKUP_DIR):
                if filename.endswith('.json'):
                    file_path = os.path.join(BACKUP_DIR, filename)
                    try:
                        file_time = os.path.getmtime(file_path)
                        file_size = os.path.getsize(file_path)
                        backups.append({
                            'filename': filename,
                            'timestamp': datetime.fromtimestamp(file_time).strftime('%Y-%m-%d %H:%M:%S'),
                            'size': file_size
                        })
                    except Exception as e:
                        logger.warning(f"读取备份文件信息失败: {filename}, {e}")
            
            # 按时间倒序排列
            backups.sort(key=lambda x: x['timestamp'], reverse=True)
            logger.info(f"返回 {len(backups)} 个备份文件")
            return jsonify({'status': 'success', 'backups': backups})
        else:
            return jsonify({'status': 'success', 'backups': []})
            
    except Exception as e:
        logger.error(f"获取备份列表失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/restore/<filename>', methods=['POST'])
def restore_backup(filename):
    """恢复备份数据"""
    try:
        # 验证API密钥
        if not verify_api_key():
            return jsonify({'status': 'error', 'message': 'API密钥验证失败'}), 401
        
        # 清理文件名，防止路径遍历攻击
        filename = os.path.basename(filename)
        backup_path = os.path.join(BACKUP_DIR, filename)
        
        if not os.path.exists(backup_path):
            return jsonify({'status': 'error', 'message': '备份文件不存在'}), 404
        
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"备份恢复成功: {filename}")
            return jsonify({'status': 'success', 'data': data, 'filename': filename})
        except json.JSONDecodeError as e:
            return jsonify({'status': 'error', 'message': f'备份文件格式错误: {str(e)}'}), 400
            
    except Exception as e:
        logger.error(f"恢复备份失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/')
def index():
    """积分系统前端页面"""
    return send_from_directory('.', 'index.html')

@app.route('/api/info', methods=['GET'])
def server_info():
    """服务器信息"""
    return jsonify({
        'name': '积分系统云同步服务',
        'version': '1.0.0',
        'description': '为积分系统提供云端数据同步服务和前端页面',
        'endpoints': {
            'index': '/',
            'upload': '/api/upload',
            'download': '/api/download', 
            'backup': '/api/backup',
            'restore': '/api/restore/<filename>',
            'health': '/api/health'
        }
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 'error', 'message': 'API端点不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'status': 'error', 'message': '服务器内部错误'}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("🌟 积分系统云同步服务启动中...")
    print("=" * 50)
    print(f"📁 数据文件: {DATA_FILE}")
    print(f"📁 备份目录: {BACKUP_DIR}")
    print(f"🔑 API密钥: {list(API_KEYS.keys())}")
    print("=" * 50)
    print("🚀 服务地址:")
    print("   本地访问: http://localhost:5000")
    print("   局域网访问: http://0.0.0.0:5000")
    print("=" * 50)
    print("📋 可用API端点:")
    print("   GET  /api/info        - 服务信息")
    print("   GET  /api/health      - 健康检查")
    print("   GET  /api/download    - 下载数据")
    print("   POST /api/upload      - 上传数据")
    print("   GET  /api/backup      - 备份列表")
    print("   POST /api/restore/<file> - 恢复备份")
    print("=" * 50)
    print("⚠️  生产环境建议:")
    print("   1. 修改默认API密钥")
    print("   2. 使用HTTPS")
    print("   3. 配置防火墙")
    print("   4. 设置定时备份")
    print("=" * 50)
    
    # 启动服务器
    app.run(host='0.0.0.0', port=5000, debug=True)