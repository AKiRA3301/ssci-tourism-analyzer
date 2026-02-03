"""
可视化模块
生成各类分析图表
"""

import logging
import os
from typing import List, Dict, Optional
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)


class Visualizer:
    """数据可视化器"""
    
    def __init__(self, output_dir: str = 'output'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 检查matplotlib是否可用
        self.plt = None
        self.has_matplotlib = False
        try:
            import matplotlib
            matplotlib.use('Agg')  # 非交互式后端
            import matplotlib.pyplot as plt
            self.plt = plt
            self.has_matplotlib = True
            
            # 设置中文字体支持
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'sans-serif']
            plt.rcParams['axes.unicode_minus'] = False
            
        except ImportError:
            logger.warning("matplotlib未安装，将生成文本报告代替图表")
    
    def plot_keyword_trends(self, keyword_stats: Dict[str, int], top_n: int = 30) -> Optional[str]:
        """绘制关键词频率趋势图"""
        if not self.has_matplotlib:
            return self._text_keyword_report(keyword_stats, top_n)
        
        plt = self.plt
        
        # 取Top N关键词
        top_keywords = list(keyword_stats.items())[:top_n]
        keywords = [k for k, _ in top_keywords]
        frequencies = [f for _, f in top_keywords]
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(14, 10))
        
        # 水平条形图
        y_pos = range(len(keywords))
        bars = ax.barh(y_pos, frequencies, color='steelblue', edgecolor='navy', alpha=0.8)
        
        # 添加数值标签
        for bar, freq in zip(bars, frequencies):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                   f'{freq}', va='center', fontsize=9)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(keywords, fontsize=10)
        ax.invert_yaxis()  # 最高频在上
        ax.set_xlabel('Frequency', fontsize=12)
        ax.set_title(f'Top {top_n} Keywords by Frequency', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        filepath = os.path.join(self.output_dir, 'keyword_trends.png')
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"关键词趋势图已保存至: {filepath}")
        return filepath
    
    def _text_keyword_report(self, keyword_stats: Dict[str, int], top_n: int = 30) -> str:
        """生成文本关键词报告"""
        filepath = os.path.join(self.output_dir, 'keyword_trends.txt')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 50 + "\n")
            f.write(f"Top {top_n} Keywords by Frequency\n")
            f.write("=" * 50 + "\n\n")
            
            for i, (kw, freq) in enumerate(list(keyword_stats.items())[:top_n], 1):
                bar = '█' * min(freq, 50)  # ASCII条形图
                f.write(f"{i:2}. {kw:30} | {freq:4} | {bar}\n")
        
        logger.info(f"关键词报告已保存至: {filepath}")
        return filepath
    
    def plot_cooccurrence_network(self, papers: List[Dict], top_n: int = 40) -> Optional[str]:
        """绘制关键词共现网络图"""
        if not self.has_matplotlib:
            return self._text_cooccurrence_report(papers, top_n)
        
        plt = self.plt
        
        try:
            import networkx as nx
        except ImportError:
            logger.warning("networkx未安装，跳过共现网络图")
            return self._text_cooccurrence_report(papers, top_n)
        
        # 构建共现数据
        keyword_freq = Counter()
        cooccurrence = Counter()
        
        for paper in papers:
            keywords = paper.get('all_keywords', paper.get('keywords', []))
            keywords = [k.lower() if isinstance(k, str) else str(k) for k in keywords]
            keyword_freq.update(keywords)
            
            # 共现对
            for i, kw1 in enumerate(keywords):
                for kw2 in keywords[i+1:]:
                    pair = tuple(sorted([kw1, kw2]))
                    cooccurrence[pair] += 1
        
        # 取Top关键词
        top_keywords = set(k for k, _ in keyword_freq.most_common(top_n))
        
        # 构建网络
        G = nx.Graph()
        
        # 添加节点
        for kw in top_keywords:
            G.add_node(kw, size=keyword_freq[kw])
        
        # 添加边（仅限Top关键词之间）
        for (kw1, kw2), weight in cooccurrence.items():
            if kw1 in top_keywords and kw2 in top_keywords and weight >= 2:
                G.add_edge(kw1, kw2, weight=weight)
        
        if len(G.nodes()) == 0:
            logger.warning("网络节点为空，跳过")
            return None
        
        # 绘图
        fig, ax = plt.subplots(figsize=(16, 12))
        
        # 布局
        try:
            pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
        except:
            pos = nx.circular_layout(G)
        
        # 节点大小基于频率
        node_sizes = [G.nodes[n].get('size', 10) * 20 for n in G.nodes()]
        
        # 边宽度基于权重
        edge_weights = [G.edges[e].get('weight', 1) for e in G.edges()]
        max_weight = max(edge_weights) if edge_weights else 1
        edge_widths = [w / max_weight * 3 for w in edge_weights]
        
        # 绘制边
        nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.3, width=edge_widths, edge_color='gray')
        
        # 绘制节点
        nx.draw_networkx_nodes(G, pos, ax=ax, node_size=node_sizes, 
                              node_color='lightblue', edgecolors='navy', linewidths=1.5)
        
        # 绘制标签
        nx.draw_networkx_labels(G, pos, ax=ax, font_size=8, font_weight='bold')
        
        ax.set_title('Keyword Co-occurrence Network', fontsize=14, fontweight='bold')
        ax.axis('off')
        
        plt.tight_layout()
        
        filepath = os.path.join(self.output_dir, 'cooccurrence_network.png')
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"共现网络图已保存至: {filepath}")
        return filepath
    
    def _text_cooccurrence_report(self, papers: List[Dict], top_n: int = 40) -> str:
        """生成文本共现报告"""
        # 构建共现数据
        cooccurrence = Counter()
        
        for paper in papers:
            keywords = paper.get('all_keywords', paper.get('keywords', []))
            keywords = [k.lower() if isinstance(k, str) else str(k) for k in keywords]
            
            for i, kw1 in enumerate(keywords):
                for kw2 in keywords[i+1:]:
                    pair = tuple(sorted([kw1, kw2]))
                    cooccurrence[pair] += 1
        
        filepath = os.path.join(self.output_dir, 'cooccurrence_network.txt')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("Keyword Co-occurrence Analysis\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("Top Co-occurring Keyword Pairs:\n\n")
            for (kw1, kw2), freq in cooccurrence.most_common(50):
                f.write(f"  {kw1} <-> {kw2}: {freq}\n")
        
        logger.info(f"共现报告已保存至: {filepath}")
        return filepath
    
    def plot_yearly_heatmap(self, papers: List[Dict], top_n: int = 20) -> Optional[str]:
        """绘制年度关键词热力图"""
        if not self.has_matplotlib:
            return self._text_yearly_report(papers, top_n)
        
        plt = self.plt
        
        # 按年份和关键词统计
        yearly_keywords = defaultdict(Counter)
        
        for paper in papers:
            year = paper.get('year')
            if not year:
                continue
            
            keywords = paper.get('all_keywords', paper.get('keywords', []))
            keywords = [k.lower() if isinstance(k, str) else str(k) for k in keywords]
            yearly_keywords[year].update(keywords)
        
        if not yearly_keywords:
            logger.warning("无年份数据，跳过热力图")
            return None
        
        # 获取所有年份和Top关键词
        years = sorted(yearly_keywords.keys())
        
        # 统计总频率找Top关键词
        total_freq = Counter()
        for year_data in yearly_keywords.values():
            total_freq.update(year_data)
        
        top_keywords = [k for k, _ in total_freq.most_common(top_n)]
        
        # 构建矩阵
        matrix = []
        for kw in top_keywords:
            row = [yearly_keywords[year].get(kw, 0) for year in years]
            matrix.append(row)
        
        # 绘制热力图
        fig, ax = plt.subplots(figsize=(12, 10))
        
        im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto')
        
        # 标签
        ax.set_xticks(range(len(years)))
        ax.set_xticklabels(years, rotation=45, ha='right')
        ax.set_yticks(range(len(top_keywords)))
        ax.set_yticklabels(top_keywords)
        
        # 添加数值
        for i in range(len(top_keywords)):
            for j in range(len(years)):
                value = matrix[i][j]
                if value > 0:
                    color = 'white' if value > max(max(row) for row in matrix) * 0.5 else 'black'
                    ax.text(j, i, str(value), ha='center', va='center', color=color, fontsize=8)
        
        ax.set_xlabel('Year', fontsize=12)
        ax.set_ylabel('Keyword', fontsize=12)
        ax.set_title(f'Keyword Frequency by Year (Top {top_n})', fontsize=14, fontweight='bold')
        
        # 颜色条
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Frequency', fontsize=10)
        
        plt.tight_layout()
        
        filepath = os.path.join(self.output_dir, 'yearly_heatmap.png')
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"年度热力图已保存至: {filepath}")
        return filepath
    
    def _text_yearly_report(self, papers: List[Dict], top_n: int = 20) -> str:
        """生成文本年度报告"""
        yearly_keywords = defaultdict(Counter)
        
        for paper in papers:
            year = paper.get('year')
            if not year:
                continue
            
            keywords = paper.get('all_keywords', paper.get('keywords', []))
            yearly_keywords[year].update(keywords)
        
        filepath = os.path.join(self.output_dir, 'yearly_heatmap.txt')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("Yearly Keyword Analysis\n")
            f.write("=" * 60 + "\n\n")
            
            for year in sorted(yearly_keywords.keys()):
                f.write(f"\n{year}:\n")
                f.write("-" * 40 + "\n")
                for kw, freq in yearly_keywords[year].most_common(top_n):
                    f.write(f"  {kw}: {freq}\n")
        
        logger.info(f"年度报告已保存至: {filepath}")
        return filepath
    
    def plot_topic_distribution(self, topics: List[Dict]) -> Optional[str]:
        """绘制主题分布图"""
        if not self.has_matplotlib or not topics:
            return self._text_topic_report(topics)
        
        plt = self.plt
        
        # 准备数据
        labels = [t['label'] for t in topics]
        sizes = [t.get('document_count', 1) for t in topics]
        
        # 饼图
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # 饼图
        colors = plt.cm.Set3(range(len(labels)))
        wedges, texts, autotexts = ax1.pie(sizes, labels=labels, colors=colors,
                                           autopct='%1.1f%%', startangle=90)
        ax1.set_title('Topic Distribution', fontsize=14, fontweight='bold')
        
        # 条形图 - 每个主题的关键词
        topic_keywords = []
        topic_labels = []
        for t in topics:
            kws = t['keywords'][:5]  # 前5个关键词
            topic_keywords.append(', '.join(kws))
            topic_labels.append(t['label'])
        
        y_pos = range(len(topic_labels))
        ax2.barh(y_pos, sizes, color=colors)
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels([f"{l}\n({k})" for l, k in zip(topic_labels, topic_keywords)], fontsize=9)
        ax2.set_xlabel('Document Count', fontsize=12)
        ax2.set_title('Topics with Keywords', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        filepath = os.path.join(self.output_dir, 'topic_distribution.png')
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"主题分布图已保存至: {filepath}")
        return filepath
    
    def _text_topic_report(self, topics: List[Dict]) -> str:
        """生成文本主题报告"""
        filepath = os.path.join(self.output_dir, 'topic_distribution.txt')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("Topic Distribution\n")
            f.write("=" * 60 + "\n\n")
            
            if topics:
                total = sum(t.get('document_count', 1) for t in topics)
                for t in topics:
                    count = t.get('document_count', 1)
                    pct = count / total * 100 if total else 0
                    f.write(f"\n{t['label']}:\n")
                    f.write(f"  Documents: {count} ({pct:.1f}%)\n")
                    f.write(f"  Keywords: {', '.join(t['keywords'][:8])}\n")
            else:
                f.write("No topics identified.\n")
        
        logger.info(f"主题报告已保存至: {filepath}")
        return filepath
    
    def plot_citation_analysis(self, papers: List[Dict]) -> Optional[str]:
        """绘制引用分析图"""
        if not self.has_matplotlib:
            return self._text_citation_report(papers)
        
        plt = self.plt
        
        # 收集引用数据
        citations = [p.get('citations', 0) for p in papers if p.get('citations', 0) > 0]
        years = [p.get('year') for p in papers if p.get('year')]
        
        if not citations or not years:
            logger.warning("无引用数据，跳过")
            return None
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 12))
        
        # 1. 引用分布直方图
        ax1 = axes[0, 0]
        ax1.hist(citations, bins=30, color='steelblue', edgecolor='navy', alpha=0.7)
        ax1.set_xlabel('Citations')
        ax1.set_ylabel('Number of Papers')
        ax1.set_title('Citation Distribution')
        ax1.axvline(x=sum(citations)/len(citations), color='red', linestyle='--', label=f'Mean: {sum(citations)/len(citations):.1f}')
        ax1.legend()
        
        # 2. 按年份的平均引用
        ax2 = axes[0, 1]
        year_citations = defaultdict(list)
        for p in papers:
            if p.get('year') and p.get('citations') is not None:
                year_citations[p['year']].append(p['citations'])
        
        years_sorted = sorted(year_citations.keys())
        avg_cites = [sum(year_citations[y])/len(year_citations[y]) for y in years_sorted]
        
        ax2.bar(years_sorted, avg_cites, color='coral', edgecolor='darkred')
        ax2.set_xlabel('Year')
        ax2.set_ylabel('Average Citations')
        ax2.set_title('Average Citations by Year')
        
        # 3. 期刊引用比较
        ax3 = axes[1, 0]
        journal_citations = defaultdict(list)
        for p in papers:
            journal = p.get('journal', 'Unknown')
            if journal and p.get('citations') is not None:
                journal_citations[journal].append(p['citations'])
        
        # 取Top 10期刊
        journal_avg = {j: sum(c)/len(c) for j, c in journal_citations.items() if len(c) >= 2}
        top_journals = sorted(journal_avg.items(), key=lambda x: -x[1])[:10]
        
        if top_journals:
            journals = [j[:20] for j, _ in top_journals]  # 截断长名称
            avgs = [a for _, a in top_journals]
            ax3.barh(range(len(journals)), avgs, color='lightgreen', edgecolor='darkgreen')
            ax3.set_yticks(range(len(journals)))
            ax3.set_yticklabels(journals, fontsize=9)
            ax3.set_xlabel('Average Citations')
            ax3.set_title('Top 10 Journals by Avg Citations')
        
        # 4. 高被引论文
        ax4 = axes[1, 1]
        top_papers = sorted(papers, key=lambda x: x.get('citations', 0), reverse=True)[:10]
        
        titles = [p.get('title', 'Unknown')[:40] + '...' if len(p.get('title', '')) > 40 else p.get('title', 'Unknown') for p in top_papers]
        cites = [p.get('citations', 0) for p in top_papers]
        
        ax4.barh(range(len(titles)), cites, color='gold', edgecolor='orange')
        ax4.set_yticks(range(len(titles)))
        ax4.set_yticklabels(titles, fontsize=8)
        ax4.set_xlabel('Citations')
        ax4.set_title('Top 10 Most Cited Papers')
        ax4.invert_yaxis()
        
        plt.tight_layout()
        
        filepath = os.path.join(self.output_dir, 'citation_analysis.png')
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"引用分析图已保存至: {filepath}")
        return filepath
    
    def _text_citation_report(self, papers: List[Dict]) -> str:
        """生成文本引用报告"""
        filepath = os.path.join(self.output_dir, 'citation_analysis.txt')
        
        citations = [p.get('citations', 0) for p in papers]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("Citation Analysis\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Total papers: {len(papers)}\n")
            f.write(f"Total citations: {sum(citations)}\n")
            f.write(f"Average citations: {sum(citations)/len(citations):.2f}\n")
            f.write(f"Max citations: {max(citations)}\n\n")
            
            f.write("Top 10 Most Cited Papers:\n")
            f.write("-" * 40 + "\n")
            
            top_papers = sorted(papers, key=lambda x: x.get('citations', 0), reverse=True)[:10]
            for i, p in enumerate(top_papers, 1):
                f.write(f"{i}. [{p.get('citations', 0)}] {p.get('title', 'Unknown')[:60]}...\n")
        
        logger.info(f"引用报告已保存至: {filepath}")
        return filepath
    
    def create_summary_dashboard(self, papers: List[Dict], keyword_stats: Dict,
                                 topics: List[Dict], gaps: List[Dict]) -> str:
        """创建汇总仪表板"""
        if not self.has_matplotlib:
            return self._text_summary_report(papers, keyword_stats, topics, gaps)
        
        plt = self.plt
        
        fig = plt.figure(figsize=(20, 16))
        
        # 标题
        fig.suptitle('SSCI Tourism Research Trend Analysis Dashboard', fontsize=18, fontweight='bold', y=0.98)
        
        # 1. 数据概览（文本）
        ax1 = fig.add_subplot(3, 3, 1)
        ax1.axis('off')
        
        summary_text = f"""
        Data Overview
        ─────────────
        Total Papers: {len(papers)}
        Unique Keywords: {len(keyword_stats)}
        Research Topics: {len(topics)}
        Research Gaps: {len(gaps)}
        
        Year Range: {min(p.get('year', 9999) for p in papers if p.get('year'))} - 
                   {max(p.get('year', 0) for p in papers if p.get('year'))}
        """
        ax1.text(0.1, 0.5, summary_text, fontsize=11, fontfamily='monospace',
                verticalalignment='center', transform=ax1.transAxes)
        
        # 2. Top关键词
        ax2 = fig.add_subplot(3, 3, 2)
        top_kws = list(keyword_stats.items())[:15]
        kws = [k for k, _ in top_kws]
        freqs = [f for _, f in top_kws]
        ax2.barh(range(len(kws)), freqs, color='steelblue')
        ax2.set_yticks(range(len(kws)))
        ax2.set_yticklabels(kws, fontsize=8)
        ax2.invert_yaxis()
        ax2.set_title('Top 15 Keywords', fontsize=12)
        
        # 3. 年度趋势
        ax3 = fig.add_subplot(3, 3, 3)
        year_count = Counter(p.get('year') for p in papers if p.get('year'))
        years = sorted(year_count.keys())
        counts = [year_count[y] for y in years]
        ax3.plot(years, counts, 'o-', color='coral', linewidth=2, markersize=8)
        ax3.fill_between(years, counts, alpha=0.3, color='coral')
        ax3.set_xlabel('Year')
        ax3.set_ylabel('Publications')
        ax3.set_title('Publications per Year', fontsize=12)
        
        # 4-6. 主题分布
        if topics:
            ax4 = fig.add_subplot(3, 3, 4)
            labels = [t['label'][:15] for t in topics]
            sizes = [t.get('document_count', 1) for t in topics]
            colors = plt.cm.Set3(range(len(labels)))
            ax4.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', textprops={'fontsize': 8})
            ax4.set_title('Topic Distribution', fontsize=12)
        
        # 5. 研究缺口
        ax5 = fig.add_subplot(3, 3, 5)
        ax5.axis('off')
        
        gap_text = "Research Gaps Identified\n" + "─" * 25 + "\n\n"
        for g in gaps[:4]:
            gap_text += f"• {g['title']}\n"
        ax5.text(0.1, 0.5, gap_text, fontsize=10, verticalalignment='center',
                transform=ax5.transAxes)
        
        # 6. 引用统计
        ax6 = fig.add_subplot(3, 3, 6)
        citations = [p.get('citations', 0) for p in papers if p.get('citations', 0) > 0]
        if citations:
            ax6.hist(citations, bins=20, color='lightgreen', edgecolor='darkgreen')
            ax6.axvline(x=sum(citations)/len(citations), color='red', linestyle='--')
            ax6.set_xlabel('Citations')
            ax6.set_ylabel('Count')
            ax6.set_title('Citation Distribution', fontsize=12)
        
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        filepath = os.path.join(self.output_dir, 'summary_dashboard.png')
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"汇总仪表板已保存至: {filepath}")
        return filepath
    
    def _text_summary_report(self, papers: List[Dict], keyword_stats: Dict,
                            topics: List[Dict], gaps: List[Dict]) -> str:
        """生成文本汇总报告"""
        filepath = os.path.join(self.output_dir, 'summary_dashboard.txt')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("SSCI Tourism Research Trend Analysis Summary\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Total Papers: {len(papers)}\n")
            f.write(f"Unique Keywords: {len(keyword_stats)}\n")
            f.write(f"Research Topics: {len(topics)}\n")
            f.write(f"Research Gaps: {len(gaps)}\n\n")
            
            f.write("Top Keywords:\n")
            for kw, freq in list(keyword_stats.items())[:15]:
                f.write(f"  {kw}: {freq}\n")
        
        logger.info(f"汇总报告已保存至: {filepath}")
        return filepath
