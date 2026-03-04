#!/bin/bash
# 早盘监控控制脚本

WORKSPACE="$HOME/.openclaw/workspace"
STRATEGIES_DIR="$WORKSPACE/strategies"
PID_FILE="$WORKSPACE/data/morning_monitor.pid"
LOG_FILE="$WORKSPACE/data/morning_monitor.log"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 python3"
    exit 1
fi

start() {
    echo "🚀 启动早盘监控..."
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "⚠️ 监控已在运行 (PID: $PID)"
            return 1
        fi
    fi
    
    # 启动监控（后台运行）
    nohup python3 "$STRATEGIES_DIR/morning_monitor.py" >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    
    echo "✅ 监控已启动 (PID: $!)"
    echo "日志: $LOG_FILE"
}

stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            kill "$PID"
            echo "✅ 监控已停止"
        else
            echo "⚠️ 监控未运行"
        fi
        rm -f "$PID_FILE"
    else
        echo "⚠️ 未找到 PID 文件"
    fi
}

status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "✅ 监控运行中 (PID: $PID)"
            echo "日志: $LOG_FILE"
        else
            echo "⚠️ 监控未运行（PID 文件存在但进程不存在）"
            rm -f "$PID_FILE"
        fi
    else
        echo "⚠️ 监控未运行"
    fi
}

log() {
    if [ -f "$LOG_FILE" ]; then
        echo "📝 最近 50 行日志:"
        tail -n 50 "$LOG_FILE"
    else
        echo "⚠️ 日志文件不存在"
    fi
}

# 主逻辑
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 1
        start
        ;;
    status)
        status
        ;;
    log)
        log
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|log}"
        echo ""
        echo "命令:"
        echo "  start   - 启动早盘监控"
        echo "  stop    - 停止监控"
        echo "  restart - 重启监控"
        echo "  status  - 查看状态"
        echo "  log     - 查看日志"
        exit 1
        ;;
esac
