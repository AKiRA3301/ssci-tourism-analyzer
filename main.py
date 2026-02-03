#!/usr/bin/env python3
"""
SSCI Tourism Academic Trend Analysis System
旅游学术趋势分析系统 v2.0

功能：
1. 通过合法API获取学术论文数据（OpenAlex、Semantic Scholar、Crossref）
2. 导入WoS/Scopus手动导出的文件
3. 文本预处理与NLP分析
4. 关键词共现网络、LDA主题建模
5. 可视化分析
6. AI辅助研究缺口识别与选题建议

作者：Claude AI Assistant
"""

import os
import sys

# 添加模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.data_fetcher import DataFetcher
from modules.file_importer import FileImporter
from modules.text_processor import TextProcessor
from modules.analyzer import TrendAnalyzer
from modules.visualizer import Visualizer
from modules.ai_advisor import AIAdvisor
from modules.utils import setup_logging, print_banner

import argparse
import logging

def main():
    """主程序入口"""
    print_banner()
    
    parser = argparse.ArgumentParser(
        description='SSCI Tourism Academic Trend Analysis System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 从OpenAlex获取数据并分析
  python main.py --fetch --keywords "generative AI tourism" --years 2024-2026
  
  # 导入WoS导出文件
  python main.py --import-wos savedrecs.txt
  
  # 导入Scopus导出文件  
  python main.py --import-scopus scopus.csv
  
  # 完整分析流程
  python main.py --analyze --output results/
  
  # AI辅助选题建议
  python main.py --ai-suggest --focus "virtual reality tourism"
        """
    )
    
    # 数据获取参数
    fetch_group = parser.add_argument_group('数据获取')
    fetch_group.add_argument('--fetch', action='store_true', help='从开放API获取数据')
    fetch_group.add_argument('--keywords', type=str, help='搜索关键词（用逗号分隔）')
    fetch_group.add_argument('--years', type=str, default='2024-2026', help='年份范围（如2024-2026）')
    fetch_group.add_argument('--max-results', type=int, default=500, help='最大获取数量')
    
    # 文件导入参数
    import_group = parser.add_argument_group('文件导入')
    import_group.add_argument('--import-wos', type=str, help='导入WoS导出文件路径')
    import_group.add_argument('--import-scopus', type=str, help='导入Scopus导出文件路径')
    import_group.add_argument('--import-csv', type=str, help='导入通用CSV文件')
    
    # 分析参数
    analysis_group = parser.add_argument_group('分析选项')
    analysis_group.add_argument('--analyze', action='store_true', help='执行完整分析')
    analysis_group.add_argument('--lda-topics', type=int, default=8, help='LDA主题数量')
    analysis_group.add_argument('--top-keywords', type=int, default=50, help='显示Top N关键词')
    
    # AI辅助
    ai_group = parser.add_argument_group('AI辅助')
    ai_group.add_argument('--ai-suggest', action='store_true', help='AI辅助选题建议')
    ai_group.add_argument('--focus', type=str, help='研究聚焦方向')
    ai_group.add_argument('--api-key', type=str, help='Anthropic API Key（可选）')
    
    # 输出参数
    output_group = parser.add_argument_group('输出选项')
    output_group.add_argument('--output', type=str, default='output/', help='输出目录')
    output_group.add_argument('--format', choices=['csv', 'excel', 'json'], default='csv', help='输出格式')
    output_group.add_argument('--no-viz', action='store_true', help='不生成可视化图表')
    
    # 其他
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    parser.add_argument('--interactive', '-i', action='store_true', help='交互模式')
    
    args = parser.parse_args()
    
    # 设置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    logger = logging.getLogger(__name__)
    
    # 创建输出目录
    os.makedirs(args.output, exist_ok=True)
    
    # 初始化组件
    fetcher = DataFetcher()
    importer = FileImporter()
    processor = TextProcessor()
    analyzer = TrendAnalyzer(n_topics=args.lda_topics)
    visualizer = Visualizer(output_dir=args.output)
    advisor = AIAdvisor(api_key=args.api_key)
    
    papers = []
    
    # 交互模式
    if args.interactive:
        run_interactive_mode(fetcher, importer, processor, analyzer, visualizer, advisor, args.output)
        return
    
    # 数据获取
    if args.fetch:
        if not args.keywords:
            logger.error("请使用 --keywords 指定搜索关键词")
            return
        
        keywords = [k.strip() for k in args.keywords.split(',')]
        year_start, year_end = map(int, args.years.split('-'))
        
        logger.info(f"正在获取数据: 关键词={keywords}, 年份={year_start}-{year_end}")
        papers = fetcher.fetch_papers(
            keywords=keywords,
            year_start=year_start,
            year_end=year_end,
            max_results=args.max_results
        )
        logger.info(f"获取到 {len(papers)} 篇论文")
    
    # 文件导入
    if args.import_wos:
        logger.info(f"导入WoS文件: {args.import_wos}")
        imported = importer.import_wos(args.import_wos)
        papers.extend(imported)
        logger.info(f"导入 {len(imported)} 篇论文")
    
    if args.import_scopus:
        logger.info(f"导入Scopus文件: {args.import_scopus}")
        imported = importer.import_scopus(args.import_scopus)
        papers.extend(imported)
        logger.info(f"导入 {len(imported)} 篇论文")
    
    if args.import_csv:
        logger.info(f"导入CSV文件: {args.import_csv}")
        imported = importer.import_csv(args.import_csv)
        papers.extend(imported)
        logger.info(f"导入 {len(imported)} 篇论文")
    
    if not papers:
        logger.warning("没有数据可分析。请使用 --fetch 获取数据或 --import-* 导入文件")
        if not args.interactive:
            # 生成演示数据
            logger.info("生成演示数据以展示系统功能...")
            papers = fetcher.generate_demo_data()
    
    # 文本预处理
    logger.info("正在进行文本预处理...")
    processed_papers = processor.process_papers(papers)
    
    # 保存处理后的数据
    output_file = os.path.join(args.output, f'processed_papers.{args.format}')
    processor.save_to_file(processed_papers, output_file, format=args.format)
    logger.info(f"数据已保存至: {output_file}")
    
    # 执行分析
    if args.analyze or True:  # 默认执行分析
        logger.info("正在执行趋势分析...")
        
        # 关键词分析
        keyword_stats = analyzer.analyze_keywords(processed_papers)
        analyzer.save_keyword_stats(keyword_stats, os.path.join(args.output, 'keyword_analysis.csv'))
        
        # 突发词检测
        burst_words = analyzer.detect_burst_words(processed_papers)
        analyzer.save_burst_words(burst_words, os.path.join(args.output, 'burst_words.csv'))
        
        # LDA主题建模
        topics = analyzer.lda_topic_modeling(processed_papers)
        analyzer.save_topics(topics, os.path.join(args.output, 'lda_topics.txt'))
        
        # 研究缺口分析
        gaps = analyzer.identify_research_gaps(processed_papers)
        analyzer.save_gaps(gaps, os.path.join(args.output, 'research_gaps.txt'))
        
        # 可视化
        if not args.no_viz:
            logger.info("正在生成可视化图表...")
            visualizer.plot_keyword_trends(keyword_stats)
            visualizer.plot_cooccurrence_network(processed_papers)
            visualizer.plot_yearly_heatmap(processed_papers)
            visualizer.plot_topic_distribution(topics)
            visualizer.plot_citation_analysis(processed_papers)
            logger.info(f"图表已保存至: {args.output}")
    
    # AI辅助建议
    if args.ai_suggest:
        logger.info("正在生成AI辅助选题建议...")
        suggestions = advisor.generate_suggestions(
            papers=processed_papers,
            gaps=gaps if 'gaps' in locals() else None,
            focus_area=args.focus
        )
        advisor.save_suggestions(suggestions, os.path.join(args.output, 'ai_suggestions.md'))
        logger.info(f"AI建议已保存至: {args.output}/ai_suggestions.md")
    
    # 生成综合报告
    logger.info("正在生成综合分析报告...")
    generate_report(
        papers=processed_papers,
        keyword_stats=keyword_stats if 'keyword_stats' in locals() else None,
        burst_words=burst_words if 'burst_words' in locals() else None,
        topics=topics if 'topics' in locals() else None,
        gaps=gaps if 'gaps' in locals() else None,
        output_dir=args.output
    )
    
    logger.info("=" * 60)
    logger.info("分析完成！")
    logger.info(f"所有结果已保存至: {os.path.abspath(args.output)}")
    logger.info("=" * 60)


def run_interactive_mode(fetcher, importer, processor, analyzer, visualizer, advisor, output_dir):
    """交互式运行模式"""
    print("\n" + "=" * 60)
    print("📚 SSCI旅游学术趋势分析系统 - 交互模式")
    print("=" * 60)
    
    papers = []
    
    while True:
        print("\n请选择操作：")
        print("1. 从OpenAlex获取数据")
        print("2. 导入本地文件（WoS/Scopus/CSV）")
        print("3. 加载演示数据")
        print("4. 执行关键词分析")
        print("5. 执行LDA主题建模")
        print("6. 生成可视化图表")
        print("7. AI辅助选题建议")
        print("8. 生成完整报告")
        print("9. 查看当前数据统计")
        print("0. 退出")
        
        choice = input("\n请输入选项 (0-9): ").strip()
        
        if choice == '0':
            print("感谢使用，再见！")
            break
        
        elif choice == '1':
            keywords = input("请输入搜索关键词（用逗号分隔）: ").strip()
            if keywords:
                keywords_list = [k.strip() for k in keywords.split(',')]
                years = input("请输入年份范围（如2024-2026，直接回车使用默认）: ").strip() or "2024-2026"
                year_start, year_end = map(int, years.split('-'))
                max_results = int(input("最大获取数量（直接回车默认500）: ").strip() or "500")
                
                print(f"\n正在获取数据...")
                new_papers = fetcher.fetch_papers(keywords_list, year_start, year_end, max_results)
                papers.extend(new_papers)
                print(f"✓ 获取到 {len(new_papers)} 篇论文，当前共 {len(papers)} 篇")
        
        elif choice == '2':
            file_type = input("文件类型（wos/scopus/csv）: ").strip().lower()
            file_path = input("文件路径: ").strip()
            
            if os.path.exists(file_path):
                if file_type == 'wos':
                    new_papers = importer.import_wos(file_path)
                elif file_type == 'scopus':
                    new_papers = importer.import_scopus(file_path)
                else:
                    new_papers = importer.import_csv(file_path)
                papers.extend(new_papers)
                print(f"✓ 导入 {len(new_papers)} 篇论文，当前共 {len(papers)} 篇")
            else:
                print("❌ 文件不存在")
        
        elif choice == '3':
            papers = fetcher.generate_demo_data()
            print(f"✓ 已加载 {len(papers)} 篇演示数据")
        
        elif choice == '4':
            if not papers:
                print("❌ 请先获取或导入数据")
                continue
            processed = processor.process_papers(papers)
            stats = analyzer.analyze_keywords(processed)
            burst = analyzer.detect_burst_words(processed)
            analyzer.save_keyword_stats(stats, os.path.join(output_dir, 'keyword_analysis.csv'))
            analyzer.save_burst_words(burst, os.path.join(output_dir, 'burst_words.csv'))
            print("✓ 关键词分析完成，结果已保存")
            print("\n📊 Top 10 高频关键词：")
            for i, (kw, freq) in enumerate(list(stats.items())[:10], 1):
                print(f"  {i}. {kw}: {freq}")
        
        elif choice == '5':
            if not papers:
                print("❌ 请先获取或导入数据")
                continue
            n_topics = int(input("主题数量（默认8）: ").strip() or "8")
            analyzer.n_topics = n_topics
            processed = processor.process_papers(papers)
            topics = analyzer.lda_topic_modeling(processed)
            analyzer.save_topics(topics, os.path.join(output_dir, 'lda_topics.txt'))
            print("✓ LDA主题建模完成")
            print("\n📚 发现的研究主题：")
            for i, topic in enumerate(topics, 1):
                print(f"  主题{i}: {', '.join(topic['keywords'][:5])}")
        
        elif choice == '6':
            if not papers:
                print("❌ 请先获取或导入数据")
                continue
            processed = processor.process_papers(papers)
            stats = analyzer.analyze_keywords(processed)
            topics = analyzer.lda_topic_modeling(processed)
            
            print("正在生成图表...")
            visualizer.plot_keyword_trends(stats)
            visualizer.plot_cooccurrence_network(processed)
            visualizer.plot_yearly_heatmap(processed)
            visualizer.plot_topic_distribution(topics)
            visualizer.plot_citation_analysis(processed)
            print(f"✓ 所有图表已保存至: {output_dir}")
        
        elif choice == '7':
            if not papers:
                print("❌ 请先获取或导入数据")
                continue
            focus = input("研究聚焦方向（可选，直接回车跳过）: ").strip() or None
            processed = processor.process_papers(papers)
            gaps = analyzer.identify_research_gaps(processed)
            
            print("\n正在生成AI辅助建议...")
            suggestions = advisor.generate_suggestions(processed, gaps, focus)
            advisor.save_suggestions(suggestions, os.path.join(output_dir, 'ai_suggestions.md'))
            print(f"✓ AI建议已保存至: {output_dir}/ai_suggestions.md")
            print("\n" + "=" * 50)
            print(suggestions[:2000] + "..." if len(suggestions) > 2000 else suggestions)
        
        elif choice == '8':
            if not papers:
                print("❌ 请先获取或导入数据")
                continue
            processed = processor.process_papers(papers)
            stats = analyzer.analyze_keywords(processed)
            burst = analyzer.detect_burst_words(processed)
            topics = analyzer.lda_topic_modeling(processed)
            gaps = analyzer.identify_research_gaps(processed)
            
            generate_report(processed, stats, burst, topics, gaps, output_dir)
            print(f"✓ 完整报告已保存至: {output_dir}/analysis_report.md")
        
        elif choice == '9':
            print(f"\n📊 当前数据统计：")
            print(f"  论文总数: {len(papers)}")
            if papers:
                years = [p.get('year', 0) for p in papers if p.get('year')]
                if years:
                    print(f"  年份范围: {min(years)} - {max(years)}")
                journals = set(p.get('journal', '') for p in papers if p.get('journal'))
                print(f"  期刊数量: {len(journals)}")
                with_abstract = sum(1 for p in papers if p.get('abstract'))
                print(f"  有摘要的论文: {with_abstract}")


def generate_report(papers, keyword_stats, burst_words, topics, gaps, output_dir):
    """生成综合分析报告"""
    report = []
    report.append("# SSCI旅游学术趋势分析报告")
    report.append(f"\n**生成时间**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"\n**分析论文数**: {len(papers)}")
    
    report.append("\n---\n")
    report.append("## 1. 数据概览\n")
    
    if papers:
        years = [p.get('year', 0) for p in papers if p.get('year')]
        if years:
            report.append(f"- 年份范围: {min(years)} - {max(years)}")
        
        journals = {}
        for p in papers:
            j = p.get('journal', 'Unknown')
            journals[j] = journals.get(j, 0) + 1
        
        report.append(f"- 涉及期刊: {len(journals)} 种")
        report.append("\n### 主要期刊分布\n")
        for j, count in sorted(journals.items(), key=lambda x: -x[1])[:10]:
            report.append(f"- {j}: {count} 篇")
    
    if keyword_stats:
        report.append("\n---\n")
        report.append("## 2. 关键词分析\n")
        report.append("### 2.1 高频关键词 Top 20\n")
        report.append("| 排名 | 关键词 | 频次 |")
        report.append("|------|--------|------|")
        for i, (kw, freq) in enumerate(list(keyword_stats.items())[:20], 1):
            report.append(f"| {i} | {kw} | {freq} |")
    
    if burst_words:
        report.append("\n### 2.2 突发词（Burst Words）\n")
        report.append("*突发词表示近期快速增长的研究热点*\n")
        report.append("| 关键词 | 增长率 | 趋势 |")
        report.append("|--------|--------|------|")
        for bw in burst_words[:15]:
            trend = "📈" if bw.get('growth_rate', 0) > 0 else "📉"
            report.append(f"| {bw['keyword']} | {bw.get('growth_rate', 0):.1%} | {trend} |")
    
    if topics:
        report.append("\n---\n")
        report.append("## 3. LDA主题建模结果\n")
        for i, topic in enumerate(topics, 1):
            report.append(f"\n### 主题 {i}: {topic.get('label', 'Unknown')}")
            report.append(f"**核心关键词**: {', '.join(topic['keywords'][:8])}")
            report.append(f"\n**主题描述**: {topic.get('description', '待补充')}\n")
    
    if gaps:
        report.append("\n---\n")
        report.append("## 4. 研究缺口识别\n")
        report.append("*基于\"Limitations\"和\"Future Research\"文本挖掘*\n")
        for i, gap in enumerate(gaps, 1):
            report.append(f"\n### 缺口 {i}: {gap['title']}")
            report.append(f"- **识别来源**: {gap.get('source_count', 'N/A')} 篇论文提及")
            report.append(f"- **研究机会**: {gap.get('opportunity', '待分析')}")
    
    report.append("\n---\n")
    report.append("## 5. 选题建议\n")
    report.append("""
基于以上分析，建议关注以下研究方向：

1. **新兴技术应用**: 结合突发词中的技术关键词（如AI、VR、IoT），探索其在旅游领域的创新应用
2. **交叉研究**: 关注高频词共现网络中的跨学科组合，如"可持续发展+数字化转型"
3. **填补缺口**: 针对研究缺口部分的方向，设计针对性研究
4. **方法论创新**: 考虑采用混合研究方法或大数据分析方法

### 写作建议

在方法论部分，可以写：
> "本研究采用基于Python的多阶段文本挖掘技术（Text Mining），对Web of Science数据库近三年
> 的XXX篇旅游类SSCI论文进行了系统性的演化路径分析，识别出XX个核心研究主题和XX个潜在
> 研究缺口。"
""")
    
    report.append("\n---\n")
    report.append("## 附录\n")
    report.append("### 数据文件清单\n")
    report.append("- `processed_papers.csv` - 预处理后的论文数据")
    report.append("- `keyword_analysis.csv` - 关键词统计")
    report.append("- `burst_words.csv` - 突发词列表")
    report.append("- `lda_topics.txt` - LDA主题详情")
    report.append("- `research_gaps.txt` - 研究缺口")
    report.append("- `ai_suggestions.md` - AI辅助建议")
    report.append("\n### 可视化图表\n")
    report.append("- `keyword_trends.png` - 关键词趋势图")
    report.append("- `cooccurrence_network.png` - 关键词共现网络")
    report.append("- `yearly_heatmap.png` - 年度热力图")
    report.append("- `topic_distribution.png` - 主题分布图")
    report.append("- `citation_analysis.png` - 引用分析图")
    
    report_text = '\n'.join(report)
    
    with open(os.path.join(output_dir, 'analysis_report.md'), 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    return report_text


if __name__ == '__main__':
    main()
