# MCP 与电商平台（Amazon / SHEIN）调研摘要

> 更新时间：2025-08 | 参考知识截止：2024-10

## 1. MCP 概述
- 定义：MCP（Model Context Protocol）是用于“工具/数据源接入”的开放协议，像 LSP 之于编辑器一样，为 AI 代理稳定对接“工具（tools）、资源（resources）、提示（prompts）和事件（events）”。
- 角色：
  - MCP Server：对接实际数据源/能力（如数据库、Web API、文件系统等），对外暴露结构化的“工具”。
  - MCP Client：AI 代理/应用侧，用统一协议调用多个 Server 的工具。
- 生态：官方与社区已提供多种通用服务器（如 filesystem、http、postgres、github、google drive、slack 等）。目前未发现“官方 Amazon 或 SHEIN 专用 MCP Server”。可通过自建 MCP Server 封装对应平台 API/服务。
- SDK：
  - Python：`mcp`（Anthropic 官方/社区维护），易于在后端集成。
  - Node.js：`@modelcontextprotocol/sdk`。

## 2. 与 Amazon 相关的数据源与API
- Amazon Product Advertising API v5（PA-API）
  - 适用：面向联盟推广/内容站查询商品、价格、图片、要点信息。
  - 能力：关键词搜索、BrowseNode 分类、ASIN 详情、图片、品牌、要点、当前价格/优惠等。
  - 不提供：完整评论内容、评论文本抓取；历史价格曲线（需第三方如 Keepa）。
  - 前提：需加入 Amazon Associates 并通过审核；各区域有独立凭证与速率限制（常见约 1 rps 起，实际随账号与转化而变）。
  - 合规：严禁将数据用于缓存超出协议、再分发、或违反品牌使用规范的用途。

- Amazon Selling Partner API（SP-API）
  - 适用：卖家运营（库存、订单、定价、广告等）。
  - 能力：丰富但与“公开商品搜索/评论分析”目标不完全重合；集成门槛高（开发者注册、角色授权、RDT 限制数据、合规审计）。
  - 推荐：仅在你是卖家且确有卖家侧分析需求时考虑。

- 评论与评分
  - 官方 API 不提供评论正文抓取能力；星级/评论聚合指标有限或需依托页面组件。
  - 任何“直接抓取”Amazon 页面内容都可能违反 ToS（需谨慎评估法律与风控）。

- 第三方数据服务（可选）
  - Keepa API：付费，提供历史价格、折扣跟踪、Buy Box、部分评论统计等；非常适合价格分析/历史曲线。
  - Rainforest API / SerpApi（Amazon 端点）/ Apify Crawler：将页面抓取能力 API 化，合规性需自行评估与约束。

## 3. 与 SHEIN 相关的数据源
- 官方 API：无公开、稳定的官方开放 API。
- 现状：站点强反爬与风控，直接抓取风险较大；多数第三方“API”实为包装抓取，存在合规与稳定性问题。
- 替代：搜索价格与热度类基础数据可通过第三方聚合 API（如 RapidAPI 生态中的非官方端点），但需评估：
  - 法务合规与使用条款
  - 成本与速率
  - 数据质量与可用性

## 4. 合规与风控要点
- 明确数据来源与权限边界：优先使用官方授权 API（PA-API、SP-API），避免未经许可的抓取。
- 缓存与存储：遵循各 API 的缓存、展示规范；对用户侧导出需加水印或来源标注。
- 安全：密钥管理（环境变量/密钥管理器）、最小权限、速率限制、重试与熔断、请求签名。
- 法务：展示 Amazon 品牌元素时遵守合作条款；对于 SHEIN，避免直接抓取造成法律风险。

## 5. 面向本项目的 MCP 设计建议
- 自研 MCP Server（Python）：
  - `mcp-amazon-paapi`：封装 PA-API v5，工具示例：
    - `search_products(query, locale, category, min_price, max_price, sort, page)`
    - `get_product_details(asin, locale)`
    - `get_offers(asin, locale)`
    - 可选：`get_browse_nodes(node_id, locale)`
  - `mcp-keepa`（可选）：封装 Keepa，工具示例：
    - `get_price_history(asin, domain)`
    - `get_deals(domain, min_drop_pct)`
  - `mcp-shein-aggregator`（二期可选）：封装第三方聚合 API（需评估 ToS）。

- 输出数据模式（建议统一 Schema）：
  - Product: `{ asin, title, brand, images[], category[], price{amount,currency}, listPrice?, savings?, rating?, totalReviews?, url }`
  - Offer: `{ sellerName, price{...}, condition, prime, deliveryInfo }`
  - PriceHistory（Keepa）: `{ timestamps[], prices[] }`

## 6. 架构选型建议
- 前端：Streamlit（交互面板、表格、图表、筛选）；
- 后端：Python（FastAPI 可选）+ MCP Client（`mcp` SDK）作为“Orchestrator Agent”，调度多个 MCP Server；
- 鉴权：服务端持有 API Key，通过安全配置注入服务器；
- 缓存：`sqlite + TTL` 或 `redis`；
- 观测：基础日志、请求追踪（trace_id）、速率指标；
- 分析：Pandas + Altair/Plotly 生成价格分布、品牌占比等图表；
- LLM（可选）：用于自然语言查询解析与洞察生成（将自然语言转为 MCP 工具参数，或对结果做总结）。

## 7. 结论与路线
- MVP：仅接入 Amazon PA-API；不支持评论正文与 SHEIN；提供搜索、详情、基础价格分析、列表导出（CSV）。
- 增强：接入 Keepa 拓展历史价格与折扣洞察；
- 二期：评估合法第三方端点后，再扩展 SHEIN；
- 全程遵守平台 ToS，保留速率与异常治理能力。

