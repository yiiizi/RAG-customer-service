# RAG 电商智能客服系统

基于 LlamaIndex + Milvus + BGE-M3 + DeepSeek 的企业级 RAG（检索增强生成）电商智能客服系统，支持多格式文档知识库、混合检索、联网搜索、FAQ 高频问答、订单/物流查询、流式问答和可视化数据大盘。

## 技术架构

```
┌─────────────────────────────────────────────────────┐
│                   React 18 + Ant Design 5            │
│     流式对话 / 知识库管理 / FAQ / 订单查询 / 数据大盘    │
└────────────────────────┬────────────────────────────┘
                         │ WebSocket + REST API
┌────────────────────────▼────────────────────────────┐
│                   FastAPI (Python)                    │
│   意图识别 → 策略路由 → FAQ缓存 → 检索 → 联网 → 生成   │
├──────────────────────────────────────────────────────┤
│  Milvus 向量库  │  MySQL  │  Redis  │  BGE-M3 嵌入    │
│  BM25 稀疏检索  │  FAQ 存储 │ 热缓存  │  Tavily 联网    │
│  LlamaIndex 分块 │  订单Mock │ 会话持久化 │  BGE-Reranker │
└──────────────────────────────────────────────────────┘
```

## 功能特性

### 智能问答
- **流式输出**：WebSocket 实时推送，打字机效果
- **意图识别**：闲聊 / FAQ / 知识检索 / 订单查询 / 物流追踪 五路自动分流
- **混合检索**：Milvus 稠密向量 + BM25 稀疏检索 → RRF 融合
- **FAQ 缓存**：高频问答 Redis → MySQL 三级缓存，命中即返回
- **知识库模式**：纯知识库检索，LLM 总结检索内容
- **联网搜索**：Tavily API 实时搜索互联网信息
- **订单/物流查询**：模拟订单系统对接，查询订单状态和物流轨迹
- **多轮对话**：支持上下文记忆，最近 10 条消息作为历史
- **引用溯源**：区分知识库来源和网络搜索来源，分组展示

### 电商客服特性
- **五种意图**：闲聊 / 高频FAQ / 商品咨询 / 订单查询 / 物流追踪
- **FAQ 模糊匹配**：中文字符重叠相似度算法，70% 阈值
- **广告法过滤**：违禁词检测 + 提示词注入防护
- **错误容错**：Redis 认证失败自动降级到 MySQL，LLM 异常返回友好提示

### 知识库管理
- **12+ 文件格式**：PDF / Word / Excel / PPT / Markdown / HTML / CSV / JSON / EPUB / 图片 OCR / 代码文件
- **父子分块**：父块 1024 tokens（LLM 上下文），子块 256 tokens（精细检索）
- **拖拽上传**：50MB 前端校验 + 批量上传
- **分块可视化**：树形结构展示父子关系

### 数据大盘
- 问答趋势图 / 意图分布饼图 / 高频 FAQ 排行
- 响应延迟监控 / 缓存命中率
- 知识库存储统计

### 前端体验
- **三栏布局**：左侧对话历史 + 中间聊天区 + 右侧引用来源
- **顶部导航栏**：对话历史 / 知识库管理 / FAQ / 数据大盘 / 系统设置（弹窗式）
- **对话持久化**：localStorage 存储，刷新不丢失
- **欢迎屏幕**：5 个电商推荐问题，点击即发送
- **思考动画**：弹跳圆点 + 停止生成按钮
- **复制/重新生成**：AI 回答支持一键复制和重新生成
- **搜索对话**：侧边栏支持按标题和内容模糊搜索
- **深色/浅色双主题**：一键切换，自动持久化
- **WebSocket 重连**：指数退避（3s→30s），断连提示 + 手动重连

## 快速开始

### 环境要求

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | 3.10+ | 推荐 Anaconda |
| Node.js | 18+ | 前端构建 |
| Milvus | 2.4+ | Docker 部署 |
| MySQL | 5.6+ | 本地安装 |
| Redis | 7+ | Docker 部署 |

### 1. 启动基础服务

```bash
# Milvus Standalone (含 etcd + MinIO)
wget https://github.com/milvus-io/milvus/releases/download/v2.4.4/milvus-standalone-docker-compose.yml
docker-compose -f milvus-standalone-docker-compose.yml up -d

# Redis
docker run -d --name redis -p 6379:6379 redis --requirepass 1234

# MySQL — 创建数据库
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS rag_db CHARACTER SET utf8mb4;"
```

### 2. 安装后端

```bash
cd backend
pip install -r requirements.txt

# 编辑 config/.env
# MYSQL_PASSWORD=你的密码
# LLM_API_KEY=你的DeepSeek_API_Key
# REDIS_URL=redis://:密码@127.0.0.1:6379/0
# TAVILY_API_KEY=你的Tavily_Key（可选，联网搜索）

# 导入电商 FAQ 数据
python scripts/ecommerce_faq.py

# 启动
python main.py
# 默认 http://localhost:8000
```

### 3. 安装前端

```bash
cd frontend
npm install
npx vite --host 0.0.0.0
# 默认 http://localhost:5173，局域网可访问
```

### 4. 使用

1. 打开 `http://localhost:5173`
2. 点击欢迎界面的推荐问题快速开始
3. 或在输入框输入问题，支持以下模式：
   - **普通问答**：自动识别意图
   - **知识库**：点击「知识库」按钮，强制走知识库检索
   - **联网搜索**：点击「联网」按钮，Tavily 搜索增强
4. 点击顶部导航栏打开知识库管理、FAQ、数据大盘、系统设置

## 意图识别流程

```
用户输入
    │
    ▼
┌─────────────────┐
│  关键词规则匹配   │  ← 快速、零成本
│  (正则表达式)     │
└────────┬────────┘
         │ 匹配到 且 置信度 ≥ 0.6？
         ├── 是 → 直接返回意图
         │
         ▼ 否
┌─────────────────┐
│  LLM 意图分类    │  ← 准确、有 API 成本
└────────┬────────┘
         │
         ▼
    返回意图 (chat / faq / knowledge_qa / order_query / logistics_track)
```

| 意图 | 示例 | 处理方式 |
|------|------|---------|
| chat | "你好"、"谢谢" | 直接 LLM 回答 |
| faq | "退换货政策"、"优惠活动" | Redis → MySQL 缓存 → 检索兜底 |
| knowledge_qa | "推荐个耳机" | 知识库检索 + LLM 总结 |
| order_query | "我的订单到哪了" | FAQ 缓存 → 模拟订单数据 + LLM |
| logistics_track | "快递到哪了" | FAQ 缓存 → 模拟物流数据 + LLM |

## 项目结构

```
RAG/
├── backend/
│   ├── config/               # Pydantic Settings 配置
│   ├── mysql_module/         # MySQL + Redis + BM25
│   ├── rag_qa/               # RAG 核心
│   │   ├── pipeline.py       # 主流程编排（含 web_search/kb_only 组合）
│   │   ├── intent_recognizer.py  # 五路意图识别
│   │   ├── generator.py      # LLM 生成（4 套提示词 + 异常捕获）
│   │   ├── retriever.py      # 混合检索
│   │   ├── web_search.py     # Tavily 联网搜索
│   │   ├── ecommerce_mock.py # 订单/物流/商品模拟数据
│   │   └── content_filter.py # 敏感词 + 注入防护
│   ├── offline_kb/           # 离线知识库（LlamaIndex）
│   ├── api/                  # FastAPI 路由
│   └── scripts/              # FAQ 数据导入脚本
│
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Chat/         # 智能问答（主页面）
│       │   ├── KnowledgeBase/ # 知识库管理（弹窗）
│       │   ├── FAQ/          # FAQ 管理（弹窗）
│       │   ├── Dashboard/    # 数据大盘（弹窗）
│       │   └── Settings/     # 系统设置（弹窗）
│       ├── stores/           # Zustand（含 persist 持久化）
│       ├── hooks/            # WebSocket（指数退避重连）
│       ├── layouts/          # MainLayout（侧边栏 + 导航栏）
│       └── components/       # MarkdownViewer、EmptyState 等
│
└── README.md
```

## 配置说明

编辑 `backend/config/.env`：

```env
# MySQL
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password

# Milvus
MILVUS_HOST=127.0.0.1
MILVUS_PORT=19530

# Redis（带密码）
REDIS_URL=redis://:your_password@127.0.0.1:6379/0

# DeepSeek LLM
LLM_API_BASE=https://api.deepseek.com
LLM_API_KEY=sk-your-api-key
LLM_MODEL=deepseek-v4-pro

# Tavily 联网搜索（可选）
TAVILY_API_KEY=tvly-your-api-key
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat` | 非流式问答 |
| WS | `/api/ws/chat` | WebSocket 流式问答 |
| POST | `/api/kb/upload` | 上传文档 |
| GET | `/api/kb/list` | 文档列表 |
| GET | `/api/kb/stats` | 知识库统计 |
| GET | `/api/kb/chunks/{file}` | 文件分块详情 |
| DELETE | `/api/kb/{file}` | 删除文档 |
| POST | `/api/kb/reindex` | 重新索引 |
| CRUD | `/api/faq` | FAQ 管理 |
| POST | `/api/faq/batch-import` | FAQ 批量导入 |
| GET | `/api/dashboard` | 数据大盘 |
| GET/PUT | `/api/settings` | 系统设置 |
| GET | `/health` | 健康检查 |

## 常见问题

**Q: BGE-M3 模型加载慢？**
首次运行自动下载 ~2.2GB 到 `~/.cache/huggingface/`。可设置 `HF_HUB_OFFLINE=1` 使用本地缓存。

**Q: Redis 认证失败？**
确保 `.env` 中 `REDIS_URL` 包含密码：`redis://:password@127.0.0.1:6379/0`

**Q: 联网搜索不生效？**
在 `backend/config/.env` 配置 `TAVILY_API_KEY`，https://tavily.com 免费注册。

**Q: 其他电脑无法访问？**
前端用 `npx vite --host 0.0.0.0` 启动，后端确保 `APP_HOST=0.0.0.0`。其他电脑通过 `http://服务器IP:5173` 访问。

**Q: FAQ 匹配不准？**
系统使用中文字符重叠相似度算法（70% 阈值），确保 FAQ 问题表述与用户常见问法一致。
