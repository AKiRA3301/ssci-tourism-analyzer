"""
数据获取模块
使用合法的开放API获取学术论文数据

支持的数据源：
1. OpenAlex (完全免费开放)
2. Semantic Scholar (免费API)
3. Crossref (开放元数据)
"""

import requests
import time
import logging
import json
from datetime import datetime
from typing import List, Dict, Optional
import random

logger = logging.getLogger(__name__)


class DataFetcher:
    """学术论文数据获取器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SSCI-Tourism-Analyzer/2.0 (Academic Research Tool; mailto:researcher@university.edu)'
        })
        
        # API端点
        self.openalex_base = "https://api.openalex.org"
        self.semantic_scholar_base = "https://api.semanticscholar.org/graph/v1"
        self.crossref_base = "https://api.crossref.org"
        
        # 旅游类SSCI期刊的OpenAlex ID
        self.tourism_journals = {
            "Tourism Management": "S137773608",
            "Annals of Tourism Research": "S49861241",
            "Journal of Travel Research": "S116545846",
            "International Journal of Hospitality Management": "S168398937",
            "Journal of Sustainable Tourism": "S2764565878",
            "Tourism Geographies": "S163753555",
            "Current Issues in Tourism": "S185196701",
            "Journal of Destination Marketing & Management": "S2764825156"
        }
    
    def fetch_papers(self, keywords: List[str], year_start: int, year_end: int, 
                     max_results: int = 500, sources: List[str] = None) -> List[Dict]:
        """
        获取论文数据
        
        Args:
            keywords: 搜索关键词列表
            year_start: 起始年份
            year_end: 结束年份
            max_results: 最大结果数
            sources: 数据源列表 ['openalex', 'semantic_scholar', 'crossref']
        
        Returns:
            论文数据列表
        """
        if sources is None:
            sources = ['openalex']  # 默认使用OpenAlex
        
        all_papers = []
        
        for source in sources:
            try:
                if source == 'openalex':
                    papers = self._fetch_from_openalex(keywords, year_start, year_end, max_results)
                elif source == 'semantic_scholar':
                    papers = self._fetch_from_semantic_scholar(keywords, year_start, year_end, max_results)
                elif source == 'crossref':
                    papers = self._fetch_from_crossref(keywords, year_start, year_end, max_results)
                else:
                    logger.warning(f"未知数据源: {source}")
                    continue
                
                all_papers.extend(papers)
                logger.info(f"从 {source} 获取到 {len(papers)} 篇论文")
                
            except Exception as e:
                logger.error(f"从 {source} 获取数据失败: {e}")
        
        # 去重（基于DOI或标题）
        seen = set()
        unique_papers = []
        for paper in all_papers:
            key = paper.get('doi') or paper.get('title', '')
            if key and key not in seen:
                seen.add(key)
                unique_papers.append(paper)
        
        logger.info(f"去重后共 {len(unique_papers)} 篇论文")
        return unique_papers
    
    def _fetch_from_openalex(self, keywords: List[str], year_start: int, 
                             year_end: int, max_results: int) -> List[Dict]:
        """从OpenAlex获取数据"""
        papers = []
        query = ' '.join(keywords)
        
        # 构建过滤器
        filters = [
            f"publication_year:{year_start}-{year_end}",
            "type:article",
            "has_abstract:true"
        ]
        
        # 添加旅游期刊过滤（可选）
        # filters.append(f"primary_location.source.id:{list(self.tourism_journals.values())[0]}")
        
        params = {
            'search': query,
            'filter': ','.join(filters),
            'per_page': min(200, max_results),
            'sort': 'cited_by_count:desc',
            'select': 'id,doi,title,publication_year,abstract_inverted_index,authorships,primary_location,cited_by_count,concepts,keywords'
        }
        
        cursor = '*'
        page = 0
        
        while len(papers) < max_results:
            params['cursor'] = cursor
            
            try:
                response = self.session.get(
                    f"{self.openalex_base}/works",
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                
                results = data.get('results', [])
                if not results:
                    break
                
                for item in results:
                    paper = self._parse_openalex_paper(item)
                    if paper:
                        papers.append(paper)
                
                cursor = data.get('meta', {}).get('next_cursor')
                if not cursor:
                    break
                
                page += 1
                logger.debug(f"OpenAlex: 第{page}页，已获取 {len(papers)} 篇")
                
                # 遵守API速率限制
                time.sleep(0.1)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"OpenAlex API请求失败: {e}")
                break
        
        return papers[:max_results]
    
    def _parse_openalex_paper(self, item: Dict) -> Optional[Dict]:
        """解析OpenAlex论文数据"""
        try:
            # 还原倒排索引格式的摘要
            abstract = ""
            if item.get('abstract_inverted_index'):
                inv_index = item['abstract_inverted_index']
                words = {}
                for word, positions in inv_index.items():
                    for pos in positions:
                        words[pos] = word
                abstract = ' '.join(words[i] for i in sorted(words.keys()))
            
            # 提取作者
            authors = []
            for auth in item.get('authorships', [])[:10]:
                author_info = auth.get('author', {})
                if author_info.get('display_name'):
                    authors.append(author_info['display_name'])
            
            # 提取期刊
            journal = ""
            location = item.get('primary_location', {})
            if location and location.get('source'):
                journal = location['source'].get('display_name', '')
            
            # 提取关键词
            keywords = []
            for concept in item.get('concepts', [])[:15]:
                if concept.get('display_name'):
                    keywords.append(concept['display_name'].lower())
            
            # 添加作者关键词
            for kw in item.get('keywords', []):
                if kw.get('keyword'):
                    keywords.append(kw['keyword'].lower())
            
            return {
                'id': item.get('id', ''),
                'doi': item.get('doi', '').replace('https://doi.org/', '') if item.get('doi') else '',
                'title': item.get('title', ''),
                'authors': authors,
                'year': item.get('publication_year'),
                'journal': journal,
                'abstract': abstract,
                'keywords': list(set(keywords)),
                'citations': item.get('cited_by_count', 0),
                'source': 'openalex'
            }
        except Exception as e:
            logger.debug(f"解析论文失败: {e}")
            return None
    
    def _fetch_from_semantic_scholar(self, keywords: List[str], year_start: int,
                                     year_end: int, max_results: int) -> List[Dict]:
        """从Semantic Scholar获取数据"""
        papers = []
        query = ' '.join(keywords)
        
        params = {
            'query': query,
            'year': f"{year_start}-{year_end}",
            'fields': 'paperId,externalIds,title,abstract,year,authors,venue,citationCount,fieldsOfStudy',
            'limit': min(100, max_results),
            'offset': 0
        }
        
        while len(papers) < max_results:
            try:
                response = self.session.get(
                    f"{self.semantic_scholar_base}/paper/search",
                    params=params,
                    timeout=30
                )
                
                if response.status_code == 429:
                    logger.warning("Semantic Scholar API速率限制，等待...")
                    time.sleep(60)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                results = data.get('data', [])
                if not results:
                    break
                
                for item in results:
                    paper = self._parse_semantic_scholar_paper(item)
                    if paper:
                        papers.append(paper)
                
                params['offset'] += len(results)
                
                if data.get('total', 0) <= params['offset']:
                    break
                
                time.sleep(1)  # 遵守速率限制
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Semantic Scholar API请求失败: {e}")
                break
        
        return papers[:max_results]
    
    def _parse_semantic_scholar_paper(self, item: Dict) -> Optional[Dict]:
        """解析Semantic Scholar论文数据"""
        try:
            authors = [a.get('name', '') for a in item.get('authors', [])[:10]]
            
            # 提取DOI
            doi = ''
            external_ids = item.get('externalIds', {})
            if external_ids:
                doi = external_ids.get('DOI', '')
            
            # 领域作为关键词
            keywords = [f.lower() for f in item.get('fieldsOfStudy', []) if f]
            
            return {
                'id': item.get('paperId', ''),
                'doi': doi,
                'title': item.get('title', ''),
                'authors': authors,
                'year': item.get('year'),
                'journal': item.get('venue', ''),
                'abstract': item.get('abstract', ''),
                'keywords': keywords,
                'citations': item.get('citationCount', 0),
                'source': 'semantic_scholar'
            }
        except Exception as e:
            logger.debug(f"解析论文失败: {e}")
            return None
    
    def _fetch_from_crossref(self, keywords: List[str], year_start: int,
                            year_end: int, max_results: int) -> List[Dict]:
        """从Crossref获取数据"""
        papers = []
        query = ' '.join(keywords)
        
        params = {
            'query': query,
            'filter': f"from-pub-date:{year_start},until-pub-date:{year_end},type:journal-article",
            'rows': min(100, max_results),
            'offset': 0,
            'select': 'DOI,title,author,published-print,container-title,abstract,is-referenced-by-count,subject'
        }
        
        while len(papers) < max_results:
            try:
                response = self.session.get(
                    f"{self.crossref_base}/works",
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                
                items = data.get('message', {}).get('items', [])
                if not items:
                    break
                
                for item in items:
                    paper = self._parse_crossref_paper(item)
                    if paper:
                        papers.append(paper)
                
                params['offset'] += len(items)
                
                total = data.get('message', {}).get('total-results', 0)
                if total <= params['offset']:
                    break
                
                time.sleep(0.5)  # 礼貌性延迟
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Crossref API请求失败: {e}")
                break
        
        return papers[:max_results]
    
    def _parse_crossref_paper(self, item: Dict) -> Optional[Dict]:
        """解析Crossref论文数据"""
        try:
            # 提取作者
            authors = []
            for author in item.get('author', [])[:10]:
                name_parts = []
                if author.get('given'):
                    name_parts.append(author['given'])
                if author.get('family'):
                    name_parts.append(author['family'])
                if name_parts:
                    authors.append(' '.join(name_parts))
            
            # 提取年份
            year = None
            published = item.get('published-print') or item.get('published-online')
            if published and published.get('date-parts'):
                date_parts = published['date-parts'][0]
                if date_parts:
                    year = date_parts[0]
            
            # 提取标题
            title = ''
            if item.get('title'):
                title = item['title'][0] if isinstance(item['title'], list) else item['title']
            
            # 提取期刊
            journal = ''
            if item.get('container-title'):
                journal = item['container-title'][0] if isinstance(item['container-title'], list) else item['container-title']
            
            return {
                'id': item.get('DOI', ''),
                'doi': item.get('DOI', ''),
                'title': title,
                'authors': authors,
                'year': year,
                'journal': journal,
                'abstract': item.get('abstract', ''),
                'keywords': [s.lower() for s in item.get('subject', [])],
                'citations': item.get('is-referenced-by-count', 0),
                'source': 'crossref'
            }
        except Exception as e:
            logger.debug(f"解析论文失败: {e}")
            return None
    
    def fetch_tourism_journals(self, year_start: int = 2024, year_end: int = 2026,
                               max_per_journal: int = 100) -> List[Dict]:
        """专门获取旅游类SSCI期刊的论文"""
        all_papers = []
        
        for journal_name, journal_id in self.tourism_journals.items():
            logger.info(f"正在获取 {journal_name} 的论文...")
            
            params = {
                'filter': f"primary_location.source.id:{journal_id},publication_year:{year_start}-{year_end},has_abstract:true",
                'per_page': min(200, max_per_journal),
                'sort': 'publication_date:desc',
                'select': 'id,doi,title,publication_year,abstract_inverted_index,authorships,primary_location,cited_by_count,concepts,keywords'
            }
            
            try:
                response = self.session.get(
                    f"{self.openalex_base}/works",
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                
                for item in data.get('results', []):
                    paper = self._parse_openalex_paper(item)
                    if paper:
                        all_papers.append(paper)
                
                logger.info(f"  获取到 {len(data.get('results', []))} 篇")
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"获取 {journal_name} 失败: {e}")
        
        return all_papers
    
    def generate_demo_data(self, n: int = 200) -> List[Dict]:
        """生成演示数据用于测试"""
        logger.info("生成演示数据...")
        
        # 模拟的研究主题
        topics = [
            ("Generative AI in Tourism", ["generative ai", "chatgpt", "tourism marketing", "customer service", "personalization"]),
            ("Virtual Reality Tourism", ["virtual reality", "augmented reality", "immersive experience", "destination marketing", "vr tourism"]),
            ("Sustainable Tourism", ["sustainable tourism", "eco-tourism", "carbon footprint", "green hotel", "environmental impact"]),
            ("Tourist Behavior", ["tourist behavior", "decision making", "travel motivation", "consumer behavior", "tourist satisfaction"]),
            ("Smart Tourism", ["smart tourism", "iot", "big data", "smart destination", "technology adoption"]),
            ("Post-COVID Tourism", ["covid-19", "recovery", "travel restrictions", "health safety", "resilience"]),
            ("Social Media Tourism", ["social media", "instagram", "influencer", "user generated content", "electronic word of mouth"]),
            ("Heritage Tourism", ["cultural heritage", "heritage site", "authenticity", "tourist experience", "cultural tourism"])
        ]
        
        journals = list(self.tourism_journals.keys())
        years = [2024, 2025, 2026]
        
        papers = []
        for i in range(n):
            topic_name, topic_keywords = random.choice(topics)
            year = random.choices(years, weights=[0.3, 0.4, 0.3])[0]
            
            # 生成模拟论文
            paper = {
                'id': f'demo_{i}',
                'doi': f'10.1000/demo.{year}.{i}',
                'title': f"{topic_name}: A {random.choice(['Systematic Review', 'Empirical Study', 'Case Study', 'Conceptual Framework', 'Mixed-Methods Analysis'])} of {random.choice(['Chinese', 'European', 'American', 'Asian', 'Global'])} {random.choice(['Tourists', 'Hotels', 'Destinations', 'Travel Agencies', 'Airlines'])}",
                'authors': [f"Author {j}" for j in range(random.randint(2, 5))],
                'year': year,
                'journal': random.choice(journals),
                'abstract': self._generate_demo_abstract(topic_name, topic_keywords),
                'keywords': random.sample(topic_keywords, min(4, len(topic_keywords))) + random.sample(['tourism', 'hospitality', 'travel', 'experience'], 2),
                'citations': random.randint(0, 150) if year < 2026 else random.randint(0, 20),
                'source': 'demo',
                'limitations_future_research': self._generate_demo_limitations()
            }
            papers.append(paper)
        
        logger.info(f"生成了 {len(papers)} 篇演示论文")
        return papers
    
    def _generate_demo_abstract(self, topic: str, keywords: List[str]) -> str:
        """生成模拟摘要"""
        templates = [
            f"This study examines the impact of {keywords[0]} on the tourism industry. Using {random.choice(['quantitative', 'qualitative', 'mixed-methods'])} research design, we analyzed data from {random.randint(200, 1000)} respondents. Results indicate that {keywords[1]} significantly influences tourist satisfaction. The findings have important implications for {random.choice(['destination marketing', 'hospitality management', 'tourism policy'])}. Limitations include sample size and geographic scope. Future research should explore {keywords[2]} in different cultural contexts.",
            f"The purpose of this research is to investigate how {keywords[0]} transforms tourist experiences. Drawing on {random.choice(['technology acceptance model', 'service quality theory', 'consumer behavior theory'])}, we propose a conceptual framework. An empirical study of {random.randint(150, 500)} tourists validates our model. Key findings suggest that {keywords[1]} enhances {random.choice(['engagement', 'satisfaction', 'loyalty'])}. This study contributes to the literature on {topic.lower()} and provides practical recommendations for industry practitioners.",
            f"Tourism scholars have increasingly focused on {keywords[0]}, yet limited research examines its relationship with {keywords[1]}. This paper addresses this gap through a {random.choice(['systematic literature review', 'meta-analysis', 'longitudinal study'])}. We identified {random.randint(50, 200)} relevant articles published between 2020 and 2026. Our analysis reveals emerging trends in {keywords[2]} research. The study concludes with a research agenda highlighting opportunities for future investigation."
        ]
        return random.choice(templates)
    
    def _generate_demo_limitations(self) -> str:
        """生成模拟的研究局限性和未来研究建议"""
        limitations = [
            "This study has several limitations that future research should address. First, the sample was limited to a single country, reducing generalizability. Second, the cross-sectional design prevents causal inferences. Third, we relied on self-reported data which may be subject to social desirability bias.",
            "Despite its contributions, this research has limitations. The convenience sampling method may limit representativeness. Additionally, the study focused solely on leisure tourists, excluding business travelers. Future studies should employ probability sampling and include diverse traveler segments.",
            "Several limitations warrant consideration. The study was conducted during the post-pandemic period, which may have influenced tourist behavior. The reliance on online surveys excluded tourists without internet access. The measurement scales, while validated, may not capture all dimensions of the construct."
        ]
        
        future_research = [
            "Future research should investigate the long-term effects of generative AI on tourist decision-making. Cross-cultural studies comparing AI adoption in Western and Asian markets would be valuable. Longitudinal designs tracking behavioral changes over time are recommended.",
            "Several avenues for future research emerge from this study. Researchers should explore how virtual reality experiences translate into actual travel intentions. The role of social presence in VR tourism deserves further attention. Mixed-methods approaches combining experimental and ethnographic methods are encouraged.",
            "This study opens opportunities for future investigation. The impact of sustainability certifications on tourist trust requires further examination. Research on the effectiveness of different green marketing strategies across market segments would be valuable. Action research involving industry collaboration is recommended."
        ]
        
        return random.choice(limitations) + " " + random.choice(future_research)
