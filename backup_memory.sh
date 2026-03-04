#!/bin/bash
# backup_memory.sh - 记忆备份脚本
# 用法: ./backup_memory.sh

set -e

# 配置
WORKSPACE_DIR="$HOME/.openclaw/workspace"
BACKUP_DIR="$HOME/Desktop/OpenClaw_备份"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="openclaw_backup_${DATE}"

echo "🔄 开始备份 OpenClaw 记忆..."

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 进入工作目录
cd "$WORKSPACE_DIR"

# 先提交最新的更改
git add -A 2>/dev/null || true
git commit -m "自动备份: $DATE" 2>/dev/null || true

# 创建压缩包
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='node_modules' \
    --exclude='.venv' \
    -C "$HOME/.openclaw" \
    workspace/

# 同时备份关键文件到单独目录
KEY_BACKUP_DIR="${BACKUP_DIR}/${BACKUP_NAME}"
mkdir -p "$KEY_BACKUP_DIR"

# 复制核心记忆文件
cp MEMORY.md "$KEY_BACKUP_DIR/" 2>/dev/null || true
cp -r memory/ "$KEY_BACKUP_DIR/" 2>/dev/null || true
cp *.md "$KEY_BACKUP_DIR/" 2>/dev/null || true

# 创建恢复说明
cat > "${KEY_BACKUP_DIR}/如何恢复.txt" << 'EOF'
恢复方法:
==========

如果你需要恢复这个备份:

1. 找到你的 OpenClaw workspace 目录:
   ~/.openclaw/workspace

2. 复制这些文件回去:
   - MEMORY.md → 长期记忆
   - memory/ → 每日记忆
   - *.md → 配置文件

3. 或者直接用压缩包覆盖:
   tar -xzf openclaw_backup_XXXXXX.tar.gz -C ~/.openclaw/

4. 重启 OpenClaw

记忆就回来了。
EOF

echo "✅ 备份完成!"
echo "📦 完整备份: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
echo "📁 关键文件: ${KEY_BACKUP_DIR}/"
echo ""
echo "💡 建议: 把这个备份文件复制到:"
echo "   - iCloud Drive"
echo "   - 百度网盘"
echo "   - U盘"
echo ""
echo "这样即使 Mac mini 坏了,你的记忆也不会丢。"
