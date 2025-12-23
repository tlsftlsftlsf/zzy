#!/bin/bash
# 积分系统云服务器部署脚本
# 适用于 Ubuntu/CentOS 系统

echo "=============================================="
echo "🚀 积分系统云服务器同步服务部署脚本"
echo "=============================================="

# 检查系统类型
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    echo "❌ 无法检测操作系统类型"
    exit 1
fi

echo "📋 检测到操作系统: $OS $VER"

# 安装Python和pip
echo "📦 安装Python和依赖..."
if command -v apt-get >/dev/null 2>&1; then
    # Ubuntu/Debian
    sudo apt update
    sudo apt install python3 python3-pip python3-venv -y
elif command -v yum >/dev/null 2>&1; then
    # CentOS/RHEL
    sudo yum install python3 python3-pip -y
elif command -v dnf >/dev/null 2>&1; then
    # Fedora
    sudo dnf install python3 python3-pip -y
else
    echo "❌ 不支持的包管理器，请手动安装Python3和pip"
    exit 1
fi

# 创建应用目录
echo "📁 创建应用目录..."
sudo mkdir -p /var/www/points-sync
sudo mkdir -p /var/www/points-sync/backups
sudo mkdir -p /var/log/points-sync

# 设置权限
sudo chown -R $USER:$USER /var/www/points-sync
sudo chmod -R 755 /var/www/points-sync

# 复制应用文件
echo "📄 部署应用文件..."
cp cloud_server.py /var/www/points-sync/
chmod +x /var/www/points-sync/cloud_server.py

# 创建虚拟环境
echo "🐍 创建Python虚拟环境..."
cd /var/www/points-sync
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo "📦 安装Python依赖..."
pip install flask flask-cors

# 创建systemd服务
echo "⚙️ 创建系统服务..."
sudo tee /etc/systemd/system/points-sync.service > /dev/null <<EOF
[Unit]
Description=Points System Cloud Sync Service
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=/var/www/points-sync
Environment=PATH=/var/www/points-sync/venv/bin
ExecStart=/var/www/points-sync/venv/bin/python /var/www/points-sync/cloud_server.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/points-sync/access.log
StandardError=append:/var/log/points-sync/error.log

[Install]
WantedBy=multi-user.target
EOF

# 重载systemd配置
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable points-sync

# 创建启动脚本
echo "📝 创建启动脚本..."
sudo tee /usr/local/bin/points-sync > /dev/null <<EOF
#!/bin/bash
# 积分系统云同步服务控制脚本

case "\$1" in
    start)
        echo "🚀 启动云同步服务..."
        sudo systemctl start points-sync
        echo "✅ 服务已启动"
        ;;
    stop)
        echo "🛑 停止云同步服务..."
        sudo systemctl stop points-sync
        echo "✅ 服务已停止"
        ;;
    restart)
        echo "🔄 重启云同步服务..."
        sudo systemctl restart points-sync
        echo "✅ 服务已重启"
        ;;
    status)
        echo "📊 服务状态:"
        sudo systemctl status points-sync --no-pager
        ;;
    logs)
        echo "📋 服务日志:"
        sudo journalctl -u points-sync -f
        ;;
    *)
        echo "用法: \$0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
EOF

sudo chmod +x /usr/local/bin/points-sync

echo "=============================================="
echo "🎉 部署完成！"
echo "=============================================="
echo ""
echo "📋 部署信息:"
echo "   应用目录: /var/www/points-sync"
echo "   配置文件: /var/www/points-sync/cloud_server.py"
echo "   日志目录: /var/log/points-sync"
echo "   系统服务: points-sync"
echo ""
echo "🚀 启动服务:"
echo "   方式1: sudo systemctl start points-sync"
echo "   方式2: points-sync start"
echo ""
echo "📊 管理命令:"
echo "   启动: points-sync start"
echo "   停止: points-sync stop"
echo "   重启: points-sync restart"
echo "   状态: points-sync status"
echo "   日志: points-sync logs"
echo ""
echo "🌐 访问地址:"
echo "   本地: http://localhost:5000"
echo "   局域网: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "📋 API端点:"
echo "   服务信息: GET /api/info"
echo "   健康检查: GET /api/health"
echo "   上传数据: POST /api/upload"
echo "   下载数据: GET /api/download"
echo "   备份列表: GET /api/backup"
echo "   恢复备份: POST /api/restore/<filename>"
echo ""
echo "⚠️  重要提醒:"
echo "   1. 修改 cloud_server.py 中的默认API密钥"
echo "   2. 配置防火墙允许5000端口"
echo "   3. 如需外网访问，配置域名和HTTPS"
echo "   4. 建议设置定期备份任务"
echo ""
echo "=============================================="