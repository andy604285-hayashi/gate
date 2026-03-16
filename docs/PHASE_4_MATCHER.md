# 阶段 4：持仓/自选获取模块实现记录

> 对应原始规划中的「阶段 4：实现持仓/自选获取模块 matcher.py」。

## 本阶段目标

- 并行支持两种持仓来源：
  - A：Gate API 自动获取
  - B：本地 `watchlist.json` 手动维护
- 当 API 不可用时，确保系统仍可用（自动降级到 watchlist）。

## 已实现内容

1. 增加凭证配置校验：仅配置 key 或 secret 之一会给出明确配置错误告警。
2. API/网络异常分级处理：
   - 配置错误（`GateAuthConfigError`）
   - 请求错误（`requests.RequestException`）
   两种情况均会降级为 watchlist-only。
3. 增强可观测性日志：输出 API / watchlist / merged 的数量统计。
4. 增加 matcher 核心测试：fallback、watchlist 异常 JSON、交集匹配逻辑。

## 下一步（阶段 5）

- 继续通知模块（Telegram 主通道）增强：
  - 重试与失败可观测性
  - 通知模板结构化
  - 可选备用通知通道
