# 产品需求文档（PRD）— Marketplace Analyzer Agent MVP

> 目标：基于 MCP 的多市场（首期 Amazon）商品查询与分析 Agent，后端 Python，前端 Streamlit。
> 版本：MVP v0.1 | 更新时间：2025-08

## 1. 背景与目标
- 背景：团队希望构建一个“可扩展、合规”的电商数据分析代理，先落地 Amazon 场景，后续扩展其他平台（如 SHEIN）。
- 总体目标：
  - 通过 MCP 统一接入电商数据源；
  - 支持关键词搜索、商品详情检索、基础价格与品牌维度分析；
  - 提供简洁交互界面（Streamlit），满足选品与内容创作的基础需求。

## 2. 用户与场景
- 用户画像：
  - 选品分析人员/运营：希望快速浏览同类产品价格分布、主流品牌、优惠幅度；
  - 内容创作者：需要获取商品基本信息（标题、图片、价格）用于选题对比；
  - 业务/产品：验证市场假设，输出轻量对比报告。
- 典型场景：
  - 输入关键词（如“mechanical keyboard”）→ 列表浏览 → 选中若干 ASIN → 查看详情 → 生成简报。
  - 按价格区间/品牌筛选 → 查看价格分布图、品牌占比饼图 → 导出 CSV。

## 3. MVP 范围（V0.1）
- 数据源与合规（官方优先）：
  - 使用 Amazon Product Advertising API v5（PA-API，官方）实现关键词搜索与 ASIN 详情；
  - 不进行页面抓取；严格遵守 Amazon Associates 与 PA-API 使用规范；
  - 区域：先支持 `US`，为多区域预留参数；
  - 说明：PA-API 需 AWS SigV4 签名，签名在后端完成（通用 HTTP MCP 不做签名）。
- 功能清单：
  1) 商品搜索：关键词 + 可选过滤（价格区间、排序、页码）。
  2) 商品详情：标题、品牌、图片、类目、当前价格/优惠、跳转链接（基于第三方返回）。
  3) 基础分析：
     - 价格分布直方图（按搜索结果）
     - 品牌出现频次 Top N（如返回中含 brand 字段）
     - 平均/中位数价格，含货币标注
  4) 列表/分析导出：CSV（UTF-8）。
  5) 速率与异常：节流、重试、限流提示、失败可重试。
- 非目标（MVP 不做）：
  - 评论正文抓取、情感分析；
  - SHEIN/其他平台（v0.2+ 依据合规与成本评估后接入）。

## 4. 指标（MVP）
- 体验：
  - 首屏可用 ≤ 2s（不含首次鉴权与冷启动）；
  - 搜索到首批列表 ≤ 3–5s（受 API 速率与网络影响）。
- 功能：
  - 搜索命中率：99% 请求返回结构化结果或明确错误；
  - 导出文件可在 Excel/Sheets 正常打开。
- 稳定性：
  - 出错可观测（日志含 trace_id）；
  - 速率限制触发有重试与退避。

## 5. 系统设计（MVP）
 - 前端（Streamlit）：
  - 视图：搜索面板、列表、详情抽屉/侧栏、图表区、导出按钮。
  - 图表：Altair/Plotly（价格分布、品牌占比）。
 - 后端（Python）：
  - MCP Client Orchestrator：使用 `mcp` SDK；
  - PA-API 访问：在后端完成 SigV4 签名并直连官方端点；
  - 可选 MCP 工具：保留通用 HTTP/OpenAPI MCP 用于非签名型辅助端点（如汇率等）；
  - 业务服务：统一参数校验、分页与缓存（如 `sqlite + TTL`）；
  - 配置：见 `.env.example` 与 `docs/PAAPI_KEYS.md`；
  - 错误处理：对速率限制与鉴权失败给出可读提示。
 - LLM 支持（可选增强）：
  - 适配 OpenAI / Gemini / Ollama，用于自然语言查询解析与结果总结；
  - 环境变量：`OPENAI_API_KEY`、`GEMINI_API_KEY`、`OLLAMA_HOST` 等。

## 6. 接口契约（简要）
 - MCP Tool 输入输出（统一 Schema，第三方字段做适配）：
  - 输入：
    - `query` string（可空于详情接口）、`locale` enum（`US|UK|DE|...`）、`category?` string、`min_price?` number、`max_price?` number、`sort?` enum（`relevance|price_asc|price_desc|newest`）、`page?` int
  - 输出：
    - `products[]`：`{ asin, title, brand?, category[], price{amount,currency}?, listPrice?, savings?, rating?, totalReviews?, images[], url }`
    - `paging`：`{ page, pageSize, total? }`

## 7. 安全与合规
- 使用官方 PA-API，遵守 Amazon Associates 与 PA-API 使用限制；
- 不长期缓存、不过度再分发，展示中注明来源（如“数据来源：Amazon PA-API”）；
- 秘钥通过环境变量注入，生产禁日志输出敏感字段；
- 对请求频率、错误码与退避策略进行治理。

## 8. 风险与应对
- 速率限制/配额不足 → 队列+退避重试、分页请求、结果缓存；
- 字段缺失/区域差异 → 做可选字段容错（如 `brand?`）；
- UI 性能瓶颈 → 延迟加载图表、限制首屏数量（如 24 条/页）。

## 9. 里程碑
- W1：
  - 完成 PA-API 签名与最小调用（SearchItems/GetItems）；
  - Streamlit 基础页面（搜索/列表/详情/图表）。
- W2：
  - 加入缓存与导出；完善异常与速率治理；
  - 小范围试用与反馈修正。
- W3（v0.2 可选）：
  - 扩展更多分析（如 BrowseNodes），以及引入 LLM 洞察模板。

## 10. 开发任务清单（MVP）
- 后端 Orchestrator：
  - [ ] 实现 PA-API SigV4 签名与 SearchItems/GetItems 调用；
  - [ ] 统一数据模型与缓存；
- MCP（可选，零自研）：
  - [ ] 配置通用 HTTP/OpenAPI MCP 供辅助工具使用（非签名端点）；
- 前端（Streamlit）：
  - [ ] 搜索表单与结果表；
  - [ ] 详情侧栏与图片展示；
  - [ ] 价格分布与品牌占比图表；
  - [ ] CSV 导出；
- 其他：
  - [ ] 环境配置与示例 `.env.example`（PA-API 与 LLM）；
  - [ ] 基础单元测试（签名/解析/容错）。

## 11. 目录结构建议
```
.
├─ docs/
│  ├─ RESEARCH_MCP.md
│  └─ PRD.md
├─ configs/
│  ├─ mcp-http.yaml       # （可选）通用 MCP 工具配置（仅非签名端点）
│  └─ openapi/            # （可选）OpenAPI 规范
├─ backend/
│  ├─ orchestrator.py     # MCP 客户端与业务封装
│  └─ models.py           # 统一数据模型
├─ app/
│  └─ streamlit_app.py
├─ tests/
│  └─ test_parsing.py     # 第三方响应解析/容错
└─ .env.example
```
