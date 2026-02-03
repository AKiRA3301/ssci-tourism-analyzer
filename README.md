# 📊 SSCI旅游学术趋势分析系统

> **2026版 | 基于Python的文献计量与AI辅助选题工具**

这是一个专为旅游管理研究者设计的**"降维打击"工具**，帮助你：
- 🔍 快速掌握近3年研究热点与趋势
- 🎯 精准定位"高价值研究缺口"
- 📝 生成专业的文献计量分析报告
- 🤖 AI辅助生成论文选题与写作建议

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 进入项目目录
cd ssci_analyzer

# 最小安装（核心功能）
pip install requests

# 推荐安装（完整功能）
pip install requests pandas openpyxl matplotlib networkx

# 完整安装（包含AI辅助）
pip install requests pandas openpyxl matplotlib networkx anthropic
```

### 2. 运行程序

```bash
# 交互式菜单模式（推荐新手）
python main.py --interactive

# 命令行模式 - 从OpenAlex获取数据并分析
python main.py --fetch --keywords "generative AI tourism" --years 2024-2026 --analyze

# 导入本地WoS导出文件
python main.py --import-wos savedrecs.txt --analyze

# 生成完整报告（包含AI建议）
python main.py --fetch --keywords "virtual reality tourism" --analyze --ai-suggest
```

---

## 📂 数据来源

### 方案一：合法API获取（推荐）

本系统使用**免费开放的学术API**，无需登录或订阅：

| API | 说明 | 限制 |
|-----|------|------|
| **OpenAlex** | 最全面的开放学术数据库 | 无限制 |
| **Semantic Scholar** | AI2的学术搜索引擎 | 100次/5分钟 |
| **Crossref** | DOI元数据 | 友好限速 |

```bash
# 示例：获取生成式AI相关旅游研究
python main.py --fetch --keywords "ChatGPT tourism" --source openalex --limit 500
```

### 方案二：导入手动导出文件

如果你有**机构订阅**，可以从Web of Science或Scopus导出数据：

1. **Web of Science导出**：
   - 搜索后点击"Export" → "Tab delimited file" 或 "BibTeX"
   - 选择"Full Record"包含摘要

2. **Scopus导出**：
   - 搜索后点击"Export" → "CSV" 或 "BibTeX"
   - 勾选"Include abstract"

```bash
# 导入WoS文件
python main.py --import-wos savedrecs.txt --analyze

# 导入Scopus CSV
python main.py --import-scopus scopus_export.csv --analyze
```

---

## 🔧 功能模块详解

### 模块A：数据采集

**支持的数据字段**：
- 标题、作者、年份、DOI
- 摘要（Abstract）
- 作者关键词（Author Keywords）
- 被引频次
- 期刊名称

**目标期刊**：
- Tourism Management
- Annals of Tourism Research
- Journal of Travel Research
- International Journal of Hospitality Management
- Journal of Sustainable Tourism
- 等20+旅游类SSCI期刊

### 模块B：文本预处理

- **分词清洗**：去除停用词、学术套话
- **词干合并**：tourists→tourism, sustainable→sustainability
- **术语识别**：识别专业词汇（LLM, ChatGPT, VR, AR等）
- **短语提取**：识别多词短语（artificial intelligence, virtual reality）

### 模块C：关键词分析

```
📊 高频关键词 Top 10:
   1. sustainable tourism          (892次)
   2. tourist behavior             (654次)
   3. destination image            (521次)
   4. social media                 (489次)
   5. customer satisfaction        (423次)
   ...

🔥 突发词 (Burst Words) - 近期热度飙升:
   ⚡ ChatGPT                      (突发指数: 8.42)
   ⚡ generative AI                (突发指数: 7.65)
   ⚡ large language model         (突发指数: 6.91)
   ...
```

### 模块D：LDA主题建模

自动将论文聚类为8-10个研究方向：

```
主题 1: 智能旅游与AI技术
   关键词: artificial intelligence, chatbot, smart tourism, technology acceptance
   代表论文: "ChatGPT and the future of tourism marketing"
   
主题 2: 可持续发展与生态旅游
   关键词: sustainable, eco-tourism, carbon footprint, climate change
   代表论文: "Tourists' pro-environmental behavior..."
```

### 模块E：可视化输出

生成4类专业图表（保存为PNG/HTML）：

1. **关键词共现网络** - 哪些概念经常一起出现
2. **时序热力图** - 关键词热度演变
3. **被引-频率矩阵** - 发现"高被引低频率"的潜力选题
4. **主题分布图** - 研究方向占比

### 模块F：研究缺口识别

**核心"骚操作"** - 从论文中提取Limitations和Future Research：

```python
# 系统自动识别论文末尾的"研究遗憾"
limitations = [
    "This study focused only on Chinese tourists...",
    "Future research should examine long-term effects...",
    "The generalizability of findings is limited to..."
]

# 汇总后生成缺口报告
research_gaps = [
    "💡 跨文化比较研究不足 - 多数研究仅关注单一国家样本",
    "💡 纵向追踪研究缺乏 - 缺少对旅游行为长期变化的研究",
    "💡 技术采纳的调节因素 - AI在旅游中的信任机制待探索"
]
```

### 模块G：AI辅助分析

**需要设置环境变量**：
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

**功能**：
1. 基于分析结果生成3-5个创新选题
2. 提供完整的研究框架和方法论建议
3. 生成文献综述写作框架
4. 回答关于研究设计的具体问题

---

## 📋 输出报告示例

运行完成后生成 `output/analysis_report.md`：

```markdown
# SSCI旅游研究趋势分析报告
生成时间: 2026-02-03

## 一、数据概览
- 分析论文数: 1,247篇
- 时间范围: 2024-01 至 2026-01
- 覆盖期刊: 15种SSCI期刊

## 二、关键词热度分析
[表格: 高频词、突发词、衰退词]

## 三、研究主题聚类
[LDA主题建模结果]

## 四、研究缺口识别
基于200篇论文的"Limitations"和"Future Research"分析：
1. AI伦理在旅游决策中的影响机制（提及频次: 23）
2. 虚拟现实旅游的长期用户粘性（提及频次: 18）
3. ...

## 五、选题建议
### 推荐选题 1: 
**题目**: "生成式AI如何重塑游客信息搜索行为？基于眼动追踪的实证研究"
**创新点**: 
- 首次将眼动技术应用于AI旅游推荐研究
- 填补游客注意力分配机制的研究空白

### 推荐选题 2:
...
```

---

## 💡 论文写作技巧

### 方法论部分这样写（加分项！）：

> 本研究采用基于Python的多阶段文本挖掘技术（Text Mining），对Web of Science数据库2024-2026年间收录的1,247篇旅游类SSCI论文进行了系统性的演化路径分析。
>
> 首先，运用潜在狄利克雷分配（LDA）主题模型对文献进行聚类，识别出8个核心研究方向；其次，采用突发检测算法（Burst Detection）识别近期热度显著上升的新兴议题；最后，通过文本挖掘技术提取各论文的"研究局限"与"未来建议"章节，汇总分析学界共识的研究缺口。

**审稿人看到这段会想**：这作者技术很扎实，研究很系统！

### 投稿策略建议

1. **首选期刊**：Tourism Management, Annals of Tourism Research
2. **备选期刊**：Journal of Travel Research, IJHM
3. **投稿前**：先在TTRA、ENTER等会议试水
4. **修改响应**：收到R&R后2-3周内回复

---

## 📁 项目结构

```
ssci_analyzer/
├── main.py                 # 主程序入口
├── requirements.txt        # 依赖包列表
├── README.md              # 使用说明（本文件）
├── modules/
│   ├── data_fetcher.py    # API数据获取
│   ├── file_importer.py   # 文件导入
│   ├── text_processor.py  # 文本预处理
│   ├── analyzer.py        # 关键词/主题分析
│   ├── visualizer.py      # 可视化生成
│   └── ai_advisor.py      # AI辅助建议
└── output/                # 输出目录
    ├── analysis_report.md
    ├── keywords.csv
    ├── topics.csv
    └── figures/
```

---

## ⚠️ 重要说明

### 合法合规使用

1. **本系统不提供非法爬取功能**
   - Web of Science、Scopus需机构订阅
   - 请通过官方导出功能获取数据

2. **使用开放API获取公开数据**
   - OpenAlex是完全开放的学术数据库
   - 所有数据获取均符合API使用条款

3. **尊重版权**
   - 系统仅处理元数据（标题、摘要、关键词）
   - 不涉及论文全文内容

### 技术支持

如遇问题，请检查：
1. Python版本 ≥ 3.8
2. 依赖包已正确安装
3. 网络连接正常（API调用）
4. 如使用AI功能，确认API密钥已设置

---

## 🎯 使用案例

### 案例1：寻找AI+旅游的研究缺口

```bash
# 步骤1：获取数据
python main.py --fetch --keywords "artificial intelligence tourism" --years 2024-2026

# 步骤2：运行分析
python main.py --analyze

# 步骤3：获取AI建议
python main.py --ai-suggest --focus "AI ethics in tourism"
```

输出：建议研究"AI推荐系统的算法偏见如何影响游客目的地选择"

### 案例2：为毕业论文选题

```bash
python main.py --interactive
# 选择功能7 "AI辅助研究分析"
# 输入你的研究兴趣和背景
# 获得定制化选题建议
```

---

**祝你SSCI发表顺利！** 🎉

有问题欢迎反馈改进。
