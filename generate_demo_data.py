#!/usr/bin/env python3
"""
示例数据生成器 - 生成用于测试的模拟论文数据
"""

import json
import random
import csv
from datetime import datetime, timedelta

# 旅游研究常见关键词库
KEYWORDS_POOL = {
    "technology": ["artificial intelligence", "ChatGPT", "virtual reality", "augmented reality", 
                   "machine learning", "big data", "smart tourism", "mobile technology",
                   "social media", "online review", "digital marketing", "e-tourism"],
    "behavior": ["tourist behavior", "travel motivation", "destination choice", "decision making",
                 "tourist satisfaction", "loyalty", "revisit intention", "word of mouth"],
    "sustainability": ["sustainable tourism", "eco-tourism", "overtourism", "carbon footprint",
                      "community tourism", "responsible tourism", "green hotel"],
    "experience": ["tourist experience", "memorable experience", "service quality", 
                   "destination image", "place attachment", "authenticity"],
    "marketing": ["destination marketing", "tourism branding", "influencer marketing",
                  "content marketing", "customer engagement"],
    "crisis": ["COVID-19", "pandemic recovery", "crisis management", "resilience", "risk perception"]
}

JOURNALS = [
    "Tourism Management",
    "Annals of Tourism Research", 
    "Journal of Travel Research",
    "International Journal of Hospitality Management",
    "Journal of Sustainable Tourism",
    "Tourism Geographies",
    "Current Issues in Tourism",
    "Journal of Destination Marketing & Management",
    "International Journal of Tourism Research"
]

AUTHORS = [
    "Li, X.", "Wang, Y.", "Zhang, H.", "Kim, J.", "Chen, S.",
    "Lee, H.", "Smith, J.", "Brown, M.", "Johnson, A.", "Williams, K.",
    "Garcia, L.", "Martinez, R.", "Anderson, P.", "Taylor, D.", "Thomas, E."
]

LIMITATIONS_TEMPLATES = [
    "This study has several limitations. First, the sample was collected only from {location}, limiting generalizability. Future research should extend to other contexts.",
    "The cross-sectional nature of this study limits causal inferences. Longitudinal studies are needed to examine temporal dynamics.",
    "Our study focused exclusively on {topic}. Future research should explore other dimensions such as {suggestion}.",
    "Data were collected during {period}, which may affect generalizability. Replication studies in normal conditions are warranted.",
    "The use of self-reported measures may introduce common method bias. Future studies should consider behavioral data."
]

FUTURE_RESEARCH_TEMPLATES = [
    "Future research should examine how {technology} influences {behavior} in different cultural contexts.",
    "Longitudinal studies are needed to understand the long-term effects of {phenomenon} on tourist {outcome}.",
    "Researchers could explore the moderating role of {factor} in the relationship between {var1} and {var2}.",
    "Experimental designs could help establish causality between {cause} and {effect}.",
    "Mixed-methods approaches combining quantitative and qualitative data would provide richer insights."
]

def generate_abstract(keywords):
    """生成模拟摘要"""
    templates = [
        "This study examines the impact of {kw1} on {kw2} in the context of tourism. Using a sample of {n} tourists from {location}, we employed structural equation modeling to test our hypotheses. Results indicate that {kw1} significantly influences {kw3}, with {kw2} playing a mediating role. Theoretical and practical implications are discussed.",
        "Drawing on the theory of planned behavior, this research investigates how {kw1} affects tourist {kw2}. A survey of {n} respondents revealed that {kw3} moderates the relationship between {kw1} and behavioral intentions. The findings contribute to our understanding of {kw2} in the digital age.",
        "This paper explores the role of {kw1} in shaping {kw2} among millennials. Through a mixed-methods approach, we found that {kw3} is a key determinant of tourist satisfaction. Implications for destination managers and future research directions are provided.",
        "Using big data analytics, we analyzed {n} online reviews to understand tourists' perceptions of {kw1}. Topic modeling revealed {num_topics} main themes, with {kw2} being the most frequently discussed. Sentiment analysis showed that attitudes toward {kw3} are becoming more positive.",
    ]
    
    template = random.choice(templates)
    kws = random.sample(keywords, min(3, len(keywords)))
    while len(kws) < 3:
        kws.append(random.choice(list(KEYWORDS_POOL.values())[0]))
    
    abstract = template.format(
        kw1=kws[0],
        kw2=kws[1] if len(kws) > 1 else "tourist behavior",
        kw3=kws[2] if len(kws) > 2 else "technology adoption",
        n=random.randint(200, 800),
        location=random.choice(["China", "USA", "Europe", "Southeast Asia", "Australia"]),
        num_topics=random.randint(5, 10)
    )
    
    # 添加Limitations和Future Research部分
    limitation = random.choice(LIMITATIONS_TEMPLATES).format(
        location=random.choice(["China", "the US", "Europe", "Asia"]),
        topic=kws[0],
        suggestion=random.choice(["customer emotions", "cultural factors", "long-term effects"]),
        period=random.choice(["the COVID-19 pandemic", "peak season", "a specific event"])
    )
    
    future = random.choice(FUTURE_RESEARCH_TEMPLATES).format(
        technology=random.choice(["AI", "VR", "social media", "chatbots"]),
        behavior=random.choice(["decision-making", "satisfaction", "loyalty", "experience"]),
        phenomenon=kws[0],
        outcome=random.choice(["satisfaction", "loyalty", "well-being"]),
        factor=random.choice(["age", "culture", "technology readiness"]),
        var1=kws[0],
        var2="tourist " + random.choice(["behavior", "satisfaction", "loyalty"]),
        cause=kws[0],
        effect="behavioral outcomes"
    )
    
    return f"{abstract}\n\n{limitation}\n\n{future}"


def generate_title(keywords):
    """生成论文标题"""
    templates = [
        "The impact of {kw1} on {kw2}: A {method} approach",
        "Exploring {kw1} in tourism: Evidence from {location}",
        "How does {kw1} influence {kw2}? The mediating role of {kw3}",
        "{kw1} and tourist {kw2}: A systematic review",
        "Understanding {kw1}: Implications for {kw2} in the post-pandemic era",
        "Rethinking {kw1}: A new framework for {kw2} research",
        "{kw1} in smart destinations: Antecedents and consequences",
    ]
    
    template = random.choice(templates)
    kws = random.sample(keywords, min(3, len(keywords)))
    while len(kws) < 3:
        kws.append(random.choice(["tourist experience", "destination marketing", "service quality"]))
    
    return template.format(
        kw1=kws[0],
        kw2=kws[1],
        kw3=kws[2] if len(kws) > 2 else "perceived value",
        method=random.choice(["SEM", "mixed-methods", "qualitative", "big data", "experimental"]),
        location=random.choice(["China", "Europe", "Asia Pacific", "North America"])
    )


def generate_demo_data(n_papers=200, output_file="demo_data.csv"):
    """生成示例论文数据"""
    papers = []
    
    # 生成时间范围 (2024-2026)
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2026, 1, 31)
    
    for i in range(n_papers):
        # 随机选择关键词类别和关键词
        categories = random.sample(list(KEYWORDS_POOL.keys()), random.randint(2, 4))
        keywords = []
        for cat in categories:
            keywords.extend(random.sample(KEYWORDS_POOL[cat], random.randint(1, 3)))
        keywords = list(set(keywords))[:6]  # 最多6个关键词
        
        # 随机日期
        random_days = random.randint(0, (end_date - start_date).days)
        pub_date = start_date + timedelta(days=random_days)
        
        # 被引次数（新文章被引少，旧文章可能被引多）
        days_since_pub = (datetime(2026, 2, 1) - pub_date).days
        max_citations = max(1, int(days_since_pub / 30))  # 大约每月最多获得1次引用
        citations = random.randint(0, max_citations * 2) if random.random() > 0.3 else random.randint(max_citations * 2, max_citations * 5)
        
        paper = {
            "title": generate_title(keywords),
            "authors": "; ".join(random.sample(AUTHORS, random.randint(2, 4))),
            "year": pub_date.year,
            "month": pub_date.month,
            "journal": random.choice(JOURNALS),
            "abstract": generate_abstract(keywords),
            "keywords": "; ".join(keywords),
            "citations": citations,
            "doi": f"10.1016/j.example.{pub_date.year}.{random.randint(100000, 999999)}"
        }
        papers.append(paper)
    
    # 保存为CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=papers[0].keys())
        writer.writeheader()
        writer.writerows(papers)
    
    print(f"✅ 已生成 {n_papers} 条示例数据: {output_file}")
    print(f"   时间范围: 2024-2026")
    print(f"   期刊数量: {len(JOURNALS)}")
    print(f"   关键词类别: {len(KEYWORDS_POOL)}")
    
    # 同时保存为JSON格式
    json_file = output_file.replace('.csv', '.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)
    print(f"   JSON版本: {json_file}")
    
    return papers


if __name__ == "__main__":
    import sys
    
    n = 200
    output = "demo_data.csv"
    
    if len(sys.argv) > 1:
        n = int(sys.argv[1])
    if len(sys.argv) > 2:
        output = sys.argv[2]
    
    generate_demo_data(n, output)
