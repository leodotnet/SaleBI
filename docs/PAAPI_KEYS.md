# Amazon Product Advertising API（PA-API）密钥申请与配置指南

> 适用范围：PA-API v5（官方），用于产品搜索与ASIN详情等。本文介绍如何申请 Partner Tag 与 Access Key/Secret Key，并在本项目中配置。

## 1. 需要哪些信息
- Partner Tag：也称“Store ID/Tracking ID”，形如 `yourtag-20`（US 区）。
- Access Key ID / Secret Access Key：用于请求签名（AWS SigV4）。
- 区域与主机：如 US 区域通常使用 `webservices.amazon.com`。

## 2. 前置条件
- 拥有 Amazon 账户，并完成 Amazon Associates（联盟）注册（按区域分别注册）。
- 在联盟后台提交网站/应用信息并通过审核（页面、隐私政策、合规内容）。
- 了解合规要求：
  - 新账户需在 180 天内完成至少 3 笔有效成交，否则可能停用 PA-API 访问。
  - 遵循品牌与展示规范、不要过度缓存或再分发数据。

## 3. 申请流程（官方路径）
1) 注册/登录 Amazon Associates（对应区域）
- 例如 US 区域：登录 `https://affiliate-program.amazon.com/`。
- 完成账户信息、结算、网站/应用信息等必填项。

2) 获取 Partner Tag（Tracking ID）
- 在 Associates Central 后台的账户/设置中可以查看你的 Tracking ID；
- US 的 Tag 通常以 `-20` 结尾（其他区域后缀不同）。
- 如需多区域，请分别创建/确认对应区域的 Partner Tag。

3) 启用 PA-API 并创建访问密钥
- 在 Associates Central 后台进入“Tools（工具）”→ “Product Advertising API”。
- 按向导将你的 Associates 账户与 AWS 账户关联（若提示）；
- 创建或查看 Access Key ID / Secret Access Key（注意 Secret 只显示一次，请安全保存）。
- 若未见创建入口，检查账户是否满足 PA-API 使用条件或阅读后台提示（有时需完成基本合规审核后开放）。

4) 区域与主机
- 根据区域选择主机，例如：
  - US: `webservices.amazon.com`
  - UK: `webservices.amazon.co.uk`
  - DE: `webservices.amazon.de`
  - JP: `webservices.amazon.co.jp`
- 实际主机以官方文档为准；不同区域 Partner Tag 不同，调用需匹配。

## 4. 速率与使用规范（概览）
- 速率受账户表现与成交影响，官方会动态调整配额；
- 请实现退避重试、分页与结果最小化展示；
- 避免长时间缓存或离线分发原始数据；
- 展示时标注来源，例如“数据来源：Amazon PA-API”。

## 5. 本项目的环境变量与配置
在项目根目录创建 `.env`（或使用系统环境变量），示例变量如下：

- `PAAPI_ACCESS_KEY`：你的 Access Key ID
- `PAAPI_SECRET_KEY`：你的 Secret Access Key
- `PAAPI_PARTNER_TAG`：你的 Partner Tag（如 `yourtag-20`）
- `PAAPI_REGION`：区域（如 `US`）
- `PAAPI_HOST`：主机（如 `webservices.amazon.com`）

可选（LLM 支持，用于自然语言查询解析/结果总结）：
- `OPENAI_API_KEY` / `OPENAI_BASE_URL?` / `OPENAI_MODEL?`
- `GEMINI_API_KEY`（或 `GOOGLE_API_KEY`，视SDK而定）/ `GEMINI_MODEL?`
- `OLLAMA_HOST?` / `OLLAMA_MODEL?`

## 6. 测试与验证
- 使用 Associates Central 提供的 PA-API Scratchpad（如有）测试签名与请求；
- 在本项目中运行“连接测试”工具（后续会提供）验证：
  - `SearchItems` 基本查询；
  - `GetItems` ASIN 详情；
- 观察日志中的签名状态码（4xx/5xx）并根据提示修正主机/区域/Tag。

## 7. 安全建议
- 不要将密钥提交到版本库；使用 `.env` + 环境注入；
- 生产环境开启密钥轮换与最小化暴露；
- 日志避免输出完整密钥/签名；
- 限制内部导出能力，并在导出中标注来源与时间戳。

---
如在申请过程中遇到“无法创建密钥/权限不足”的提示，多半与账户审核、成交要求或区域设置相关。请先在 Associates Central 的 PA-API 页查看官方提示与操作入口，再按指引完成。 
