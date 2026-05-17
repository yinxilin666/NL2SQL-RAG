# NL2SQL RAG — Hive 自然语言转 SQL 问答系统

基于 Excel 数据表元数据构建 RAG 知识库，使用本地部署的 **deepseek-r1:8b** 模型将自然语言转换为 **HiveQL** 可执行 SQL。

## 系统架构

```
Excel 元数据 → 三级分块 → 向量库(ChromaDB) + 关键词索引(BM25)
                                    ↓
用户自然语言 → 混合检索(RRF融合) → deepseek-r1:8b → HiveQL SQL
                                    ↓
                          FastAPI + Streamlit UI
```

## 前置条件

| 组件 | 版本要求 | 说明 |
|------|---------|------|
| Python | ≥ 3.10 | |
| Ollama | 最新版 | 本地 LLM 服务，默认端口 11434 |
| deepseek-r1:8b | — | `ollama pull deepseek-r1:8b` |
| nomic-embed-text | — | `ollama pull nomic-embed-text` |

### 安装 Ollama 模型

```bash
ollama pull deepseek-r1:8b
ollama pull nomic-embed-text
```

验证模型已安装：

```bash
ollama list
```

## 项目初始化

### 1. 安装 Python 依赖

```bash
cd nl2sql-rag
pip install -r requirements.txt
```

### 2. 配置文件

编辑 `.env`（已生成默认值，按需修改）：

```env
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=deepseek-r1:8b
EMBED_MODEL=nomic-embed-text
CHROMADB_PATH=data/chromadb
BM25_INDEX_PATH=data/bm25_index/bm25.pkl
EXCEL_INPUT_PATH=data/input/schema.xlsx
```

### 3. 准备 Excel 文件

将 Excel 文件放入 `data/input/schema.xlsx`，必须包含以下 6 列：

| 列名 | 说明 | 示例 |
|------|------|------|
| `table` | 表名 | `user_info` |
| `subs_code` | 子系统代码 | `USER` |
| `table_comment` | 表名注释 | `用户基础信息表` |
| `column_name` | 字段名称 | `mobile` |
| `column_comment` | 字段注释 | `手机号` |
| `column_type` | 字段类型 | `varchar(20)` |

Excel 中每一行代表一个字段，同一表名的多行自动合并。

### 4. 知识库摄入（首次）

```bash
python -m scripts.ingest --file data/input/schema.xlsx
```

成功输出示例：

```
Loading Excel: data/input/schema.xlsx
Ollama URL: http://localhost:11434
ChromaDB path: data/chromadb
BM25 index path: data/bm25_index/bm25.pkl

 Ingestion complete!
   Tables:    25
   Chunks:    520
     - table: 25
     - field: 480
     - rel:   15
```

成功后会生成：
- `data/chromadb/` — ChromaDB 向量数据库
- `data/bm25_index/bm25.pkl` — BM25 关键词索引

### 5. 启动 API 服务

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

验证 API 是否正常：

```bash
curl http://localhost:8000/api/health
```

返回示例：

```json
{
  "status": "ok",
  "ollama": true,
  "chromadb": true,
  "bm25_index_loaded": true,
  "num_chunks": 520
}
```

API 文档（Swagger）：打开浏览器访问 `http://localhost:8000/docs`

### 6. 启动 Web UI

```bash
streamlit run ui/app.py
```

访问 `http://localhost:8501`，在对话框中输入自然语言问题即可获得 HiveQL SQL。

---

## 增量更新

当 Excel 文件发生变更（新增表、修改字段、调整注释等），无需重新从头构建，支持增量更新。

### 方式一：通过 API 更新

```bash
curl -X POST http://localhost:8000/api/reindex \
  -H "Content-Type: application/json" \
  -d '{"excel_path": "data/input/schema_v2.xlsx", "incremental": true}'
```

参数说明：
- `excel_path`：新的 Excel 文件路径（可选，默认读取 `.env` 中配置的路径）
- `incremental`：`true` = 增量更新（upsert），`false` = 全量重建

### 方式二：通过 UI 更新

1. 打开 `http://localhost:8501`
2. 点击左侧边栏的 **"Re-index"** 按钮
3. 等待提示 `"XX tables indexed"` 即完成

### 方式三：通过 CLI 更新

```bash
# 增量更新（默认）
python -m scripts.ingest --file data/input/schema_v2.xlsx --incremental

# 全量重建
python -m scripts.ingest --file data/input/schema_v2.xlsx
```

### 增量更新原理

- **ChromaDB**：使用 `upsert` 操作，相同 `id` 的 chunk 会被更新，新增 chunk 会被插入
- **BM25 索引**：由于 BM25 依赖全局词频统计，增量时整体重建 pickle 文件

---

## API 接口速查

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 |
| `POST` | `/api/query` | 自然语言转 SQL（核心） |
| `GET` | `/api/schema` | 查看已加载的表列表 |
| `GET` | `/api/rules` | 查看表级规则 |
| `POST` | `/api/reindex` | 重新摄入 Excel（增量更新） |

### POST /api/query 示例

请求：

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "查询上个月注册的用户中，手机号以138开头的有多少人",
    "top_k": 8,
    "temperature": 0.1,
    "include_reasoning": false,
    "few_shot": true
  }'
```

响应：

```json
{
  "sql": "SELECT COUNT(DISTINCT user_id) AS user_cnt\nFROM user_info\nWHERE register_time >= DATE_ADD(LAST_DAY(DATE_ADD(CURRENT_DATE, -2)), 1)\n  AND register_time < DATE_ADD(LAST_DAY(DATE_ADD(CURRENT_DATE, -1)), 1)\n  AND mobile LIKE '138%';",
  "reasoning": null,
  "retrieved_tables": ["user_info"],
  "warnings": [],
  "execution_time_ms": 2345.67
}
```

请求参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `question` | string | 必填 | 自然语言问题 |
| `top_k` | int | 8 | 检索的 chunk 数量 (1-30) |
| `temperature` | float | 0.1 | LLM 温度 (0.0-2.0) |
| `include_reasoning` | bool | false | 是否返回推理过程 |
| `few_shot` | bool | true | 是否包含 few-shot 示例 |

---

## 表级规则配置

部分表在查询时需要固定带上某些过滤条件（例如只查有效数据 `vali_flag = '1'`），手动每次输入既繁琐又容易遗漏。通过表级规则功能，可以为指定的表预设查询条件，系统在生成 SQL 时自动注入，无需重复输入。

### 配置规则

编辑 `data/table_rules.json`：

```json
{
  "rules": [
    {
      "table": "",
      "condition": "",
      "description": ""
    }
  ]
}
```

每项规则的字段说明：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `table` | string | 是 | 表名，与 Excel 中 `table` 列保持一致 |
| `condition` | string | 是 | SQL WHERE 条件，会自动拼接到查询中 |
| `description` | string | 否 | 规则说明，方便维护和理解 |

### 工作原理

1. 用户输入自然语言问题
2. 混合检索召回相关的 schema 片段，识别出涉及的表名
3. 自动匹配 `table_rules.json` 中对应表的规则
4. 在 LLM 提示词中注入规则（以 `TABLE-SPECIFIC RULES (MUST BE APPLIED)` 区块呈现）
5. LLM 生成 SQL 时强制应用这些条件

### 查看与验证

- **UI 侧边栏**：点击「加载规则」按钮可查看所有已配置规则
- **查询响应**：每次查询结果的元数据中会展示本次应用了哪些规则（`已应用规则: xxx`）
- **API 接口**：`GET /api/rules` 返回所有规则列表

---

## 项目目录结构

```
nl2sql-rag/
├── .env                          # 环境变量配置
├── requirements.txt              # Python 依赖
├── config/                       # 配置层
│   ├── settings.py               # Pydantic 配置（读取 .env）
│   ├── constants.py              # 常量定义
│   └── table_rules.py            # 表级规则加载器
├── data/
│   ├── input/                    # 放置 Excel 文件
│   │   └── schema.xlsx
│   └── table_rules.json           # 表级规则配置
│   ├── chromadb/                 # ChromaDB 持久化（自动生成）
│   └── bm25_index/               # BM25 索引 pickle（自动生成）
├── ingestion/                    # 数据摄入层
│   ├── loader.py                 # Excel 解析
│   ├── chunker.py                # 三级分块（表/字段/关系）
│   ├── embedder.py               # Ollama 嵌入
│   └── indexer.py                # 摄入编排器
├── retrieval/                    # 检索层
│   ├── vector_store.py           # ChromaDB 封装
│   ├── bm25_retriever.py         # BM25 关键词检索
│   └── hybrid_retriever.py       # RRF 混合检索
├── llm/                          # LLM 层
│   ├── ollama_client.py          # Ollama API 客户端
│   ├── prompt_templates.py       # Prompt 模板
│   ├── response_parser.py        # deepseek-r1 输出解析
│   └── sql_validator.py          # HiveQL 语法校验
├── api/                          # API 层
│   ├── main.py                   # FastAPI 入口
│   ├── dependencies.py           # 依赖注入
│   ├── routers/                  # 路由
│   │   ├── query.py              # POST /api/query
│   │   ├── health.py             # GET /api/health
│   │   ├── schema.py             # GET /api/schema
│   │   ├── rules.py              # GET /api/rules
│   │   └── reindex.py            # POST /api/reindex
│   └── schemas/                  # Pydantic 模型
├── ui/                           # UI 层
│   ├── app.py                    # Streamlit 入口
│   ├── components/               # UI 组件
│   │   ├── sidebar.py            # 侧边栏
│   │   └── chat_panel.py         # 对话区域
│   └── utils/                    # 工具函数
├── scripts/
│   └── ingest.py                 # CLI 摄入脚本
└── tests/                        # 单元测试（待补充）
```

---

## 常见问题

**Q: Ollama 连接失败？**

确保 Ollama 已启动且端口正确：
```bash
ollama serve          # 默认监听 11434
curl http://localhost:11434/api/tags
```

**Q: 摄入时报 "embedding" 相关错误？**

确保 `nomic-embed-text` 模型已拉取：
```bash
ollama pull nomic-embed-text
```

**Q: deepseek-r1 输出格式不稳定，SQL 提取失败？**

`response_parser.py` 内置了多层兜底策略：
1. 优先匹配 `<think>...</think>` + `<sql>...</sql>` 标签
2. 无标签时搜索 `SELECT ...` 语句
3. 模型拒答时返回错误注释而非编造

**Q: 如何添加自定义 SQL 规则？**

编辑 `llm/prompt_templates.py` 中的 `SYSTEM_PROMPT` 和 `llm/sql_validator.py` 中的 `FORBIDDEN_PATTERNS`。

**Q: 向量检索结果不相关？**

尝试调整 Top-K 参数：
- API：请求中 `"top_k": 15`
- UI：侧边栏 `Top-K chunks` 滑块调大
