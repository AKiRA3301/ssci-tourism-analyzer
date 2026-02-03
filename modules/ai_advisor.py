"""
AI辅助模块
生成研究选题建议、论文写作指导等
"""

import logging
import os
from typing import List, Dict, Optional
from collections import Counter

logger = logging.getLogger(__name__)


class AIAdvisor:
    """AI研究顾问"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化AI顾问
        
        Args:
            api_key: Anthropic API Key（可选，用于调用Claude API）
        """
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        self.has_api = bool(self.api_key)
        
        if self.has_api:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("已连接Anthropic API")
            except ImportError:
                logger.warning("anthropic包未安装，将使用本地分析")
                self.has_api = False
            except Exception as e:
                logger.warning(f"API连接失败: {e}，将使用本地分析")
                self.has_api = False
        else:
            logger.info("未配置API Key，将使用本地规则分析")
    
    def generate_suggestions(self, papers: List[Dict], gaps: Optional[List[Dict]] = None,
                            focus_area: Optional[str] = None) -> str:
        """
        生成研究选题建议
        
        Args:
            papers: 分析过的论文列表
            gaps: 识别的研究缺口
            focus_area: 聚焦的研究方向（可选）
        
        Returns:
            建议报告（Markdown格式）
        """
        # 收集分析数据
        analysis_data = self._collect_analysis_data(papers, gaps, focus_area)
        
        if self.has_api:
            return self._generate_with_api(analysis_data)
        else:
            return self._generate_local(analysis_data)
    
    def _collect_analysis_data(self, papers: List[Dict], gaps: Optional[List[Dict]],
                               focus_area: Optional[str]) -> Dict:
        """收集用于分析的数据"""
        # 关键词统计
        keyword_freq = Counter()
        for p in papers:
            keywords = p.get('all_keywords', p.get('keywords', []))
            keyword_freq.update(keywords)
        
        # 研究局限性和未来研究建议
        limitations = []
        future_research = []
        for p in papers:
            if p.get('limitations'):
                limitations.append(p['limitations'])
            if p.get('future_research'):
                future_research.append(p['future_research'])
        
        # 高被引论文
        top_cited = sorted(papers, key=lambda x: x.get('citations', 0), reverse=True)[:10]
        
        # 最新论文
        recent = sorted([p for p in papers if p.get('year')], 
                       key=lambda x: x['year'], reverse=True)[:10]
        
        return {
            'total_papers': len(papers),
            'top_keywords': dict(keyword_freq.most_common(30)),
            'limitations': limitations[:20],
            'future_research': future_research[:20],
            'top_cited': [{'title': p.get('title', ''), 'citations': p.get('citations', 0)} for p in top_cited],
            'recent_papers': [{'title': p.get('title', ''), 'year': p.get('year')} for p in recent],
            'gaps': gaps or [],
            'focus_area': focus_area
        }
    
    def _generate_with_api(self, data: Dict) -> str:
        """使用API生成建议"""
        prompt = self._build_prompt(data)
        
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return message.content[0].text
            
        except Exception as e:
            logger.error(f"API调用失败: {e}")
            return self._generate_local(data)
    
    def _build_prompt(self, data: Dict) -> str:
        """构建API提示词"""
        prompt = f"""你是一位资深的旅游学SSCI期刊编辑和学术研究顾问。请基于以下学术文献分析数据，为一位想发表SSCI论文的研究者提供选题建议和写作指导。

## 分析数据概览

- 分析论文数量：{data['total_papers']}篇
- 聚焦方向：{data['focus_area'] or '未指定'}

## Top 30 高频关键词
{self._format_keywords(data['top_keywords'])}

## 高被引论文（Top 10）
{self._format_papers(data['top_cited'])}

## 最新发表论文（Top 10）
{self._format_recent(data['recent_papers'])}

## 研究局限性摘录（来自多篇论文）
{self._format_list(data['limitations'][:10])}

## 未来研究建议摘录（来自多篇论文）
{self._format_list(data['future_research'][:10])}

## 已识别的研究缺口
{self._format_gaps(data['gaps'])}

---

请提供以下内容（用中文回答）：

### 1. 选题建议（3-5个具体选题）
- 每个选题需要包含：题目、研究问题、创新点、潜在贡献
- 选题应当：填补研究缺口、结合新兴趋势、具有理论和实践价值

### 2. 方法论建议
- 推荐的研究设计
- 数据收集方法
- 分析技术（可以突出使用Python/文本挖掘/大数据分析等方法）

### 3. 论文写作指导
- 如何在方法论部分体现技术含量
- 如何定位理论贡献
- 审稿人可能关注的点

### 4. 发表策略
- 适合投稿的目标期刊
- 提高接受率的建议

请确保建议具有实操性，能够直接指导研究工作。
"""
        return prompt
    
    def _generate_local(self, data: Dict) -> str:
        """本地生成建议（不使用API）"""
        suggestions = []
        
        suggestions.append("# SSCI旅游论文选题与写作建议报告")
        suggestions.append(f"\n**分析基础**: {data['total_papers']}篇论文")
        if data['focus_area']:
            suggestions.append(f"\n**聚焦方向**: {data['focus_area']}")
        
        suggestions.append("\n---\n")
        
        # 1. 选题建议
        suggestions.append("## 1. 选题建议\n")
        
        # 基于关键词分析生成选题
        top_kws = list(data['top_keywords'].keys())[:15]
        
        # 识别热门主题组合
        tech_keywords = ['ai', 'vr', 'ar', 'iot', 'generative ai', 'chatgpt', 'metaverse', 'smart tourism']
        behavior_keywords = ['satisfaction', 'loyalty', 'motivation', 'experience', 'behavior', 'intention']
        sustainability_keywords = ['sustainable', 'green', 'eco', 'carbon', 'environmental']
        
        found_tech = [k for k in top_kws if any(t in k.lower() for t in tech_keywords)]
        found_behavior = [k for k in top_kws if any(b in k.lower() for b in behavior_keywords)]
        found_sustain = [k for k in top_kws if any(s in k.lower() for s in sustainability_keywords)]
        
        topic_suggestions = []
        
        # 选题1：技术+行为
        if found_tech and found_behavior:
            topic_suggestions.append({
                'title': f"The Impact of {found_tech[0].title()} on Tourist {found_behavior[0].title()}: A Multi-Method Approach",
                'question': f"How does {found_tech[0]} technology influence tourist {found_behavior[0]} in the post-pandemic era?",
                'innovation': "Combines emerging technology with classic tourism behavior research, using mixed-methods design",
                'contribution': "Extends technology acceptance model to tourism context, provides practical insights for industry"
            })
        
        # 选题2：可持续+数字化
        if found_sustain or found_tech:
            topic_suggestions.append({
                'title': "Digital Transformation and Sustainable Tourism: A Text Mining Analysis of Tourist Reviews",
                'question': "How can digital technologies promote sustainable tourism practices and influence tourist behavior?",
                'innovation': "Uses text mining and sentiment analysis on large-scale UGC data",
                'contribution': "Bridges the gap between technology adoption and sustainability research"
            })
        
        # 选题3：AI应用
        topic_suggestions.append({
            'title': "Generative AI in Tourism Marketing: Opportunities, Challenges, and Consumer Responses",
            'question': "How do tourists perceive and respond to AI-generated travel content and recommendations?",
            'innovation': "Examines the latest AI technology application in tourism with experimental design",
            'contribution': "Provides first empirical evidence on generative AI's impact on tourism marketing"
        })
        
        # 选题4：研究缺口驱动
        if data['gaps']:
            gap = data['gaps'][0]
            topic_suggestions.append({
                'title': f"Addressing the {gap['title']} in Tourism Research: A Systematic Investigation",
                'question': f"What are the key factors influencing {gap['title'].lower()} and how can they be measured?",
                'innovation': "Directly addresses identified research gap with rigorous methodology",
                'contribution': "Fills important gap identified across multiple recent studies"
            })
        
        for i, topic in enumerate(topic_suggestions, 1):
            suggestions.append(f"### 选题 {i}: {topic['title']}\n")
            suggestions.append(f"**研究问题**: {topic['question']}\n")
            suggestions.append(f"**创新点**: {topic['innovation']}\n")
            suggestions.append(f"**潜在贡献**: {topic['contribution']}\n")
        
        suggestions.append("\n---\n")
        
        # 2. 方法论建议
        suggestions.append("## 2. 方法论建议\n")
        suggestions.append("""
### 2.1 推荐研究设计

**混合方法设计（Mixed-Methods）**：
- 第一阶段：定性探索（深度访谈/焦点小组）→ 构建理论框架
- 第二阶段：定量验证（问卷调查）→ 假设检验
- 第三阶段：大数据分析（文本挖掘）→ 结果三角验证

### 2.2 数据收集方法

**主要数据**：
- 问卷调查：Prolific/MTurk样本（建议N>300）
- 二手数据：TripAdvisor/携程评论数据

**辅助数据**：
- 深度访谈：15-20位旅游从业者或游客
- 实验数据：A/B测试或情境实验

### 2.3 分析技术（可写入方法论）

```
"本研究采用基于Python的多阶段文本挖掘技术（Text Mining），
对Web of Science近三年的XX篇旅游类SSCI论文进行了系统性的
演化路径分析，识别出XX个核心研究主题和XX个潜在研究缺口。
具体而言，我们使用了以下技术栈：
- 数据采集：OpenAlex API自动化文献检索
- 文本预处理：NLTK/spaCy分词、词干提取、命名实体识别
- 主题建模：LDA（Latent Dirichlet Allocation）
- 可视化：NetworkX共现网络分析
"
```

### 2.4 统计工具

- 结构方程模型（SEM）：AMOS/SmartPLS
- 机器学习：Python scikit-learn
- 文本分析：LIWC/Sentiment Analysis
""")
        
        suggestions.append("\n---\n")
        
        # 3. 论文写作指导
        suggestions.append("## 3. 论文写作指导\n")
        suggestions.append("""
### 3.1 方法论部分亮点

**技术含量体现**：
1. 强调"计算方法"（Computational Methods）
2. 使用"大数据"（Big Data）/大样本
3. 展示分析代码片段或流程图
4. 引用最新的方法论文献

**示例段落**：
> "Drawing on computational social science approaches (Lazer et al., 2009), 
> this study employed a multi-stage text mining procedure to analyze 
> [N] academic papers retrieved from Web of Science database..."

### 3.2 理论贡献定位

**三层贡献框架**：
1. **理论层面**：扩展/修正现有理论（如TAM, TPB, S-D Logic）
2. **方法层面**：引入新的研究方法或数据来源
3. **实践层面**：为产业界提供可操作建议

### 3.3 审稿人关注点

| 常见问题 | 应对策略 |
|---------|---------|
| 样本代表性 | 说明样本选择理由，讨论局限性 |
| 因果推断 | 使用纵向设计或工具变量 |
| 理论贡献 | 明确提出命题或修正现有理论 |
| 实践意义 | 添加"Managerial Implications"小节 |
| 方法透明度 | 提供补充材料（数据/代码）|
""")
        
        suggestions.append("\n---\n")
        
        # 4. 发表策略
        suggestions.append("## 4. 发表策略\n")
        suggestions.append("""
### 4.1 目标期刊推荐

**Tier 1 (Impact Factor > 10)**：
- Tourism Management（最推荐）
- Annals of Tourism Research

**Tier 2 (Impact Factor 5-10)**：
- Journal of Travel Research
- International Journal of Hospitality Management
- Journal of Sustainable Tourism

**Tier 3 (Impact Factor 3-5)**：
- Current Issues in Tourism
- Tourism Geographies
- Journal of Destination Marketing & Management

### 4.2 提高接受率建议

1. **预投稿**：先发会议论文（TTRA, ENTER）获取反馈
2. **编辑desk-reject规避**：
   - 严格遵循Author Guidelines
   - 确保研究问题与期刊scope匹配
   - 首页突出理论贡献
3. **Cover Letter策略**：
   - 强调novelty和timeliness
   - 说明与期刊近期论文的关联
4. **修改策略**：
   - R&R后快速响应（2-3周内）
   - 逐条回复审稿意见
   - 使用表格展示修改

### 4.3 时间规划

| 阶段 | 预计时间 |
|------|---------|
| 文献综述 | 1-2个月 |
| 数据收集 | 1-2个月 |
| 数据分析 | 1个月 |
| 写作初稿 | 1个月 |
| 内部审阅 | 2周 |
| 投稿-录用 | 6-12个月 |

**建议总周期**：12-18个月
""")
        
        suggestions.append("\n---\n")
        
        # 5. 基于分析的具体洞察
        suggestions.append("## 5. 基于本次分析的具体洞察\n")
        
        if data['top_keywords']:
            suggestions.append("### 5.1 热门研究主题\n")
            suggestions.append("当前文献中最热门的主题包括：\n")
            for kw, freq in list(data['top_keywords'].items())[:10]:
                suggestions.append(f"- **{kw}** (出现{freq}次)\n")
        
        if data['gaps']:
            suggestions.append("\n### 5.2 识别的研究缺口\n")
            for gap in data['gaps'][:3]:
                suggestions.append(f"- **{gap['title']}**: {gap.get('opportunity', 'N/A')}\n")
        
        if data['future_research']:
            suggestions.append("\n### 5.3 学界呼吁的未来研究方向\n")
            suggestions.append("基于对论文'Future Research'部分的文本挖掘：\n")
            # 提取常见建议
            from collections import Counter
            future_words = Counter()
            for text in data['future_research']:
                words = text.lower().split()
                future_words.update(w for w in words if len(w) > 5)
            
            for word, count in future_words.most_common(10):
                if count >= 2:
                    suggestions.append(f"- '{word}' mentioned in {count} papers\n")
        
        suggestions.append("\n---\n")
        suggestions.append("*报告生成时间：" + __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "*")
        
        return '\n'.join(suggestions)
    
    def _format_keywords(self, keywords: Dict) -> str:
        """格式化关键词"""
        lines = []
        for kw, freq in keywords.items():
            lines.append(f"- {kw}: {freq}")
        return '\n'.join(lines)
    
    def _format_papers(self, papers: List[Dict]) -> str:
        """格式化论文列表"""
        lines = []
        for i, p in enumerate(papers, 1):
            lines.append(f"{i}. [{p.get('citations', 0)} citations] {p.get('title', 'Unknown')}")
        return '\n'.join(lines)
    
    def _format_recent(self, papers: List[Dict]) -> str:
        """格式化最新论文"""
        lines = []
        for i, p in enumerate(papers, 1):
            lines.append(f"{i}. [{p.get('year', 'N/A')}] {p.get('title', 'Unknown')}")
        return '\n'.join(lines)
    
    def _format_list(self, items: List[str]) -> str:
        """格式化列表"""
        lines = []
        for i, item in enumerate(items, 1):
            # 截断过长的文本
            text = item[:200] + '...' if len(item) > 200 else item
            lines.append(f"{i}. \"{text}\"")
        return '\n'.join(lines)
    
    def _format_gaps(self, gaps: List[Dict]) -> str:
        """格式化研究缺口"""
        if not gaps:
            return "No specific gaps identified."
        
        lines = []
        for gap in gaps:
            lines.append(f"- **{gap['title']}**: {gap.get('description', 'N/A')[:100]}...")
        return '\n'.join(lines)
    
    def save_suggestions(self, suggestions: str, filepath: str):
        """保存建议到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(suggestions)
        logger.info(f"AI建议已保存至: {filepath}")
    
    def interactive_qa(self, papers: List[Dict]) -> None:
        """交互式问答（如果有API）"""
        if not self.has_api:
            print("交互式问答需要配置Anthropic API Key")
            return
        
        print("\n" + "=" * 50)
        print("AI研究顾问 - 交互模式")
        print("输入'quit'退出")
        print("=" * 50 + "\n")
        
        # 构建上下文
        context = self._build_context(papers)
        
        while True:
            question = input("\n你的问题: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("再见！")
                break
            
            if not question:
                continue
            
            try:
                message = self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=2000,
                    system=f"""你是一位资深的旅游学SSCI期刊编辑和学术研究顾问。
                    
以下是基于{len(papers)}篇论文的分析数据：
{context}

请基于这些数据回答用户的问题，提供专业、具体、可操作的建议。用中文回答。""",
                    messages=[
                        {"role": "user", "content": question}
                    ]
                )
                
                print("\n" + "-" * 40)
                print(message.content[0].text)
                print("-" * 40)
                
            except Exception as e:
                print(f"Error: {e}")
    
    def _build_context(self, papers: List[Dict]) -> str:
        """构建上下文摘要"""
        keyword_freq = Counter()
        for p in papers:
            keywords = p.get('all_keywords', p.get('keywords', []))
            keyword_freq.update(keywords)
        
        top_kws = dict(keyword_freq.most_common(20))
        
        years = [p.get('year') for p in papers if p.get('year')]
        year_range = f"{min(years)}-{max(years)}" if years else "N/A"
        
        return f"""
- 论文数量: {len(papers)}
- 年份范围: {year_range}
- Top关键词: {', '.join(list(top_kws.keys())[:15])}
"""
