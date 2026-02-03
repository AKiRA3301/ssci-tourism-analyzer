"""
趋势分析模块
包含关键词分析、突发词检测、LDA主题建模、研究缺口识别等功能
"""

import logging
from typing import List, Dict, Tuple, Optional
from collections import Counter, defaultdict
import math
import json

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """学术趋势分析器"""
    
    def __init__(self, n_topics: int = 8):
        self.n_topics = n_topics
    
    def analyze_keywords(self, papers: List[Dict]) -> Dict[str, int]:
        """
        分析关键词频率
        
        Returns:
            按频率排序的关键词字典
        """
        keyword_counter = Counter()
        
        for paper in papers:
            # 合并所有关键词来源
            keywords = set()
            
            if paper.get('all_keywords'):
                keywords.update(paper['all_keywords'])
            elif paper.get('keywords_normalized'):
                keywords.update(paper['keywords_normalized'])
            elif paper.get('keywords'):
                keywords.update(k.lower() for k in paper['keywords'])
            
            keyword_counter.update(keywords)
        
        # 按频率排序
        sorted_keywords = dict(keyword_counter.most_common())
        
        logger.info(f"分析了 {len(sorted_keywords)} 个唯一关键词")
        return sorted_keywords
    
    def analyze_keywords_by_year(self, papers: List[Dict]) -> Dict[int, Dict[str, int]]:
        """按年份分析关键词频率"""
        yearly_keywords = defaultdict(Counter)
        
        for paper in papers:
            year = paper.get('year')
            if not year:
                continue
            
            keywords = set()
            if paper.get('all_keywords'):
                keywords.update(paper['all_keywords'])
            elif paper.get('keywords'):
                keywords.update(k.lower() for k in paper['keywords'])
            
            yearly_keywords[year].update(keywords)
        
        # 转换为普通字典并排序
        result = {}
        for year in sorted(yearly_keywords.keys()):
            result[year] = dict(yearly_keywords[year].most_common())
        
        return result
    
    def detect_burst_words(self, papers: List[Dict], window: int = 1) -> List[Dict]:
        """
        检测突发词（Burst Words）
        
        突发词是指在短时间内出现频率急剧增加的词汇，
        通常代表新兴研究热点。
        
        Args:
            papers: 论文列表
            window: 时间窗口（年）
        
        Returns:
            突发词列表，包含增长率等信息
        """
        # 按年份统计关键词
        yearly_keywords = self.analyze_keywords_by_year(papers)
        
        if len(yearly_keywords) < 2:
            logger.warning("数据年份不足，无法检测突发词")
            return []
        
        years = sorted(yearly_keywords.keys())
        recent_years = years[-2:]  # 最近两年
        earlier_years = years[:-2] if len(years) > 2 else years[:1]
        
        # 计算增长率
        burst_words = []
        
        # 获取最近年份的关键词
        recent_keywords = Counter()
        for year in recent_years:
            recent_keywords.update(yearly_keywords.get(year, {}))
        
        # 获取较早年份的关键词
        earlier_keywords = Counter()
        for year in earlier_years:
            earlier_keywords.update(yearly_keywords.get(year, {}))
        
        # 计算每个关键词的增长率
        for keyword, recent_freq in recent_keywords.items():
            earlier_freq = earlier_keywords.get(keyword, 0)
            
            # 计算增长率（使用平滑处理避免除零）
            if earlier_freq == 0:
                # 新出现的词
                growth_rate = float('inf') if recent_freq >= 3 else recent_freq
                is_new = True
            else:
                growth_rate = (recent_freq - earlier_freq) / earlier_freq
                is_new = False
            
            # 只关注显著增长的词（增长率 > 50% 或新出现频率 >= 3）
            if growth_rate > 0.5 or (is_new and recent_freq >= 3):
                burst_words.append({
                    'keyword': keyword,
                    'recent_freq': recent_freq,
                    'earlier_freq': earlier_freq,
                    'growth_rate': growth_rate if growth_rate != float('inf') else 10.0,  # 归一化无穷大
                    'is_new': is_new,
                    'trend': 'rising'
                })
        
        # 按增长率排序
        burst_words.sort(key=lambda x: (-x['growth_rate'], -x['recent_freq']))
        
        logger.info(f"检测到 {len(burst_words)} 个突发词")
        return burst_words
    
    def lda_topic_modeling(self, papers: List[Dict]) -> List[Dict]:
        """
        LDA主题建模
        
        由于避免依赖重型库，这里实现一个简化版的主题提取
        基于关键词共现和聚类
        """
        # 收集所有文档的关键词
        documents = []
        for paper in papers:
            keywords = set()
            if paper.get('all_keywords'):
                keywords.update(paper['all_keywords'])
            if paper.get('abstract_tokens'):
                keywords.update(paper['abstract_tokens'][:20])  # 取前20个token
            documents.append(list(keywords))
        
        # 计算词频
        word_freq = Counter()
        for doc in documents:
            word_freq.update(doc)
        
        # 过滤低频词
        min_freq = max(2, len(documents) * 0.01)  # 至少出现在1%的文档中
        valid_words = {w for w, f in word_freq.items() if f >= min_freq}
        
        # 构建共现矩阵
        cooccurrence = defaultdict(Counter)
        for doc in documents:
            doc_words = [w for w in doc if w in valid_words]
            for i, w1 in enumerate(doc_words):
                for w2 in doc_words[i+1:]:
                    cooccurrence[w1][w2] += 1
                    cooccurrence[w2][w1] += 1
        
        # 简单聚类：基于共现关系分组
        used_words = set()
        topics = []
        
        # 按频率排序的种子词
        seed_words = sorted(valid_words, key=lambda w: -word_freq[w])
        
        for seed in seed_words:
            if seed in used_words:
                continue
            if len(topics) >= self.n_topics:
                break
            
            # 找出与种子词共现最多的词
            related = cooccurrence[seed].most_common(20)
            topic_words = [seed]
            
            for word, _ in related:
                if word not in used_words and len(topic_words) < 15:
                    topic_words.append(word)
            
            if len(topic_words) >= 3:
                topics.append({
                    'id': len(topics) + 1,
                    'keywords': topic_words,
                    'label': self._generate_topic_label(topic_words),
                    'description': self._generate_topic_description(topic_words),
                    'document_count': self._count_topic_documents(documents, topic_words)
                })
                used_words.update(topic_words)
        
        logger.info(f"识别出 {len(topics)} 个研究主题")
        return topics
    
    def _generate_topic_label(self, keywords: List[str]) -> str:
        """生成主题标签"""
        # 简单策略：使用前两个关键词
        if len(keywords) >= 2:
            return f"{keywords[0].title()} & {keywords[1].title()}"
        elif keywords:
            return keywords[0].title()
        return "Unknown Topic"
    
    def _generate_topic_description(self, keywords: List[str]) -> str:
        """生成主题描述"""
        if len(keywords) >= 5:
            return f"This topic focuses on {keywords[0]}, exploring its relationship with {keywords[1]}, {keywords[2]}, and related concepts such as {keywords[3]} and {keywords[4]}."
        elif len(keywords) >= 3:
            return f"This topic examines {keywords[0]} in relation to {keywords[1]} and {keywords[2]}."
        else:
            return f"This topic centers on {keywords[0]}."
    
    def _count_topic_documents(self, documents: List[List[str]], topic_keywords: List[str]) -> int:
        """计算包含主题关键词的文档数"""
        topic_set = set(topic_keywords)
        count = 0
        for doc in documents:
            if topic_set & set(doc):  # 有交集
                count += 1
        return count
    
    def build_cooccurrence_network(self, papers: List[Dict], top_n: int = 50) -> Dict:
        """
        构建关键词共现网络
        
        Returns:
            网络数据，包含节点和边
        """
        # 计算词频
        keyword_freq = self.analyze_keywords(papers)
        top_keywords = list(keyword_freq.keys())[:top_n]
        
        # 构建共现矩阵
        cooccurrence = defaultdict(int)
        
        for paper in papers:
            keywords = set()
            if paper.get('all_keywords'):
                keywords.update(paper['all_keywords'])
            elif paper.get('keywords'):
                keywords.update(k.lower() for k in paper['keywords'])
            
            # 过滤到top关键词
            keywords = keywords & set(top_keywords)
            keywords = list(keywords)
            
            # 记录共现
            for i, kw1 in enumerate(keywords):
                for kw2 in keywords[i+1:]:
                    pair = tuple(sorted([kw1, kw2]))
                    cooccurrence[pair] += 1
        
        # 构建网络数据
        nodes = []
        for kw in top_keywords:
            nodes.append({
                'id': kw,
                'label': kw,
                'size': keyword_freq.get(kw, 1)
            })
        
        edges = []
        for (source, target), weight in cooccurrence.items():
            if weight >= 2:  # 至少共现2次
                edges.append({
                    'source': source,
                    'target': target,
                    'weight': weight
                })
        
        # 按权重排序
        edges.sort(key=lambda x: -x['weight'])
        
        return {
            'nodes': nodes,
            'edges': edges[:200]  # 限制边数
        }
    
    def identify_research_gaps(self, papers: List[Dict]) -> List[Dict]:
        """
        识别研究缺口
        
        基于：
        1. 论文中的Limitations部分
        2. Future Research建议
        3. 低频但高被引的主题
        """
        gaps = []
        
        # 1. 从Limitations和Future Research提取
        limitation_themes = Counter()
        future_themes = Counter()
        
        for paper in papers:
            if paper.get('limitations'):
                # 简单提取关键词
                words = paper['limitations'].lower().split()
                limitation_themes.update(w for w in words if len(w) > 4)
            
            if paper.get('future_research'):
                words = paper['future_research'].lower().split()
                future_themes.update(w for w in words if len(w) > 4)
        
        # 2. 找出被多篇论文提到的研究方向
        common_future = [w for w, c in future_themes.most_common(20) if c >= 2]
        common_limitations = [w for w, c in limitation_themes.most_common(20) if c >= 2]
        
        # 3. 分析高被引但低频的关键词组合（潜力选题）
        keyword_citations = defaultdict(list)
        keyword_freq = Counter()
        
        for paper in papers:
            citations = paper.get('citations', 0)
            keywords = paper.get('all_keywords', paper.get('keywords', []))
            
            for kw in keywords:
                kw = kw.lower() if isinstance(kw, str) else str(kw)
                keyword_citations[kw].append(citations)
                keyword_freq[kw] += 1
        
        # 计算每个关键词的平均被引
        high_impact_low_freq = []
        for kw, cites in keyword_citations.items():
            if len(cites) >= 2:  # 至少出现2次
                avg_cite = sum(cites) / len(cites)
                freq = keyword_freq[kw]
                
                # 高被引(>10)但低频(<5)
                if avg_cite > 10 and freq < 5:
                    high_impact_low_freq.append({
                        'keyword': kw,
                        'avg_citations': avg_cite,
                        'frequency': freq
                    })
        
        high_impact_low_freq.sort(key=lambda x: -x['avg_citations'])
        
        # 4. 构建研究缺口报告
        # Gap 1: 基于Future Research提取
        if common_future:
            gaps.append({
                'id': 1,
                'title': 'Methodological Advancement',
                'description': f"Multiple studies suggest future research should address: {', '.join(common_future[:5])}",
                'source_count': len([p for p in papers if p.get('future_research')]),
                'keywords': common_future[:10],
                'opportunity': "Consider developing new methodological approaches or frameworks addressing these areas."
            })
        
        # Gap 2: 基于Limitations提取
        if common_limitations:
            gaps.append({
                'id': 2,
                'title': 'Addressing Current Limitations',
                'description': f"Common limitations across studies include: {', '.join(common_limitations[:5])}",
                'source_count': len([p for p in papers if p.get('limitations')]),
                'keywords': common_limitations[:10],
                'opportunity': "Design studies that specifically overcome these common methodological limitations."
            })
        
        # Gap 3: 高被引低频主题
        if high_impact_low_freq:
            top_potential = high_impact_low_freq[:5]
            gaps.append({
                'id': 3,
                'title': 'High-Impact Underexplored Topics',
                'description': f"Topics with high citation impact but low publication frequency: {', '.join(t['keyword'] for t in top_potential)}",
                'source_count': sum(t['frequency'] for t in top_potential),
                'keywords': [t['keyword'] for t in top_potential],
                'opportunity': "These topics show high academic interest but limited coverage - prime opportunities for new contributions.",
                'potential_topics': top_potential
            })
        
        # Gap 4: 新兴技术应用
        emerging_tech = ['generative ai', 'chatgpt', 'llm', 'metaverse', 'blockchain', 'iot', 'digital twin']
        tech_gaps = []
        for tech in emerging_tech:
            freq = keyword_freq.get(tech, 0)
            if freq < 10:  # 如果该技术在旅游研究中还不够普及
                tech_gaps.append(tech)
        
        if tech_gaps:
            gaps.append({
                'id': 4,
                'title': 'Emerging Technology Applications',
                'description': f"Cutting-edge technologies with limited tourism research coverage: {', '.join(tech_gaps[:5])}",
                'source_count': sum(keyword_freq.get(t, 0) for t in tech_gaps),
                'keywords': tech_gaps,
                'opportunity': "Apply these emerging technologies to tourism contexts for innovative research contributions."
            })
        
        logger.info(f"识别出 {len(gaps)} 个研究缺口")
        return gaps
    
    def calculate_h_index(self, papers: List[Dict]) -> int:
        """计算h-index（基于论文被引）"""
        citations = sorted([p.get('citations', 0) for p in papers], reverse=True)
        
        h = 0
        for i, c in enumerate(citations):
            if c >= i + 1:
                h = i + 1
            else:
                break
        
        return h
    
    def get_citation_statistics(self, papers: List[Dict]) -> Dict:
        """获取引用统计"""
        citations = [p.get('citations', 0) for p in papers]
        
        if not citations:
            return {}
        
        total = sum(citations)
        count = len(citations)
        
        return {
            'total_citations': total,
            'paper_count': count,
            'mean_citations': total / count if count else 0,
            'median_citations': sorted(citations)[count // 2] if count else 0,
            'max_citations': max(citations),
            'h_index': self.calculate_h_index(papers),
            'highly_cited_papers': sum(1 for c in citations if c > 50),  # 被引>50的论文数
        }
    
    def save_keyword_stats(self, stats: Dict[str, int], filepath: str):
        """保存关键词统计"""
        with open(filepath, 'w', encoding='utf-8-sig') as f:
            f.write('Keyword,Frequency\n')
            for kw, freq in stats.items():
                f.write(f'"{kw}",{freq}\n')
        logger.info(f"关键词统计已保存至: {filepath}")
    
    def save_burst_words(self, burst_words: List[Dict], filepath: str):
        """保存突发词"""
        with open(filepath, 'w', encoding='utf-8-sig') as f:
            f.write('Keyword,Recent_Freq,Earlier_Freq,Growth_Rate,Is_New,Trend\n')
            for bw in burst_words:
                f.write(f'"{bw["keyword"]}",{bw["recent_freq"]},{bw["earlier_freq"]},{bw["growth_rate"]:.2f},{bw["is_new"]},{bw["trend"]}\n')
        logger.info(f"突发词已保存至: {filepath}")
    
    def save_topics(self, topics: List[Dict], filepath: str):
        """保存LDA主题"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("LDA Topic Modeling Results\n")
            f.write("=" * 60 + "\n\n")
            
            for topic in topics:
                f.write(f"Topic {topic['id']}: {topic['label']}\n")
                f.write("-" * 40 + "\n")
                f.write(f"Keywords: {', '.join(topic['keywords'])}\n")
                f.write(f"Document Count: {topic['document_count']}\n")
                f.write(f"Description: {topic['description']}\n")
                f.write("\n")
        
        logger.info(f"LDA主题已保存至: {filepath}")
    
    def save_gaps(self, gaps: List[Dict], filepath: str):
        """保存研究缺口"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("Research Gap Analysis\n")
            f.write("=" * 60 + "\n\n")
            
            for gap in gaps:
                f.write(f"Gap {gap['id']}: {gap['title']}\n")
                f.write("-" * 40 + "\n")
                f.write(f"Description: {gap['description']}\n")
                f.write(f"Source Count: {gap['source_count']}\n")
                f.write(f"Keywords: {', '.join(gap.get('keywords', []))}\n")
                f.write(f"Opportunity: {gap['opportunity']}\n")
                f.write("\n")
        
        logger.info(f"研究缺口已保存至: {filepath}")
