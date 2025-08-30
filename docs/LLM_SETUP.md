# LLM 提供商支持（OpenAI / Gemini / Ollama）

> 目标：为自然语言查询解析与结果总结提供可插拔的 LLM 支持。本文说明三类提供商的最小配置与建议。

## 1. OpenAI
- 环境变量：
  - `OPENAI_API_KEY`（必填）
  - `OPENAI_BASE_URL`（可选，走代理或兼容 OpenAI 协议的网关时使用）
  - `OPENAI_MODEL`（可选，默认可用 `gpt-4o-mini` 或你偏好的模型）
- 建议：
  - 控制温度与最大输出，保证可复现性；
  - 对外网敏感环境可考虑私有代理。

## 2. Google Gemini
- 环境变量：
  - `GEMINI_API_KEY`（或 `GOOGLE_API_KEY`，依据所用 SDK）
  - `GEMINI_MODEL`（可选，如 `gemini-1.5-flash`）
- 建议：
  - 遵循数据政策，避免上传敏感信息；
  - 关注每分钟配额与区域可用性。

## 3. Ollama（本地推理）
- 环境变量：
  - `OLLAMA_HOST`（如 `http://localhost:11434`）
  - `OLLAMA_MODEL`（如 `llama3.1:8b`）
- 使用方式：
  - 需本机或服务器安装并拉取模型：`ollama pull llama3.1:8b`；
  - 适合离线/本地数据不出域的场景。

## 4. 代码对接建议
- 设计一个 `LLMClient` 适配层，按 `provider` 路由：`openai | gemini | ollama`；
- 输入输出：统一 `messages`/`system`/`tools?` 接口，便于切换；
- 超时与重试：各自独立设置，并在 UI 报告来源与耗时；
- 日志：记录 `provider/model/latency/tokens?`，避免记录敏感内容。

## 5. 最小验证
- 配置至少一个提供商的 API Key；
- 在应用中执行一次“解释搜索结果”的试运行，确认响应可达；
- 若响应失败，优先检查：网络连通、Key 权限、区域/配额、代理设置。
