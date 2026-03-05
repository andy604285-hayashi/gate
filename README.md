# Gate.io 下架公告监控工具

一个可长期运行的 Python 监控程序：扫描 Gate.io 公告中的「下架/delist」信息，解析涉及币种，匹配你的持仓/自选列表，并通过 Telegram 发送告警。

## 项目结构

- `main.py`：主循环（定时扫描与调度）
- `scanner.py`：公告抓取与去重
- `parser.py`：公告正文币种解析
- `matcher.py`：持仓读取与匹配
- `notifier.py`：消息构造与 Telegram 发送
- `config.py`：配置项（从环境变量读取）
- `history.json`：已处理公告 ID
- `watchlist.json`：手动维护自选币种

## 快速开始

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 配置环境变量：
   - `GATE_API_KEY` / `GATE_API_SECRET`（可选，不填则仅使用 `watchlist.json`）
   - `TG_BOT_TOKEN` / `TG_CHAT_ID`（可选，不填则只在控制台输出）
3. 运行：
   ```bash
   python main.py
   ```

## 备注

- 默认每 120 秒扫描一次（可用 `POLL_INTERVAL_SECONDS` 调整）。
- 若 Gate 页面结构变化，需要更新 `scanner.py` 选择器。
- 建议先用 `watchlist.json` 验证流程，再接入 API Key。


## 阶段推进记录

- 阶段1（数据源调研）报告：`docs/PHASE_1_RESEARCH.md`
- 调研探测脚本：`python tools/source_probe.py`

- 阶段2（扫描模块实现）记录：`docs/PHASE_2_SCANNER.md`

- 阶段3（解析模块实现）记录：`docs/PHASE_3_PARSER.md`

- 阶段4（持仓匹配实现）记录：`docs/PHASE_4_MATCHER.md`

- 阶段5（通知模块实现）记录：`docs/PHASE_5_NOTIFIER.md`

- 阶段6（主程序整合）记录：`docs/PHASE_6_MAIN.md`

- 阶段7（测试与调试）记录：`docs/PHASE_7_TESTING.md`

- 阶段8（部署与运行）记录：`docs/PHASE_8_DEPLOYMENT.md`

## 部署资产

- systemd 服务模板：`deploy/gate-delist-monitor.service`
- crontab 示例：`deploy/crontab.example`
- 单轮执行脚本：`scripts/run_once.sh`
