from googletrans import Translator
import pandas as pd
import time
from typing import List, Dict

# 翻译配置
TRANSLATOR = Translator(service_urls=['translate.google.com'])
TRANSLATION_DELAY = 1  # 秒

def translate_text(text: str, target_lang: str = 'zh-cn') -> str:
    """翻译文本到目标语言"""
    if not text or text == "N/A":
        return "N/A"
    
    try:
        time.sleep(TRANSLATION_DELAY)
        return TRANSLATOR.translate(text, dest=target_lang).text
    except Exception:
        return "N/A"

def load_impact_factors(filepath: str) -> dict:
    """加载期刊影响因子数据"""
    try:
        df = pd.read_excel(filepath)
        return dict(zip(df['Journal'], df['Impact Factor']))
    except Exception:
        return {}

def get_impact_factor(journal: str, impact_data: dict) -> str:
    """获取期刊影响因子"""
    return impact_data.get(journal, "N/A")

def process_articles_common(articles: List[dict]) -> List[dict]:
    """标准化文章数据结构"""
    required_fields = [
        "PMID", "Title", "Title (中文翻译版)", "Abstract", "Abstract (中文翻译版)",
        "Publication Date", "Authors", "Journal", "Impact Factor",
        "Article Type", "Keywords", "DOI", "Full Text Link"
    ]
    
    return [{
        field: article.get(field, "N/A")
        for field in required_fields
    } for article in articles]
