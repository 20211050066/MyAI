# 游戏百科智能问答系统
基于RAG混合检索架构的游戏知识库智能问答平台，整合向量检索、全文检索、LLM查询改写、Rerank重排序能力，搭配Streamlit可视化前端，支持多格式文档导入、多轮流式对话、会话缓存与知识库全生命周期管理。

## 一、项目目录结构
```
游戏百科智能问答系统/
├── app.py                    # Streamlit 主页面 - 智能问答对话
├── main.py                   # 项目启动入口
├── config.py                 # 全局配置管理（PostgreSQL/Redis/Embedding/LLM/搜索参数）
├── db_pool.py                # PostgreSQL + Redis 连接池封装
├── doc_processor.py          # 多格式文档解析（TXT/PDF/DOCX/PPTX/图片）
├── embeddings.py             # Embedding 文本向量化服务
├── knowledge_base.py         # 知识库核心管理（上传/索引/查询/删除/数据统计）
├── vector_search.py          # 向量检索模块（pgvector、余弦距离、HNSW向量索引）
├── fulltext_search.py        # 全文检索模块（PostgreSQL tsvector + Jieba中文分词）
├── reranker.py               # 文本重排序服务（智谱Rerank API）
├── hybrid_search.py          # 混合搜索编排主逻辑
├── chat_history_store.py     # Redis 对话会话持久化存储
├── rag.py                    # RAG问答主服务（检索+上下文拼接+LLM生成）
├── requirements.txt          # Python项目依赖清单
├── .env                      # 本地环境变量配置文件
└── pages/
    ├── 1_知识库管理.py        # 知识库可视化页面：文档上传/列表/删除/数据统计
    └── 2_对话历史.py          # 会话历史页面：记录浏览、一键清空会话
```

## 二、核心架构：混合搜索流水线
整体流程遵循「混合搜索.doc」规范，共5个执行步骤：

| 步骤 | 功能模块 | 底层技术实现 |
|------|--------|------------|
| Step 1 | Query Rewrite 查询改写 | 轻量LLM生成原始query+2条变体查询，Redis缓存复用 |
| Step 2 | 双路召回检索 | pgvector 1024维向量检索 + PostgreSQL tsvector Jieba全文检索 |
| Step 3 | RRF融合排序 | Reciprocal Rank Fusion 多路结果融合，参数K=60 |
| Step 4 | Rerank 精排过滤 | 智谱Rerank API，匹配阈值0.1，接口超时限制10s |
| Step 5 | 结果去重截断 | 单文档最多保留2个片段，输出Top-K候选上下文 |

## 三、数据存储方案
| 存储介质 | 技术组件 | 业务存储用途 |
|---------|--------|------------|
| PostgreSQL + pgvector | 关系型数据库+向量扩展 | 知识库底层存储：documents文档主表、document_chunks文本分片表；内置向量列、全文分词索引 |
| Redis | 内存缓存数据库 | 1. 用户对话会话历史（24小时自动过期）<br>2. 查询改写缓存（10分钟有效期）<br>3. 混合检索结果缓存（1分钟有效期） |

## 四、前端页面功能
基于Streamlit搭建多页面可视化后台，三大核心模块：
- 🎮 对话主页面：支持多轮上下文问答、LLM流式输出、历史上下文记忆
- 📚 知识库管理页：多格式文档上传（TXT/PDF/DOCX/PPTX/图片）、纯文本快速导入、文档列表查看、文档删除、知识库数据统计
- 💬 对话历史页：全量会话记录浏览、一键清空全部会话缓存

## 五、快速部署与启动
### 1. 安装项目依赖
```bash
pip install -r requirements.txt
```

### 2. 环境变量配置
复制`.env.example`并重命名为`.env`，填写对应密钥与数据库参数；Windows临时配置示例：
```cmd
set DASHSCOPE_API_KEY=你的大模型API密钥
set PG_PASSWORD=你的PostgreSQL数据库密码
```

### 3. 初始化数据库向量扩展
自动创建pgvector扩展、业务数据表与索引：
```bash
python -c "from db_pool import ensure_pgvector; ensure_pgvector()"
```

### 4. 启动完整应用
```bash
python main.py
```

## 六、核心文件说明
1. `main.py`：统一启动入口，加载配置、初始化数据库连接池、拉起Streamlit服务
2. `config.py`：集中管理所有可调参数（向量维度、RRF权重、rerank阈值、缓存过期时间等）
3. `db_pool.py`：单例数据库连接池，复用PG/Redis连接，避免频繁创建连接开销
4. `doc_processor.py` 统一解析各类文件，提取纯文本并做清洗分片
5. `hybrid_search.py` 混合检索调度中心，串联查询改写、双路召回、融合、精排全流程
6. `rag.py` 接收用户问题，调用混合搜索获取上下文，拼接Prompt后调用LLM生成回答
7. `chat_history_store.py` 封装Redis读写逻辑，实现会话隔离、自动过期清理