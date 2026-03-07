# 阶段 8：部署与长期运行实现记录

> 对应原始规划中的「阶段 8：部署与长期运行」。

## 本阶段目标

- 提供本地与云端两种可执行的长期运行方案。
- 提供最小可用运维资产，降低上线门槛。

## 已实现内容

1. 新增 `deploy/gate-delist-monitor.service`（systemd 服务模板）：
   - 开机自启
   - 异常自动重启
   - 支持 `.env` 文件注入密钥
2. 新增 `deploy/crontab.example`（本地定时任务示例）：
   - 每 2 分钟执行一次 `--once` 单轮检查
3. 新增 `scripts/run_once.sh`：
   - 可选自动激活 `.venv`
   - 执行 `python main.py --once`
4. 形成阶段文档，说明部署路径与运行方式。

## 推荐部署路径

### 方案 A：本地电脑（简易）

- 使用 `crontab` + `scripts/run_once.sh`
- 适合电脑长期开机用户

### 方案 B：云服务器（推荐）

- 使用 `systemd` 服务
- 适合 7x24 持续运行

## systemd 快速步骤（示例）

1. 拷贝项目到 `/opt/gate_delist_monitor`
2. 创建虚拟环境并安装依赖
3. 编辑 `.env`（填写 `TG_BOT_TOKEN` / `TG_CHAT_ID` / 可选 API key）
4. 安装服务文件：
   - `sudo cp deploy/gate-delist-monitor.service /etc/systemd/system/`
   - `sudo systemctl daemon-reload`
   - `sudo systemctl enable --now gate-delist-monitor`
5. 查看日志：
   - `journalctl -u gate-delist-monitor -f`

## 验证建议

- 先执行一次：`python main.py --once --log-level DEBUG`
- 再观察 24 小时日志中的重启次数与告警行为


## 预检查工具

- 执行：`python tools/preflight_check.py`
- 用途：检查关键文件存在性、history 可写性、TG/API 环境变量是否配置。

- JSON 预检查（自动化场景）：`python main.py --preflight --preflight-json`
