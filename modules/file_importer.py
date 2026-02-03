"""
文件导入模块
支持导入多种学术数据库导出格式

支持格式：
1. Web of Science 导出文件 (.txt, .bib)
2. Scopus 导出文件 (.csv, .bib)
3. 通用CSV格式
4. RIS格式
5. BibTeX格式
"""

import csv
import re
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class FileImporter:
    """学术文献文件导入器"""
    
    def __init__(self):
        pass
    
    def import_wos(self, filepath: str) -> List[Dict]:
        """
        导入Web of Science导出文件
        
        支持格式：
        - Plain Text (Tab-delimited) - .txt
        - BibTeX - .bib
        
        WoS字段说明：
        - TI: Title (标题)
        - AU: Authors (作者)
        - PY: Publication Year (发表年份)
        - SO: Source (期刊名)
        - AB: Abstract (摘要)
        - DE: Author Keywords (作者关键词)
        - ID: Keywords Plus (WoS关键词)
        - TC: Times Cited (被引次数)
        - DI: DOI
        - FX: Funding Text (资助信息，常包含limitations)
        """
        filepath = Path(filepath)
        
        if filepath.suffix.lower() == '.bib':
            return self._import_bibtex(filepath)
        
        papers = []
        current_paper = {}
        current_field = None
        
        try:
            # 尝试多种编码
            for encoding in ['utf-8', 'utf-16', 'latin-1', 'cp1252']:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                logger.error(f"无法解码文件: {filepath}")
                return []
            
            lines = content.split('\n')
            
            for line in lines:
                # 跳过空行
                if not line.strip():
                    continue
                
                # 检查是否是新字段（两个大写字母开头）
                if len(line) >= 2 and line[:2].isupper() and (len(line) < 3 or line[2] == ' '):
                    field_code = line[:2].strip()
                    field_value = line[3:].strip() if len(line) > 3 else ''
                    
                    # 新记录开始
                    if field_code == 'PT' and current_paper:
                        paper = self._parse_wos_paper(current_paper)
                        if paper:
                            papers.append(paper)
                        current_paper = {}
                    
                    # 记录结束
                    if field_code == 'ER':
                        paper = self._parse_wos_paper(current_paper)
                        if paper:
                            papers.append(paper)
                        current_paper = {}
                        current_field = None
                        continue
                    
                    current_field = field_code
                    
                    # 处理多值字段
                    if field_code in ['AU', 'AF', 'DE', 'ID', 'C1']:
                        if field_code not in current_paper:
                            current_paper[field_code] = []
                        if field_value:
                            current_paper[field_code].append(field_value)
                    else:
                        current_paper[field_code] = field_value
                
                # 续行（以空格开头）
                elif line.startswith('   ') and current_field:
                    field_value = line.strip()
                    if current_field in ['AU', 'AF', 'DE', 'ID', 'C1']:
                        if field_value:
                            current_paper[current_field].append(field_value)
                    else:
                        current_paper[current_field] = current_paper.get(current_field, '') + ' ' + field_value
            
            # 处理最后一篇
            if current_paper:
                paper = self._parse_wos_paper(current_paper)
                if paper:
                    papers.append(paper)
            
            logger.info(f"从WoS文件导入 {len(papers)} 篇论文")
            return papers
            
        except Exception as e:
            logger.error(f"导入WoS文件失败: {e}")
            return []
    
    def _parse_wos_paper(self, record: Dict) -> Optional[Dict]:
        """解析WoS记录"""
        try:
            # 提取作者
            authors = record.get('AF', record.get('AU', []))
            if isinstance(authors, str):
                authors = [authors]
            
            # 提取关键词
            keywords = []
            for kw_field in ['DE', 'ID']:
                kws = record.get(kw_field, [])
                if isinstance(kws, str):
                    kws = [kws]
                keywords.extend([k.lower().strip() for k in kws])
            
            # 提取年份
            year = None
            if record.get('PY'):
                try:
                    year = int(record['PY'])
                except ValueError:
                    pass
            
            # 提取被引次数
            citations = 0
            if record.get('TC'):
                try:
                    citations = int(record['TC'])
                except ValueError:
                    pass
            
            return {
                'id': record.get('UT', record.get('DI', '')),
                'doi': record.get('DI', ''),
                'title': record.get('TI', ''),
                'authors': authors,
                'year': year,
                'journal': record.get('SO', ''),
                'abstract': record.get('AB', ''),
                'keywords': list(set(keywords)),
                'citations': citations,
                'source': 'wos',
                'volume': record.get('VL', ''),
                'issue': record.get('IS', ''),
                'pages': record.get('BP', '') + '-' + record.get('EP', '') if record.get('BP') else '',
                'affiliations': record.get('C1', [])
            }
        except Exception as e:
            logger.debug(f"解析WoS记录失败: {e}")
            return None
    
    def import_scopus(self, filepath: str) -> List[Dict]:
        """
        导入Scopus导出文件
        
        支持格式：
        - CSV格式
        - BibTeX格式
        
        Scopus CSV字段：
        - Title: 标题
        - Authors: 作者
        - Year: 年份
        - Source title: 期刊名
        - Abstract: 摘要
        - Author Keywords: 作者关键词
        - Index Keywords: 索引关键词
        - Cited by: 被引次数
        - DOI: DOI
        """
        filepath = Path(filepath)
        
        if filepath.suffix.lower() == '.bib':
            return self._import_bibtex(filepath)
        
        papers = []
        
        try:
            # 尝试多种编码
            for encoding in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        # 检测分隔符
                        sample = f.read(8192)
                        f.seek(0)
                        
                        dialect = csv.Sniffer().sniff(sample, delimiters=',;\t')
                        reader = csv.DictReader(f, dialect=dialect)
                        
                        for row in reader:
                            paper = self._parse_scopus_row(row)
                            if paper:
                                papers.append(paper)
                    break
                except (UnicodeDecodeError, csv.Error):
                    continue
            
            logger.info(f"从Scopus文件导入 {len(papers)} 篇论文")
            return papers
            
        except Exception as e:
            logger.error(f"导入Scopus文件失败: {e}")
            return []
    
    def _parse_scopus_row(self, row: Dict) -> Optional[Dict]:
        """解析Scopus CSV行"""
        try:
            # 字段名可能有变化，尝试多种
            def get_field(possible_names, default=''):
                for name in possible_names:
                    # 精确匹配
                    if name in row:
                        return row[name]
                    # 不区分大小写匹配
                    for key in row.keys():
                        if key.lower() == name.lower():
                            return row[key]
                return default
            
            # 提取作者
            authors_str = get_field(['Authors', 'Author(s)', 'Author'])
            authors = [a.strip() for a in authors_str.split(';') if a.strip()] if authors_str else []
            
            # 提取关键词
            keywords = []
            for kw_field in ['Author Keywords', 'Index Keywords', 'Keywords']:
                kws = get_field([kw_field])
                if kws:
                    keywords.extend([k.lower().strip() for k in kws.split(';') if k.strip()])
            
            # 提取年份
            year = None
            year_str = get_field(['Year', 'Publication Year'])
            if year_str:
                try:
                    year = int(year_str)
                except ValueError:
                    pass
            
            # 提取被引次数
            citations = 0
            cite_str = get_field(['Cited by', 'Times Cited', 'Citation Count'])
            if cite_str:
                try:
                    citations = int(cite_str)
                except ValueError:
                    pass
            
            return {
                'id': get_field(['EID', 'Document ID', 'ID']),
                'doi': get_field(['DOI']),
                'title': get_field(['Title', 'Document Title']),
                'authors': authors,
                'year': year,
                'journal': get_field(['Source title', 'Journal', 'Source']),
                'abstract': get_field(['Abstract']),
                'keywords': list(set(keywords)),
                'citations': citations,
                'source': 'scopus',
                'volume': get_field(['Volume']),
                'issue': get_field(['Issue']),
                'pages': get_field(['Page start', 'Pages']),
                'affiliations': [a.strip() for a in get_field(['Affiliations']).split(';') if a.strip()]
            }
        except Exception as e:
            logger.debug(f"解析Scopus行失败: {e}")
            return None
    
    def import_csv(self, filepath: str) -> List[Dict]:
        """
        导入通用CSV格式
        
        期望的列名（不区分大小写）：
        - title: 标题
        - authors/author: 作者（分号分隔）
        - year: 年份
        - journal/source: 期刊
        - abstract: 摘要
        - keywords: 关键词（分号分隔）
        - citations/cited: 被引次数
        - doi: DOI
        """
        papers = []
        
        try:
            for encoding in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        dialect = csv.Sniffer().sniff(f.read(8192), delimiters=',;\t')
                        f.seek(0)
                        reader = csv.DictReader(f, dialect=dialect)
                        
                        for row in reader:
                            paper = self._parse_generic_csv_row(row)
                            if paper:
                                papers.append(paper)
                    break
                except (UnicodeDecodeError, csv.Error):
                    continue
            
            logger.info(f"从CSV文件导入 {len(papers)} 篇论文")
            return papers
            
        except Exception as e:
            logger.error(f"导入CSV文件失败: {e}")
            return []
    
    def _parse_generic_csv_row(self, row: Dict) -> Optional[Dict]:
        """解析通用CSV行"""
        try:
            # 标准化列名
            normalized = {k.lower().strip(): v for k, v in row.items()}
            
            def get_val(*keys, default=''):
                for k in keys:
                    if k in normalized and normalized[k]:
                        return normalized[k]
                return default
            
            # 解析作者
            authors_str = get_val('authors', 'author')
            authors = [a.strip() for a in authors_str.split(';') if a.strip()] if authors_str else []
            
            # 解析关键词
            kw_str = get_val('keywords', 'keyword', 'author keywords')
            keywords = [k.lower().strip() for k in kw_str.split(';') if k.strip()] if kw_str else []
            
            # 解析年份
            year = None
            year_str = get_val('year', 'publication year', 'pub year')
            if year_str:
                try:
                    year = int(year_str)
                except ValueError:
                    pass
            
            # 解析被引次数
            citations = 0
            cite_str = get_val('citations', 'cited', 'cited by', 'times cited')
            if cite_str:
                try:
                    citations = int(cite_str)
                except ValueError:
                    pass
            
            return {
                'id': get_val('id', 'eid', 'uid'),
                'doi': get_val('doi'),
                'title': get_val('title'),
                'authors': authors,
                'year': year,
                'journal': get_val('journal', 'source', 'source title'),
                'abstract': get_val('abstract'),
                'keywords': list(set(keywords)),
                'citations': citations,
                'source': 'csv'
            }
        except Exception as e:
            logger.debug(f"解析CSV行失败: {e}")
            return None
    
    def _import_bibtex(self, filepath: str) -> List[Dict]:
        """导入BibTeX格式"""
        papers = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单的BibTeX解析
            entries = re.findall(r'@\w+\{([^@]+)\}', content, re.DOTALL)
            
            for entry in entries:
                paper = self._parse_bibtex_entry(entry)
                if paper:
                    papers.append(paper)
            
            logger.info(f"从BibTeX文件导入 {len(papers)} 篇论文")
            return papers
            
        except Exception as e:
            logger.error(f"导入BibTeX文件失败: {e}")
            return []
    
    def _parse_bibtex_entry(self, entry: str) -> Optional[Dict]:
        """解析BibTeX条目"""
        try:
            # 提取键值对
            fields = {}
            
            # 提取条目ID
            entry_id = entry.split(',')[0].strip()
            fields['id'] = entry_id
            
            # 提取字段
            pattern = r'(\w+)\s*=\s*[\{\"](.+?)[\}\"](?:,|\s*$)'
            matches = re.findall(pattern, entry, re.DOTALL)
            
            for key, value in matches:
                fields[key.lower()] = value.replace('\n', ' ').strip()
            
            # 解析作者
            authors = []
            if 'author' in fields:
                # BibTeX用 "and" 分隔作者
                authors = [a.strip() for a in fields['author'].split(' and ') if a.strip()]
            
            # 解析关键词
            keywords = []
            for kw_field in ['keywords', 'keyword']:
                if kw_field in fields:
                    keywords.extend([k.lower().strip() for k in fields[kw_field].split(',') if k.strip()])
            
            # 解析年份
            year = None
            if 'year' in fields:
                try:
                    year = int(fields['year'])
                except ValueError:
                    pass
            
            return {
                'id': entry_id,
                'doi': fields.get('doi', ''),
                'title': fields.get('title', ''),
                'authors': authors,
                'year': year,
                'journal': fields.get('journal', fields.get('booktitle', '')),
                'abstract': fields.get('abstract', ''),
                'keywords': list(set(keywords)),
                'citations': 0,
                'source': 'bibtex'
            }
        except Exception as e:
            logger.debug(f"解析BibTeX条目失败: {e}")
            return None
    
    def import_ris(self, filepath: str) -> List[Dict]:
        """
        导入RIS格式
        
        RIS标签：
        - TI: 标题
        - AU/A1: 作者
        - PY/Y1: 年份
        - JO/JF/T2: 期刊
        - AB/N2: 摘要
        - KW: 关键词
        - DO: DOI
        """
        papers = []
        current_paper = {}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    # RIS格式: XX  - value
                    match = re.match(r'^([A-Z][A-Z0-9])\s+-\s+(.*)$', line)
                    
                    if match:
                        tag, value = match.groups()
                        
                        # 记录结束
                        if tag == 'ER':
                            if current_paper:
                                paper = self._parse_ris_record(current_paper)
                                if paper:
                                    papers.append(paper)
                            current_paper = {}
                            continue
                        
                        # 多值字段
                        if tag in ['AU', 'A1', 'KW']:
                            if tag not in current_paper:
                                current_paper[tag] = []
                            current_paper[tag].append(value)
                        else:
                            current_paper[tag] = value
            
            logger.info(f"从RIS文件导入 {len(papers)} 篇论文")
            return papers
            
        except Exception as e:
            logger.error(f"导入RIS文件失败: {e}")
            return []
    
    def _parse_ris_record(self, record: Dict) -> Optional[Dict]:
        """解析RIS记录"""
        try:
            # 作者
            authors = record.get('AU', record.get('A1', []))
            if isinstance(authors, str):
                authors = [authors]
            
            # 关键词
            keywords = record.get('KW', [])
            if isinstance(keywords, str):
                keywords = [keywords]
            keywords = [k.lower() for k in keywords]
            
            # 年份
            year = None
            year_str = record.get('PY', record.get('Y1', ''))
            if year_str:
                try:
                    year = int(year_str[:4])
                except ValueError:
                    pass
            
            return {
                'id': record.get('ID', record.get('DO', '')),
                'doi': record.get('DO', ''),
                'title': record.get('TI', record.get('T1', '')),
                'authors': authors,
                'year': year,
                'journal': record.get('JO', record.get('JF', record.get('T2', ''))),
                'abstract': record.get('AB', record.get('N2', '')),
                'keywords': list(set(keywords)),
                'citations': 0,
                'source': 'ris'
            }
        except Exception as e:
            logger.debug(f"解析RIS记录失败: {e}")
            return None
    
    def detect_format(self, filepath: str) -> str:
        """自动检测文件格式"""
        filepath = Path(filepath)
        suffix = filepath.suffix.lower()
        
        if suffix == '.bib':
            return 'bibtex'
        elif suffix == '.ris':
            return 'ris'
        elif suffix == '.csv':
            # 检查是否是Scopus格式
            try:
                with open(filepath, 'r', encoding='utf-8-sig') as f:
                    header = f.readline().lower()
                    if 'eid' in header or 'scopus' in header:
                        return 'scopus'
            except:
                pass
            return 'csv'
        elif suffix == '.txt':
            # 检查是否是WoS格式
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    first_line = f.readline()
                    if first_line.startswith('FN ') or first_line.startswith('PT '):
                        return 'wos'
            except:
                pass
            return 'txt'
        
        return 'unknown'
    
    def import_auto(self, filepath: str) -> List[Dict]:
        """自动检测格式并导入"""
        format_type = self.detect_format(filepath)
        
        if format_type == 'wos':
            return self.import_wos(filepath)
        elif format_type == 'scopus':
            return self.import_scopus(filepath)
        elif format_type == 'bibtex':
            return self._import_bibtex(filepath)
        elif format_type == 'ris':
            return self.import_ris(filepath)
        elif format_type == 'csv':
            return self.import_csv(filepath)
        else:
            logger.warning(f"未知文件格式: {filepath}")
            return self.import_csv(filepath)  # 尝试作为CSV导入
