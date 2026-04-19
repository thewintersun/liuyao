#!/bin/bash
# ============================================================
#  六爻解卦 — 零停机部署脚本
#
#  首次使用:  bash deploy.sh --setup
#  日常部署:  bash deploy.sh
# ============================================================
set -e

# ===== 配置区（根据实际环境修改）=====
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
SERVICE_NAME="liuyao"
MIN_NODE_VERSION=18
# =====================================

cd "$PROJECT_DIR"

# ---------- 环境检查 ----------
check_node_version() {
    if ! command -v node &> /dev/null; then
        echo "错误: 未找到 node 命令。请先安装 Node.js >= $MIN_NODE_VERSION"
        echo ""
        echo "推荐使用 NodeSource 安装:"
        echo "  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
        echo "  sudo apt-get install -y nodejs"
        exit 1
    fi

    NODE_VERSION=$(node -v | sed 's/v//' | cut -d. -f1)
    if [ "$NODE_VERSION" -lt "$MIN_NODE_VERSION" ]; then
        echo "错误: Node.js 版本过低 (当前: $(node -v)，需要: >= v$MIN_NODE_VERSION)"
        echo ""
        echo "请先升级 Node.js:"
        echo "  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
        echo "  sudo apt-get install -y nodejs"
        exit 1
    fi

    echo ">>> Node.js 版本检查通过: $(node -v)"
}

check_node_version

# ---------- 首次安装 ----------
if [ "$1" = "--setup" ]; then
    echo "===== 首次安装 ====="

    # 1. 创建虚拟环境（如不存在）
    if [ ! -d "$VENV_DIR" ]; then
        echo ">>> 创建 Python 虚拟环境..."
        python3 -m venv "$VENV_DIR"
    fi

    # 2. 安装依赖
    echo ">>> 安装 Python 依赖..."
    "$VENV_DIR/bin/pip" install -r requirements.txt

    # 3. 安装前端依赖并构建
    echo ">>> 构建前端..."
    cd "$PROJECT_DIR/frontend"
    npm install
    npm run build
    cd "$PROJECT_DIR"

    # 4. 生成 systemd 服务文件
    echo ">>> 安装 systemd 服务..."
    SERVICE_FILE="$PROJECT_DIR/deploy/liuyao.service"

    if [ ! -f "$SERVICE_FILE" ]; then
        echo "错误: 找不到服务模板文件 $SERVICE_FILE"
        exit 1
    fi

    # 如果服务被 masked，先 unmask
    if systemctl is-enabled "$SERVICE_NAME" 2>/dev/null | grep -q "masked"; then
        echo ">>> 检测到服务被 masked，正在 unmask..."
        sudo systemctl unmask "$SERVICE_NAME"
    fi

    # 用实际路径替换模板中的占位内容
    sed \
        -e "s|User=ubuntu|User=$USER|" \
        -e "s|WorkingDirectory=.*|WorkingDirectory=$PROJECT_DIR|" \
        -e "s|ExecStart=.*|ExecStart=$VENV_DIR/bin/gunicorn -c gunicorn.conf.py gua_app:app|" \
        "$SERVICE_FILE" | sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null

    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME"
    sudo systemctl start "$SERVICE_NAME"

    echo ""
    echo "===== 安装完成 ====="
    echo "服务状态:"
    sudo systemctl status "$SERVICE_NAME" --no-pager
    echo ""
    echo "日常部署只需运行: bash deploy.sh"
    exit 0
fi

# ---------- 日常部署 ----------
echo "===== 零停机部署 ====="

# 1. 备份数据库（保留最近 10 份）
BACKUP_DIR="$PROJECT_DIR/backups"
mkdir -p "$BACKUP_DIR"
if [ -f "$PROJECT_DIR/users.db" ]; then
    BACKUP_FILE="$BACKUP_DIR/users.db.$(date +%Y%m%d_%H%M%S)"
    cp "$PROJECT_DIR/users.db" "$BACKUP_FILE"
    echo ">>> 数据库已备份: $BACKUP_FILE"
    # 只保留最近 10 份备份
    ls -t "$BACKUP_DIR"/users.db.* 2>/dev/null | tail -n +11 | xargs -r rm
fi

# 2. 安装/更新依赖（如有变化）
echo ">>> 更新 Python 依赖..."
"$VENV_DIR/bin/pip" install -q -r requirements.txt

# 2. 构建前端
echo ">>> 构建前端..."
cd "$PROJECT_DIR/frontend"
npm run build
cd "$PROJECT_DIR"

# 3. 平滑重启（Gunicorn 收到 HUP 信号后，会用新代码启动新 worker，
#    等旧 worker 处理完当前请求后退出，实现零停机）
echo ">>> 平滑重启服务..."
sudo systemctl reload "$SERVICE_NAME"

echo ""
echo "===== 部署完成（零停机）====="
sudo systemctl status "$SERVICE_NAME" --no-pager -l
