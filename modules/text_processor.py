"""
文本预处理模块
包含NLP文本处理、分词、清洗、实体识别等功能
"""

import re
import logging
from typing import List, Dict, Set, Optional
from collections import Counter
import json
import csv

logger = logging.getLogger(__name__)


class TextProcessor:
    """文本预处理器"""
    
    def __init__(self):
        # 停用词列表
        self.stopwords = self._load_stopwords()
        
        # 学术领域特定停用词
        self.academic_stopwords = {
            'study', 'research', 'paper', 'article', 'results', 'findings',
            'analysis', 'data', 'method', 'methods', 'approach', 'model',
            'using', 'based', 'propose', 'proposed', 'show', 'shows',
            'suggest', 'suggests', 'indicate', 'indicates', 'examine',
            'examines', 'explore', 'explores', 'investigate', 'investigates',
            'aim', 'aims', 'objective', 'purpose', 'contribution',
            'literature', 'review', 'framework', 'theory', 'theoretical',
            'empirical', 'quantitative', 'qualitative', 'sample', 'samples',
            'respondent', 'respondents', 'participant', 'participants',
            'significant', 'significantly', 'effect', 'effects', 'impact',
            'impacts', 'influence', 'influences', 'relationship', 'relationships',
            'factor', 'factors', 'variable', 'variables', 'hypothesis',
            'hypotheses', 'conclusion', 'conclusions', 'implication', 'implications',
            'limitation', 'limitations', 'future', 'direction', 'directions'
        }
        
        # 旅游领域关键术语（应保留）
        self.domain_terms = {
            'tourism', 'tourist', 'tourists', 'travel', 'traveler', 'travelers',
            'destination', 'destinations', 'hotel', 'hotels', 'hospitality',
            'accommodation', 'airline', 'airlines', 'attraction', 'attractions',
            'experience', 'experiences', 'satisfaction', 'loyalty', 'motivation',
            'sustainable', 'sustainability', 'eco-tourism', 'ecotourism',
            'cultural', 'heritage', 'authenticity', 'wellness', 'medical',
            'dark tourism', 'adventure', 'rural', 'urban', 'coastal',
            'airbnb', 'sharing economy', 'platform', 'online', 'digital',
            'smart tourism', 'smart destination', 'iot', 'big data',
            'virtual reality', 'vr', 'augmented reality', 'ar', 'metaverse',
            'artificial intelligence', 'ai', 'machine learning', 'ml',
            'generative ai', 'chatgpt', 'llm', 'chatbot', 'robot',
            'service quality', 'servicescape', 'service recovery',
            'word of mouth', 'wom', 'ewom', 'social media', 'instagram',
            'influencer', 'ugc', 'review', 'reviews', 'rating', 'ratings',
            'booking', 'reservation', 'ota', 'expedia', 'tripadvisor',
            'covid', 'pandemic', 'recovery', 'resilience', 'crisis',
            'overtourism', 'undertourism', 'gentrification', 'carrying capacity'
        }
        
        # 短语映射（合并同义词）
        self.phrase_mapping = {
            'artificial intelligence': 'ai',
            'virtual reality': 'vr',
            'augmented reality': 'ar',
            'machine learning': 'ml',
            'internet of things': 'iot',
            'big data analytics': 'big data',
            'word of mouth': 'wom',
            'electronic word of mouth': 'ewom',
            'user generated content': 'ugc',
            'online travel agency': 'ota',
            'customer satisfaction': 'satisfaction',
            'tourist satisfaction': 'satisfaction',
            'service quality': 'service quality',
            'sustainable tourism': 'sustainable tourism',
            'eco tourism': 'ecotourism',
            'smart tourism': 'smart tourism',
            'sharing economy': 'sharing economy',
            'generative artificial intelligence': 'generative ai',
            'large language model': 'llm',
            'large language models': 'llm'
        }
        
        # 词干映射
        self.stem_mapping = {
            'tourists': 'tourist',
            'travelers': 'traveler',
            'destinations': 'destination',
            'hotels': 'hotel',
            'experiences': 'experience',
            'attractions': 'attraction',
            'reviews': 'review',
            'ratings': 'rating',
            'booking': 'booking',
            'bookings': 'booking'
        }
    
    def _load_stopwords(self) -> Set[str]:
        """加载停用词"""
        # 基础英语停用词
        basic_stopwords = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'have', 'in', 'is', 'it', 'its', 'of', 'on', 'or', 'that',
            'the', 'this', 'to', 'was', 'were', 'will', 'with', 'which',
            'can', 'could', 'do', 'does', 'did', 'done', 'been', 'being',
            'but', 'if', 'not', 'no', 'such', 'than', 'these', 'those',
            'then', 'there', 'their', 'they', 'them', 'through', 'we', 'our',
            'what', 'when', 'where', 'who', 'how', 'why', 'would', 'should',
            'may', 'might', 'must', 'shall', 'also', 'more', 'most', 'much',
            'many', 'some', 'any', 'all', 'both', 'each', 'few', 'other',
            'over', 'own', 'same', 'so', 'too', 'very', 'just', 'only',
            'now', 'here', 'however', 'therefore', 'thus', 'although',
            'because', 'since', 'while', 'between', 'among', 'during',
            'before', 'after', 'above', 'below', 'under', 'within', 'without',
            'about', 'into', 'onto', 'upon', 'per', 'via', 'etc', 'ie', 'eg',
            'i', 'me', 'my', 'you', 'your', 'he', 'him', 'his', 'she', 'her',
            'one', 'two', 'three', 'first', 'second', 'third', 'well', 'yet'
        }
        return basic_stopwords
    
    def process_papers(self, papers: List[Dict]) -> List[Dict]:
        """
        处理论文列表
        
        处理步骤：
        1. 清洗文本（去除HTML、特殊字符等）
        2. 提取和标准化关键词
        3. 分词处理摘要
        4. 提取研究局限性和未来研究建议
        """
        processed = []
        
        for paper in papers:
            try:
                processed_paper = self._process_single_paper(paper)
                if processed_paper:
                    processed.append(processed_paper)
            except Exception as e:
                logger.debug(f"处理论文失败: {e}")
                continue
        
        logger.info(f"成功处理 {len(processed)}/{len(papers)} 篇论文")
        return processed
    
    def _process_single_paper(self, paper: Dict) -> Optional[Dict]:
        """处理单篇论文"""
        # 复制原始数据
        processed = dict(paper)
        
        # 清洗标题
        if paper.get('title'):
            processed['title_clean'] = self._clean_text(paper['title'])
        
        # 清洗和处理摘要
        if paper.get('abstract'):
            abstract = paper['abstract']
            processed['abstract_clean'] = self._clean_text(abstract)
            processed['abstract_tokens'] = self._tokenize(abstract)
            processed['abstract_keywords'] = self._extract_keywords_from_text(abstract)
            
            # 提取研究局限性和未来研究
            limitations = self._extract_limitations(abstract)
            future_research = self._extract_future_research(abstract)
            processed['limitations'] = limitations
            processed['future_research'] = future_research
        
        # 标准化关键词
        if paper.get('keywords'):
            processed['keywords_normalized'] = self._normalize_keywords(paper['keywords'])
        else:
            processed['keywords_normalized'] = []
        
        # 合并所有关键词（作者关键词 + 从摘要提取的关键词）
        all_keywords = set(processed.get('keywords_normalized', []))
        all_keywords.update(processed.get('abstract_keywords', []))
        processed['all_keywords'] = list(all_keywords)
        
        # 提取年月信息
        if paper.get('year'):
            processed['year'] = int(paper['year']) if paper['year'] else None
        
        return processed
    
    def _clean_text(self, text: str) -> str:
        """清洗文本"""
        if not text:
            return ""
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # 移除特殊字符但保留基本标点
        text = re.sub(r'[^\w\s\.\,\;\:\-\'\"]', ' ', text)
        
        # 规范化空白
        text = re.sub(r'\s+', ' ', text)
        
        # 移除版权声明等
        text = re.sub(r'©.*?(?=\.|$)', '', text)
        text = re.sub(r'copyright.*?(?=\.|$)', '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        if not text:
            return []
        
        # 转小写
        text = text.lower()
        
        # 先处理多词短语
        for phrase, replacement in self.phrase_mapping.items():
            text = text.replace(phrase, replacement.replace(' ', '_'))
        
        # 简单分词
        tokens = re.findall(r'\b[a-z][a-z0-9_\-]+\b', text)
        
        # 过滤
        filtered = []
        for token in tokens:
            # 还原下划线为空格
            token = token.replace('_', ' ')
            
            # 跳过停用词
            if token in self.stopwords:
                continue
            
            # 跳过学术停用词（除非是领域术语）
            if token in self.academic_stopwords and token not in self.domain_terms:
                continue
            
            # 跳过太短的词
            if len(token) < 2:
                continue
            
            # 跳过纯数字
            if token.isdigit():
                continue
            
            # 词干化
            if token in self.stem_mapping:
                token = self.stem_mapping[token]
            
            filtered.append(token)
        
        return filtered
    
    def _normalize_keywords(self, keywords: List[str]) -> List[str]:
        """标准化关键词"""
        normalized = []
        
        for kw in keywords:
            if not kw:
                continue
            
            kw = kw.lower().strip()
            
            # 移除特殊字符
            kw = re.sub(r'[^\w\s\-]', '', kw)
            
            # 短语映射
            if kw in self.phrase_mapping:
                kw = self.phrase_mapping[kw]
            
            # 词干化
            if kw in self.stem_mapping:
                kw = self.stem_mapping[kw]
            
            # 跳过停用词
            if kw in self.stopwords or kw in self.academic_stopwords:
                continue
            
            if kw and len(kw) >= 2:
                normalized.append(kw)
        
        return list(set(normalized))
    
    def _extract_keywords_from_text(self, text: str, top_n: int = 10) -> List[str]:
        """从文本中提取关键词"""
        tokens = self._tokenize(text)
        
        # 计算词频
        freq = Counter(tokens)
        
        # 优先返回领域术语
        domain_found = [t for t in tokens if t in self.domain_terms]
        domain_freq = Counter(domain_found)
        
        # 合并结果
        result = []
        
        # 先添加高频领域术语
        for term, _ in domain_freq.most_common(top_n // 2):
            result.append(term)
        
        # 再添加其他高频词
        for token, _ in freq.most_common(top_n):
            if token not in result:
                result.append(token)
        
        return result[:top_n]
    
    def _extract_limitations(self, text: str) -> str:
        """提取研究局限性"""
        if not text:
            return ""
        
        # 匹配模式
        patterns = [
            r'limitation[s]?\s*(?:of\s+(?:this|the|our)\s+(?:study|research|paper))?\s*[:\.\,]?\s*(.{50,500})',
            r'(?:this|the|our)\s+(?:study|research)\s+(?:has|have)\s+(?:several|some|a few)?\s*limitation[s]?[:\.\,]?\s*(.{50,500})',
            r'(?:despite|although|however)[,\s]+(?:this|the|our)\s+(?:study|research)[,\s]+(.{50,300})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_future_research(self, text: str) -> str:
        """提取未来研究建议"""
        if not text:
            return ""
        
        # 匹配模式
        patterns = [
            r'future\s+(?:research|studies|study|work|investigation)[s]?\s*(?:should|could|may|might)?\s*(.{50,500})',
            r'(?:further|additional)\s+(?:research|studies|study|investigation)[s]?\s*(?:is|are)?\s*(?:needed|required|recommended|suggested)?\s*(.{50,500})',
            r'(?:directions?\s+for|avenues?\s+for|opportunities?\s+for)\s+future\s+(?:research|studies)\s*(.{50,500})',
            r'(?:suggest|recommend|propose)[s]?\s+(?:that\s+)?future\s+(?:research|studies)\s*(.{50,500})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def extract_ngrams(self, text: str, n: int = 2) -> List[str]:
        """提取n-gram"""
        tokens = self._tokenize(text)
        
        if len(tokens) < n:
            return []
        
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngram = ' '.join(tokens[i:i+n])
            ngrams.append(ngram)
        
        return ngrams
    
    def get_text_stats(self, papers: List[Dict]) -> Dict:
        """获取文本统计信息"""
        stats = {
            'total_papers': len(papers),
            'papers_with_abstract': 0,
            'papers_with_keywords': 0,
            'total_tokens': 0,
            'unique_tokens': set(),
            'avg_abstract_length': 0,
            'keyword_freq': Counter()
        }
        
        abstract_lengths = []
        
        for paper in papers:
            if paper.get('abstract'):
                stats['papers_with_abstract'] += 1
                tokens = paper.get('abstract_tokens', [])
                stats['total_tokens'] += len(tokens)
                stats['unique_tokens'].update(tokens)
                abstract_lengths.append(len(paper['abstract']))
            
            if paper.get('keywords') or paper.get('all_keywords'):
                stats['papers_with_keywords'] += 1
                keywords = paper.get('all_keywords', paper.get('keywords', []))
                stats['keyword_freq'].update(keywords)
        
        if abstract_lengths:
            stats['avg_abstract_length'] = sum(abstract_lengths) / len(abstract_lengths)
        
        stats['unique_tokens'] = len(stats['unique_tokens'])
        
        return stats
    
    def save_to_file(self, papers: List[Dict], filepath: str, format: str = 'csv'):
        """保存处理后的数据到文件"""
        if format == 'csv':
            self._save_to_csv(papers, filepath)
        elif format == 'json':
            self._save_to_json(papers, filepath)
        elif format == 'excel':
            self._save_to_excel(papers, filepath)
        else:
            logger.warning(f"未知格式: {format}，使用CSV")
            self._save_to_csv(papers, filepath)
    
    def _save_to_csv(self, papers: List[Dict], filepath: str):
        """保存为CSV"""
        if not papers:
            return
        
        # 定义输出字段
        fields = [
            'id', 'doi', 'title', 'authors', 'year', 'journal',
            'abstract', 'keywords', 'all_keywords', 'citations',
            'limitations', 'future_research', 'source'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
            writer.writeheader()
            
            for paper in papers:
                row = dict(paper)
                # 转换列表为字符串
                for key in ['authors', 'keywords', 'all_keywords']:
                    if key in row and isinstance(row[key], list):
                        row[key] = '; '.join(row[key])
                writer.writerow(row)
        
        logger.info(f"数据已保存至: {filepath}")
    
    def _save_to_json(self, papers: List[Dict], filepath: str):
        """保存为JSON"""
        # 过滤不可序列化的数据
        serializable = []
        for paper in papers:
            clean_paper = {}
            for k, v in paper.items():
                if isinstance(v, (str, int, float, bool, list, dict, type(None))):
                    clean_paper[k] = v
            serializable.append(clean_paper)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serializable, f, ensure_ascii=False, indent=2)
        
        logger.info(f"数据已保存至: {filepath}")
    
    def _save_to_excel(self, papers: List[Dict], filepath: str):
        """保存为Excel（需要openpyxl）"""
        try:
            import pandas as pd
            
            # 转换为DataFrame
            df_data = []
            for paper in papers:
                row = dict(paper)
                for key in ['authors', 'keywords', 'all_keywords', 'abstract_tokens', 'abstract_keywords']:
                    if key in row and isinstance(row[key], list):
                        row[key] = '; '.join(str(x) for x in row[key])
                df_data.append(row)
            
            df = pd.DataFrame(df_data)
            
            # 选择重要列
            columns = [
                'id', 'doi', 'title', 'authors', 'year', 'journal',
                'abstract', 'keywords', 'all_keywords', 'citations',
                'limitations', 'future_research', 'source'
            ]
            columns = [c for c in columns if c in df.columns]
            df = df[columns]
            
            df.to_excel(filepath, index=False, engine='openpyxl')
            logger.info(f"数据已保存至: {filepath}")
            
        except ImportError:
            logger.warning("需要安装pandas和openpyxl才能导出Excel，改用CSV")
            csv_path = filepath.replace('.xlsx', '.csv').replace('.xls', '.csv')
            self._save_to_csv(papers, csv_path)
