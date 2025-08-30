# 全局代码规范（Coding Rules）

> 适用于本项目的后端（Python）、前端（Streamlit）、MCP 接入与 LLM 适配。作为约束与参考，后续如有冲突以 PRD 与合规要求为准。

## 1. 原则
- 简单优先：先满足 MVP，避免过度工程化；
- 清晰边界：签名/鉴权、数据模型、业务逻辑、UI 分层清晰；
- 合规安全：严格遵守 Amazon PA-API 与 LLM 的使用条款，不记录敏感信息；
- 可观测性：关键路径具备最小可观测（日志 + trace_id + 计时）。

## 2. Python 后端
- 版本与风格：
  - Python 3.10+；全量类型标注；函数/变量使用 snake_case，类名使用 CapWords；
  - 文档注释采用 Google/NumPy 任一一致风格；
  - 行宽建议 100，尽量保持纯函数与无副作用模块。
- 依赖：
  - HTTP 客户端优先 `httpx`（同步/异步二选一，MVP 同步）；
  - 数据处理 `pandas`（仅在分析层），避免在请求层引入沉重依赖；
  - 数据模型使用 `pydantic`（V1/V2 均可，保持统一）。
- 配置：
  - 所有密钥/主机/区域通过环境变量注入（见 `.env.example` 与 docs/PAAPI_KEYS.md）；
  - 提供集中配置模块（如 `backend/config.py`）读取并校验必要项。

## 3. PA-API（官方）集成
- 签名：
  - 实现 AWS SigV4 封装（单一模块，如 `backend/paapi/signing.py`），禁止散落在业务代码；
  - 每次请求显式设置超时（连接 ≤ 2s，总超时 ≤ 8s）。
- 请求与重试：
  - 遇到 429/5xx 使用指数退避（100ms–2s，含抖动，最多 3 次）；
  - 严格尊重速率限制，不并发淹没；
  - 必要字段校验失败直接在业务层返回可读错误。
- 数据映射：
  - 将 PA-API 响应映射至统一模型（见“数据模型”）；
  - 对可选字段做健壮性处理（缺失时为 None/空集合）。

## 4. MCP 使用约定
- 不自研 MCP Server：
  - 通用 HTTP/OpenAPI MCP 仅用于非签名型辅助端点；
  - 对 PA-API 这类签名端点，直接由后端调用（MCP 不中转）。
- 工具命名：
  - 统一小写-短横线，如 `http-get`, `openapi-call`；
  - 入参/出参以 JSON Schema 明确，遵循最小必要字段。

## 5. Streamlit 前端
- 结构：
  - 页面组织为“搜索表单 → 列表 → 详情侧栏 → 图表 → 导出”；
  - 组件 ID 与状态变量命名清晰，避免全局状态污染。
- 性能与缓存：
  - 使用 `st.cache_data` 对纯数据查询做 TTL 缓存（默认 60–300s，可配置）；
  - 大列表分页展示，默认每页 ≤ 24 条。
- UX：
  - 失败与限流使用 `st.warning/error` 明确提示；
  - 价格显示包含货币符号与区域。
- 安全：
  - 前端不持久化任何密钥；下载的 CSV 加来源与时间戳。

## 6. LLM 适配（OpenAI / Gemini / Ollama）
- 适配层：
  - 新建 `backend/llm/client.py`，按 `provider` 路由三类提供商；
  - 统一接口：`generate(messages, system=None, tools=None, **kwargs)`；
- 配置与超时：
  - 不同提供商分别设置超时与重试；默认总超时 ≤ 15s；
  - 模型从环境变量读取，提供合理默认（见 docs/LLM_SETUP.md）。
- 日志与合规：
  - 记录 `provider/model/latency`，禁止记录用户原文与密钥。

## 7. 数据模型
- 统一 Product Schema（pydantic 模型）：
  - `asin: str`
  - `title: str`
  - `brand: Optional[str]`
  - `categories: List[str]`
  - `price: Optional[{ amount: Decimal, currency: str }]`
  - `list_price: Optional[{ amount: Decimal, currency: str }]`
  - `savings: Optional[{ amount: Decimal, currency: str }]`
  - `rating: Optional[float]`（0–5）
  - `total_reviews: Optional[int]`
  - `images: List[str]`
  - `url: HttpUrl`
- 金额类型：
  - 内部计算使用 `Decimal`；输入输出保留原币种与精度；
  - 序列化到前端时保留 `amount` 与 `currency`。

## 8. 错误处理
- 分级：
  - 用户可读：参数错误、鉴权失败、超限、网络不可达；
  - 开发者定位：签名摘要、上游状态码、trace_id；
- 传播：
  - 后端统一异常类型（如 `AppError`，含 `code`, `message`, `detail?`）；
  - 前端对已知错误进行分类提示。

## 9. 测试
- 框架：`pytest`；
- 范围：
  - 单元：签名、解析、数据映射、容错；
  - 集成（可选）：打桩上游响应（VCR/本地 fixture），避免真实网络；
- 规范：
  - 测试不依赖外网与真实密钥；
  - 断言包含关键字段与边界条件。

## 10. 观测与日志
- 记录级别：INFO 业务摘要，DEBUG 仅在本地；
- 结构化：建议 `json` 格式或统一前缀，包含 `trace_id`、`latency_ms`；
- 屏蔽：任何密钥/签名/PII 禁止出现在日志与异常 message 中。

## 11. 性能与速率
- 速率限制：尊重官方配额，串行或有限并发（≤ 2 并发）；
- 退避重试：指数退避 + 抖动，最多 3 次；
- 分页：后端分页与前端分页一致，避免一次性拉取过大数据。

## 12. 文档与示例
- 变更需更新相关文档：
  - PA-API 相关 → `docs/PAAPI_KEYS.md`
  - LLM 相关 → `docs/LLM_SETUP.md`
  - 产品/范围 → `docs/PRD.md`
- 在 README/使用文档中提供最小示例（待创建）。

---
如需调整或新增规范，请在 PR 中更新该文档并简要说明动机与影响范围。
