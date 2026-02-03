#!/usr/bin/env python3
"""
SSCI旅游学术趋势分析系统 - Web UI界面
使用 Streamlit 构建

运行方式: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import os
import sys
import json
from datetime import datetime

# 添加模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.data_fetcher import DataFetcher
from modules.file_importer import FileImporter
from modules.text_processor import TextProcessor
from modules.analyzer import TrendAnalyzer
from modules.visualizer import Visualizer
from modules.ai_advisor import AIAdvisor

# 页面配置
st.set_page_config(
    page_title="SSCI旅游学术趋势分析系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 10px 20px;
        background-color: #f0f2f6;
        border-radius: 5px;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border-radius: 5px;
        border-left: 5px solid #28a745;
    }
    .warning-box {
        padding: 1rem;
        background-color: #fff3cd;
        border-radius: 5px;
        border-left: 5px solid #ffc107;
    }
</style>
""", unsafe_allow_html=True)

# 初始化session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'topics' not in st.session_state:
    st.session_state.topics = None


def load_demo_data():
    """加载或生成Demo数据"""
    from generate_demo_data import generate_demo_data
    
    demo_file = "demo_data.csv"
    if not os.path.exists(demo_file):
        generate_demo_data(200, demo_file)
    
    return pd.read_csv(demo_file)


def main():
    # 标题
    st.markdown('<p class="main-header">📊 SSCI旅游学术趋势分析系统</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">文献计量 | 关键词挖掘 | 研究缺口识别 | AI辅助选题</p>', unsafe_allow_html=True)
    
    # 侧边栏
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/search-in-cloud.png", width=80)
        st.markdown("### 🎯 操作面板")
        st.markdown("---")
        
        # 数据来源选择
        data_source = st.selectbox(
            "选择数据来源",
            ["📂 上传本地文件", "🌐 从OpenAlex获取", "🎲 使用Demo数据"]
        )
        
        st.markdown("---")
        st.markdown("### 📈 当前状态")
        
        if st.session_state.data is not None:
            st.success(f"✅ 已加载 {len(st.session_state.data)} 条数据")
        else:
            st.warning("⚠️ 未加载数据")
        
        if st.session_state.analysis_results is not None:
            st.success("✅ 已完成分析")
        
        st.markdown("---")
        st.markdown("### ℹ️ 关于")
        st.markdown("""
        **版本**: 2.0  
        **功能**: 
        - 关键词频率分析
        - 突发词检测
        - LDA主题建模
        - 研究缺口识别
        - AI辅助选题
        """)
    
    # 主要内容区域 - 使用标签页
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📂 数据加载", 
        "🔑 关键词分析", 
        "🧠 主题建模",
        "📈 可视化",
        "🤖 AI助手"
    ])
    
    # ==================== Tab 1: 数据加载 ====================
    with tab1:
        st.markdown("## 📂 数据加载")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if "上传" in data_source:
                st.markdown("### 上传本地文件")
                st.markdown("支持格式: CSV, TXT (WoS), BibTeX, RIS")
                
                uploaded_file = st.file_uploader(
                    "拖拽或点击上传文件",
                    type=['csv', 'txt', 'bib', 'ris'],
                    help="支持Web of Science、Scopus导出文件"
                )
                
                if uploaded_file is not None:
                    try:
                        # 保存上传的文件
                        file_path = f"temp_{uploaded_file.name}"
                        with open(file_path, 'wb') as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # 导入文件
                        importer = FileImporter()
                        data = importer.import_file(file_path)
                        
                        if data is not None and len(data) > 0:
                            st.session_state.data = data
                            st.success(f"✅ 成功加载 {len(data)} 条文献记录!")
                        else:
                            st.error("❌ 文件解析失败，请检查格式")
                        
                        # 清理临时文件
                        os.remove(file_path)
                        
                    except Exception as e:
                        st.error(f"❌ 加载失败: {str(e)}")
            
            elif "OpenAlex" in data_source:
                st.markdown("### 🌐 从OpenAlex获取数据")
                st.markdown("OpenAlex是免费开放的学术数据库，无需API密钥")
                
                keywords = st.text_input(
                    "搜索关键词",
                    placeholder="例如: generative AI tourism",
                    help="输入英文关键词，多个关键词用空格分隔"
                )
                
                col_a, col_b = st.columns(2)
                with col_a:
                    year_start = st.number_input("起始年份", min_value=2000, max_value=2026, value=2024)
                with col_b:
                    year_end = st.number_input("结束年份", min_value=2000, max_value=2026, value=2026)
                
                max_results = st.slider("最大获取数量", 50, 500, 200)
                
                if st.button("🔍 开始获取", type="primary"):
                    if keywords:
                        with st.spinner("正在从OpenAlex获取数据..."):
                            try:
                                fetcher = DataFetcher()
                                papers = fetcher.fetch_papers(
                                    keywords=keywords.split(),
                                    year_start=year_start,
                                    year_end=year_end,
                                    max_results=max_results
                                )
                                # 转换为DataFrame
                                import pandas as pd
                                data = pd.DataFrame(papers) if papers else None
                                
                                if data is not None and len(data) > 0:
                                    st.session_state.data = data
                                    st.success(f"✅ 成功获取 {len(data)} 条文献记录!")
                                else:
                                    st.warning("⚠️ 未找到相关文献，请尝试其他关键词")
                                    
                            except Exception as e:
                                st.error(f"❌ 获取失败: {str(e)}")
                    else:
                        st.warning("请输入搜索关键词")
            
            else:  # Demo数据
                st.markdown("### 🎲 使用Demo测试数据")
                st.markdown("生成200条模拟论文数据，用于测试系统功能")
                
                if st.button("📦 加载Demo数据", type="primary"):
                    with st.spinner("正在生成Demo数据..."):
                        try:
                            data = load_demo_data()
                            st.session_state.data = data
                            st.success(f"✅ 成功加载 {len(data)} 条Demo数据!")
                        except Exception as e:
                            st.error(f"❌ 加载失败: {str(e)}")
        
        with col2:
            st.markdown("### 📊 数据预览")
            if st.session_state.data is not None:
                df = st.session_state.data
                
                # 统计信息
                st.metric("论文总数", len(df))
                if 'year' in df.columns:
                    st.metric("时间范围", f"{df['year'].min()} - {df['year'].max()}")
                if 'journal' in df.columns:
                    st.metric("期刊数量", df['journal'].nunique())
                if 'citations' in df.columns:
                    st.metric("平均被引", f"{df['citations'].mean():.1f}")
        
        # 数据表格展示
        if st.session_state.data is not None:
            st.markdown("### 📋 数据详情")
            
            # 显示前10条
            display_df = st.session_state.data.head(10).copy()
            if 'abstract' in display_df.columns:
                display_df['abstract'] = display_df['abstract'].str[:100] + '...'
            
            st.dataframe(display_df, use_container_width=True)
            
            # 下载按钮
            csv = st.session_state.data.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                "📥 下载完整数据 (CSV)",
                csv,
                "ssci_data.csv",
                "text/csv"
            )
    
    # ==================== Tab 2: 关键词分析 ====================
    with tab2:
        st.markdown("## 🔑 关键词分析")
        
        if st.session_state.data is None:
            st.warning("⚠️ 请先在【数据加载】标签页加载数据")
        else:
            if st.button("🚀 开始关键词分析", type="primary"):
                with st.spinner("正在分析关键词..."):
                    try:
                        # 文本预处理
                        processor = TextProcessor()
                        processed = processor.process(st.session_state.data)
                        st.session_state.processed_data = processed
                        
                        # 关键词分析
                        analyzer = TrendAnalyzer()
                        results = analyzer.analyze(processed)
                        st.session_state.analysis_results = results
                        
                        st.success("✅ 分析完成!")
                        
                    except Exception as e:
                        st.error(f"❌ 分析失败: {str(e)}")
            
            # 显示分析结果
            if st.session_state.analysis_results is not None:
                results = st.session_state.analysis_results
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 📊 高频关键词 Top 20")
                    if 'top_keywords' in results:
                        kw_df = pd.DataFrame(results['top_keywords'][:20], columns=['关键词', '频次'])
                        
                        # 条形图
                        st.bar_chart(kw_df.set_index('关键词'))
                        
                        # 表格
                        st.dataframe(kw_df, use_container_width=True)
                
                with col2:
                    st.markdown("### 🔥 突发词 (Burst Words)")
                    st.markdown("*近期热度飙升的关键词*")
                    
                    if 'burst_words' in results and results['burst_words']:
                        for word, score in results['burst_words'][:10]:
                            st.markdown(f"⚡ **{word}** (突发指数: {score:.2f})")
                    else:
                        st.info("未检测到明显的突发词")
                    
                    st.markdown("---")
                    st.markdown("### 🕳️ 潜在研究缺口")
                    
                    if 'research_gaps' in results and results['research_gaps']:
                        for i, gap in enumerate(results['research_gaps'][:5], 1):
                            st.markdown(f"💡 {i}. {gap}")
                    else:
                        st.info("请完成LDA主题建模以获取研究缺口")
    
    # ==================== Tab 3: 主题建模 ====================
    with tab3:
        st.markdown("## 🧠 LDA主题建模")
        
        if st.session_state.processed_data is None:
            st.warning("⚠️ 请先完成关键词分析")
        else:
            col1, col2 = st.columns([1, 3])
            
            with col1:
                n_topics = st.slider("主题数量", 4, 15, 8)
                
                if st.button("🧠 运行LDA建模", type="primary"):
                    with st.spinner("正在进行主题建模..."):
                        try:
                            analyzer = TrendAnalyzer()
                            topics = analyzer.lda_topic_modeling(
                                st.session_state.processed_data, 
                                n_topics=n_topics
                            )
                            st.session_state.topics = topics
                            st.success("✅ 主题建模完成!")
                        except Exception as e:
                            st.error(f"❌ 建模失败: {str(e)}")
            
            with col2:
                if st.session_state.topics is not None:
                    st.markdown("### 📚 识别出的研究主题")
                    
                    for i, topic in enumerate(st.session_state.topics, 1):
                        with st.expander(f"📌 主题 {i}: {topic.get('label', 'Unknown')}", expanded=(i<=3)):
                            st.markdown(f"**关键词**: {', '.join(topic.get('keywords', [])[:10])}")
                            if 'doc_count' in topic:
                                st.markdown(f"**相关论文数**: {topic['doc_count']}")
                            if 'representative_paper' in topic:
                                st.markdown(f"**代表性论文**: {topic['representative_paper'][:100]}...")
    
    # ==================== Tab 4: 可视化 ====================
    with tab4:
        st.markdown("## 📈 可视化分析")
        
        if st.session_state.analysis_results is None:
            st.warning("⚠️ 请先完成关键词分析")
        else:
            viz_type = st.selectbox(
                "选择可视化类型",
                ["📊 关键词频率图", "🕸️ 共现网络", "📅 年度趋势", "📈 被引分析"]
            )
            
            if "频率" in viz_type:
                st.markdown("### 📊 关键词频率分布")
                
                if 'top_keywords' in st.session_state.analysis_results:
                    kw_data = st.session_state.analysis_results['top_keywords'][:30]
                    df = pd.DataFrame(kw_data, columns=['keyword', 'frequency'])
                    
                    # 使用Streamlit原生图表
                    st.bar_chart(df.set_index('keyword'))
            
            elif "共现" in viz_type:
                st.markdown("### 🕸️ 关键词共现网络")
                st.info("共现网络显示关键词之间的关联关系")
                
                if st.session_state.analysis_results and 'cooccurrence' in st.session_state.analysis_results:
                    cooc = st.session_state.analysis_results['cooccurrence']
                    
                    # 显示共现对
                    st.markdown("**高频共现词对:**")
                    for pair, count in list(cooc.items())[:15]:
                        st.markdown(f"- {pair[0]} ↔ {pair[1]}: {count}次")
                else:
                    st.warning("需要先运行关键词分析")
            
            elif "年度" in viz_type:
                st.markdown("### 📅 关键词年度趋势")
                
                if st.session_state.data is not None and 'year' in st.session_state.data.columns:
                    yearly = st.session_state.data.groupby('year').size()
                    st.line_chart(yearly)
                    
                    st.markdown("**各年度论文数量:**")
                    st.dataframe(yearly.reset_index().rename(columns={0: '论文数', 'year': '年份'}))
            
            elif "被引" in viz_type:
                st.markdown("### 📈 被引分析")
                
                if st.session_state.data is not None and 'citations' in st.session_state.data.columns:
                    df = st.session_state.data
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("总被引次数", int(df['citations'].sum()))
                    col2.metric("平均被引", f"{df['citations'].mean():.1f}")
                    col3.metric("最高被引", int(df['citations'].max()))
                    
                    # 被引分布
                    st.markdown("**被引次数分布:**")
                    hist_data = df['citations'].value_counts().sort_index().head(20)
                    st.bar_chart(hist_data)
                    
                    # 高被引论文
                    st.markdown("**🏆 高被引论文 Top 10:**")
                    top_cited = df.nlargest(10, 'citations')[['title', 'year', 'citations', 'journal']]
                    st.dataframe(top_cited, use_container_width=True)
    
    # ==================== Tab 5: AI助手 ====================
    with tab5:
        st.markdown("## 🤖 AI辅助分析")
        
        st.markdown("""
        AI助手可以帮你：
        - 🎯 生成创新选题建议
        - 📝 提供论文写作框架
        - 🔍 识别研究缺口
        - 💡 推荐研究方法
        """)
        
        # 检查是否有API key
        api_key = os.environ.get('ANTHROPIC_API_KEY', '')
        
        if not api_key:
            st.warning("⚠️ 未检测到 ANTHROPIC_API_KEY 环境变量")
            st.markdown("""
            **设置方法:**
            ```bash
            # Windows
            set ANTHROPIC_API_KEY=your-api-key
            
            # Mac/Linux
            export ANTHROPIC_API_KEY=your-api-key
            ```
            
            没有API Key也可以使用基于规则的建议功能👇
            """)
        
        st.markdown("---")
        
        analysis_type = st.selectbox(
            "选择分析类型",
            [
                "🎯 生成选题建议",
                "📝 论文写作框架",
                "🔍 研究缺口深度分析",
                "💬 自定义问题"
            ]
        )
        
        if "选题" in analysis_type:
            st.markdown("### 🎯 AI选题建议")
            
            focus_area = st.text_input(
                "你的研究兴趣方向",
                placeholder="例如: AI在旅游营销中的应用",
                help="输入你感兴趣的研究方向，AI会结合文献分析给出建议"
            )
            
            if st.button("✨ 生成选题建议", type="primary"):
                with st.spinner("AI正在分析并生成建议..."):
                    try:
                        advisor = AIAdvisor()
                        
                        context = {
                            'data': st.session_state.data,
                            'analysis': st.session_state.analysis_results,
                            'topics': st.session_state.topics,
                            'focus': focus_area
                        }
                        
                        suggestions = advisor.generate_topic_suggestions(context)
                        
                        st.markdown("### 📋 选题建议")
                        st.markdown(suggestions)
                        
                    except Exception as e:
                        st.error(f"生成失败: {str(e)}")
        
        elif "写作" in analysis_type:
            st.markdown("### 📝 论文写作框架")
            
            paper_topic = st.text_input(
                "你的论文题目/主题",
                placeholder="例如: ChatGPT对游客决策行为的影响研究"
            )
            
            if st.button("📄 生成写作框架", type="primary"):
                with st.spinner("生成写作框架..."):
                    try:
                        advisor = AIAdvisor()
                        framework = advisor.generate_writing_framework(paper_topic)
                        
                        st.markdown("### 📑 建议的论文框架")
                        st.markdown(framework)
                        
                    except Exception as e:
                        st.error(f"生成失败: {str(e)}")
        
        elif "缺口" in analysis_type:
            st.markdown("### 🔍 研究缺口深度分析")
            
            if st.session_state.analysis_results is None:
                st.warning("请先完成关键词分析以获得更准确的缺口识别")
            
            if st.button("🔎 分析研究缺口", type="primary"):
                with st.spinner("深度分析研究缺口..."):
                    try:
                        advisor = AIAdvisor()
                        
                        context = {
                            'data': st.session_state.data,
                            'analysis': st.session_state.analysis_results,
                            'topics': st.session_state.topics
                        }
                        
                        gaps = advisor.analyze_research_gaps(context)
                        
                        st.markdown("### 🕳️ 研究缺口分析报告")
                        st.markdown(gaps)
                        
                    except Exception as e:
                        st.error(f"分析失败: {str(e)}")
        
        else:  # 自定义问题
            st.markdown("### 💬 自定义问题")
            
            user_question = st.text_area(
                "输入你的问题",
                placeholder="例如: 如何在论文中强调方法论创新？SSCI审稿人最看重什么？",
                height=100
            )
            
            if st.button("💡 获取建议", type="primary"):
                if user_question:
                    with st.spinner("思考中..."):
                        try:
                            advisor = AIAdvisor()
                            
                            context = {
                                'data': st.session_state.data,
                                'analysis': st.session_state.analysis_results,
                                'question': user_question
                            }
                            
                            answer = advisor.answer_question(context)
                            
                            st.markdown("### 💡 建议")
                            st.markdown(answer)
                            
                        except Exception as e:
                            st.error(f"获取建议失败: {str(e)}")
                else:
                    st.warning("请输入问题")
    
    # 页脚
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #888; font-size: 0.9rem;">
            📊 SSCI旅游学术趋势分析系统 v2.0 | 
            Made with ❤️ by Claude AI
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
