# 早盘异动监控系统

## 📋 功能说明

监控系统在 A股早盘时段（9:30-10:00）运行，每5分钟扫描自选股，发现异动立即推送飞书通知。

## 🎯 监控条件

| 条件 | 阈值 | 说明 |
|------|------|------|
| 涨幅 | ≥ 2% | 快速拉升 |
| 量比 | ≥ 1.5 | 成交量放大 |
| 成交额 | ≥ 1亿 | 确保流动性 |

## 📁 文件结构

```
~/.openclaw/workspace/strategies/
├── morning_monitor.py           # 主监控脚本
├── morning_monitor_notify.py    # 单次检查+飞书推送
├── monitor_control.sh           # 控制脚本
└── README_morning_monitor.md    # 本文档
```

## 🚀 使用方法

### 1. 手动运行（测试）

```bash
# 运行一次测试（非交易时段也能运行）
python3 ~/.openclaw/workspace/strategies/morning_monitor.py

# 运行并推送飞书
python3 ~/.openclaw/workspace/strategies/morning_monitor_notify.py
```

### 2. 使用控制脚本

```bash
cd ~/.openclaw/workspace/strategies

# 启动监控
./monitor_control.sh start

# 查看状态
./monitor_control.sh status

# 查看日志
./monitor_control.sh log

# 停止监控
./monitor_control.sh stop

# 重启监控
./monitor_control.sh restart
```

### 3. 定时任务（推荐）

每天 9:28 自动启动监控：

```bash
# 编辑 crontab
crontab -e

# 添加以下行
28 9 * * 1-5 /Users/opensamhot/.openclaw/workspace/strategies/monitor_control.sh start

# 查看 crontab
crontab -l
```

## ⚙️ 配置修改

### 修改自选股

编辑 `morning_monitor.py`，修改 `WATCHLIST`：

```python
WATCHLIST = [
    {"code": "000001", "name": "平安银行", "market": "sz"},
    {"code": "600519", "name": "贵州茅台", "market": "sh"},
    {"code": "600362", "name": "江西铜业", "market": "sh"},
    # 添加你的股票
]
```

### 修改监控阈值

```python
THRESHOLDS = {
    "price_change_pct": 2.0,  # 涨幅阈值（%）
    "volume_ratio": 1.5,      # 量比阈值
    "turnover_min": 1.0,      # 最小成交额（亿）
}
```

### 修改监控时段

```python
MONITOR_START = time(9, 30)   # 开始时间
MONITOR_END = time(10, 0)     # 结束时间
CHECK_INTERVAL = 300          # 检查间隔（秒）
```

## 📱 飞书通知

发现异动时，飞书会收到类似消息：

```
🚀 早盘异动提醒 (09:45)

**江西铜业 (600362)**
  价格: ¥12.85 🔴 +3.2%
  成交: 5.6亿
  信号: 涨3.2%, 成交5.6亿
  时间: 09:45:23

💡 建议: 关注资金是否配合，确认突破有效性
```

## 📊 日志文件

```
~/.openclaw/workspace/data/
├── morning_monitor.log          # 监控日志
├── alert_093015.txt             # 异动记录
└── ...
```

## 🔧 故障排查

### 监控没有启动

```bash
# 检查 PID 文件
ls -la ~/.openclaw/workspace/data/morning_monitor.pid

# 手动启动查看错误
python3 ~/.openclaw/workspace/strategies/morning_monitor.py
```

### 收不到飞书通知

1. 检查 OpenClaw 飞书配置
2. 查看日志中的错误信息
3. 检查网络连接

### 数据获取失败

- 检查网络连接
- 新浪财经接口可能有频率限制
- 等待几分钟后重试

## 📝 更新计划

- [ ] 接入 Tushare Pro 资金流向数据
- [ ] 增加均线突破检测
- [ ] 增加板块联动检测
- [ ] 增加个股买卖建议

## ⚠️ 免责声明

本系统仅供学习研究使用，不构成投资建议。股市有风险，投资需谨慎。

---

*创建时间: 2026-02-25*
*版本: v1.0*
