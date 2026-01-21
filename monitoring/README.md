# 心守AI 监控系统

本目录包含完整的可观测性（Observability）配置，包括指标收集、日志聚合、告警和可视化。

## 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                     Observability Stack                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Metrics    │  │    Logs      │  │   Alerts     │          │
│  │  Prometheus  │  │    Loki      │  │ Alertmanager │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           │                                      │
│                    ┌──────▼──────┐                              │
│                    │   Grafana   │                              │
│                    │  Dashboard  │                              │
│                    └─────────────┘                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 启动监控栈

```bash
# 从项目根目录运行
docker-compose -f docker-compose.yml -f monitoring/docker-compose.monitoring.yml up -d
```

### 2. 访问服务

| 服务 | URL | 默认凭据 |
|------|-----|----------|
| Grafana | http://localhost:3001 | admin / xinshoucai123 |
| Prometheus | http://localhost:9090 | - |
| Alertmanager | http://localhost:9093 | - |
| Loki | http://localhost:3100 | - |

### 3. 验证

```bash
# 检查所有服务状态
docker-compose -f docker-compose.yml -f monitoring/docker-compose.monitoring.yml ps

# 验证 Prometheus 目标
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[].health'

# 验证后端指标端点
curl http://localhost:8000/metrics
```

## 目录结构

```
monitoring/
├── prometheus/
│   ├── prometheus.yml          # Prometheus 主配置
│   └── alerts/
│       └── xinshoucai.yml      # 告警规则
│
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/        # 数据源配置
│   │   └── dashboards/         # Dashboard 配置
│   └── dashboards/
│       └── xinshoucai-overview.json  # 主 Dashboard
│
├── alertmanager/
│   └── alertmanager.yml        # 告警路由配置
│
├── loki/
│   └── loki-config.yml         # Loki 日志聚合配置
│
├── promtail/
│   └── promtail-config.yml     # 日志采集器配置
│
├── docker-compose.monitoring.yml  # 监控栈 Docker 配置
└── README.md                      # 本文件
```

## 指标说明

### HTTP 请求指标

| 指标名 | 类型 | 描述 |
|--------|------|------|
| `xinshoucai_http_requests_total` | Counter | HTTP 请求总数 |
| `xinshoucai_http_request_duration_seconds` | Histogram | 请求延迟分布 |
| `xinshoucai_http_requests_in_progress` | Gauge | 当前进行中的请求数 |

### AI 引擎指标

| 指标名 | 类型 | 描述 |
|--------|------|------|
| `xinshoucai_ai_requests_total` | Counter | AI API 请求总数 |
| `xinshoucai_ai_request_duration_seconds` | Histogram | AI 请求延迟 |
| `xinshoucai_ai_tokens_total` | Counter | AI token 使用量 |

### 风险检测指标

| 指标名 | 类型 | 描述 |
|--------|------|------|
| `xinshoucai_risk_events_total` | Counter | 检测到的风险事件 |
| `xinshoucai_risk_events_unreviewed` | Gauge | 未审查的风险事件数 |

### 业务指标

| 指标名 | 类型 | 描述 |
|--------|------|------|
| `xinshoucai_checkins_total` | Counter | 每日检查提交数 |
| `xinshoucai_assessments_total` | Counter | 评估完成数 |
| `xinshoucai_average_mood_score` | Gauge | 平均情绪分数 |
| `xinshoucai_websocket_connections` | Gauge | WebSocket 连接数 |

### 数据库指标

| 指标名 | 类型 | 描述 |
|--------|------|------|
| `xinshoucai_db_pool_size` | Gauge | 连接池大小 |
| `xinshoucai_db_pool_checked_out` | Gauge | 已使用连接数 |
| `xinshoucai_db_query_duration_seconds` | Histogram | 查询延迟 |

## 告警规则

### 严重级别

| 级别 | 响应时间 | 通知渠道 |
|------|----------|----------|
| **critical** | 立即 | 邮件 + Slack + 电话 |
| **warning** | 5分钟 | 邮件 + Slack |
| **info** | 24小时 | 邮件 |

### 关键告警

| 告警名 | 条件 | 说明 |
|--------|------|------|
| `CriticalRiskEventDetected` | 检测到 CRITICAL 级别风险 | 需要临床团队立即关注 |
| `HighErrorRate` | 5xx 错误率 > 1% | API 服务异常 |
| `HighLatency` | P95 延迟 > 1s | 性能下降 |
| `ServiceDown` | 服务不可达 | 服务宕机 |
| `DatabaseConnectionPoolCritical` | 连接池使用率 > 95% | 数据库连接耗尽 |

## Grafana Dashboard

预配置的 Dashboard 包含以下面板：

### Overview Row
- 请求速率 (RPS)
- 错误率 (%)
- P95 延迟 (秒)
- WebSocket 连接数
- 未审查风险事件
- 平均情绪分数

### Request Metrics Row
- 按端点划分的请求速率
- 请求延迟百分位数 (P50, P90, P95, P99)

### AI Engine Row
- 按引擎类型的 AI 请求
- AI 请求延迟 (P95)
- AI Token 使用量

### Risk & Clinical Row
- 按级别的风险事件
- 临床活动 (检查 + 评估)
- 按类型的评估分布

### Infrastructure Row
- 数据库连接池使用率
- 数据库查询延迟
- 按类型的错误分布

## 日志系统

### 结构化日志格式 (JSON)

```json
{
  "timestamp": "2025-01-20T12:34:56.789Z",
  "level": "INFO",
  "logger": "app.api.chat",
  "message": "AI chat response generated",
  "request_id": "abc-123-def",
  "user_id": 42,
  "data": {
    "duration_ms": 1234.56,
    "tokens_used": 500
  }
}
```

### 日志级别

| 级别 | 用途 |
|------|------|
| DEBUG | 开发调试信息 |
| INFO | 正常操作日志 |
| WARNING | 潜在问题警告 |
| ERROR | 错误和异常 |
| CRITICAL | 严重系统问题 |

### 审计日志

敏感操作自动记录到审计日志：

- 用户登录/登出
- 数据访问 (GDPR)
- 风险事件检测
- 数据导出请求

## 生产环境配置

### 1. 修改默认密码

```bash
# Grafana
GF_SECURITY_ADMIN_PASSWORD=<strong-password>

# Alertmanager SMTP
smtp_auth_password: <smtp-password>
```

### 2. 配置告警接收者

编辑 `alertmanager/alertmanager.yml`:

```yaml
receivers:
  - name: 'critical-receiver'
    email_configs:
      - to: 'your-oncall@company.com'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/xxx'
        channel: '#alerts'
```

### 3. 调整数据保留期

```yaml
# Prometheus (prometheus.yml)
--storage.tsdb.retention.time=30d

# Loki (loki-config.yml)
table_manager:
  retention_period: 720h  # 30 days
```

### 4. 启用 HTTPS

建议在生产环境使用反向代理 (Nginx/Traefik) 提供 HTTPS。

## 故障排查

### 常见问题

**Prometheus 无法抓取目标**

```bash
# 检查目标状态
curl http://localhost:9090/api/v1/targets

# 验证后端 metrics 端点
curl http://localhost:8000/metrics
```

**Grafana 无数据**

1. 检查 Prometheus 数据源配置
2. 验证时间范围
3. 检查 PromQL 查询

**告警未发送**

```bash
# 检查 Alertmanager 状态
curl http://localhost:9093/api/v1/status

# 检查静默规则
curl http://localhost:9093/api/v1/silences
```

## 扩展

### 添加自定义指标

```python
from app.utils.monitoring import (
    REGISTRY,
    Counter,
)

# 创建自定义计数器
MY_METRIC = Counter(
    "xinshoucai_my_metric_total",
    "Description",
    ["label1", "label2"],
    registry=REGISTRY,
)

# 使用
MY_METRIC.labels(label1="value1", label2="value2").inc()
```

### 添加自定义 Dashboard

1. 在 Grafana UI 创建 Dashboard
2. 导出 JSON
3. 保存到 `grafana/dashboards/` 目录
4. 重启 Grafana

## 参考链接

- [Prometheus 文档](https://prometheus.io/docs/)
- [Grafana 文档](https://grafana.com/docs/)
- [Loki 文档](https://grafana.com/docs/loki/latest/)
- [Alertmanager 文档](https://prometheus.io/docs/alerting/latest/alertmanager/)
