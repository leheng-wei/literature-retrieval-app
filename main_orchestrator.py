import os
import pandas as pd
from pubmed_retriever import search_pubmed
from data_processor_fixed import (
    translate_text,
    load_impact_factors,
    get_impact_factor,
    process_articles_common,
    IMPACT_FACTOR_FILE_PATH
)

# 配置
USER_EMAIL = "your_email@example.com"  # 替换为您的邮箱
USER_API_KEY = "your_api_key"         # 替换为您的API密钥
OUTPUT_DIR = "output"

def save_to_excel(df, filename):
    """保存DataFrame到Excel"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)
    df.to_excel(filepath, index=False, engine="openpyxl")
    return filepath

def run_retrieval_workflow(query_en, time_period_str, max_pubmed_results=20):
    """执行完整检索流程"""
    # 加载影响因子数据
    impact_factors = load_impact_factors(IMPACT_FACTOR_FILE_PATH)
    
    # PubMed检索
    articles = search_pubmed(
        query=query_en,
        time_period_str=time_period_str,
        email=USER_EMAIL,
        api_key=USER_API_KEY,
        max_results=max_pubmed_results
    )
    
    # 处理结果
    processed_articles = []
    for article in articles:
        # 翻译标题和摘要
        article["Title (中文)"] = translate_text(article.get("Title", ""))
        article["Abstract (中文)"] = translate_text(article.get("Abstract", ""))
        
        # 获取影响因子
        journal = article.get("Journal", "")
        article["Impact Factor"] = get_impact_factor(journal, impact_factors)
        
        processed_articles.append(article)
    
    # 标准化数据格式
    final_data = process_articles_common(processed_articles)
    df = pd.DataFrame(final_data)
    
    # 确保列顺序
    columns = [
        "PMID", "Title", "Title (中文)", "Abstract", "Abstract (中文)",
        "Publication Date", "Authors", "Journal", "Impact Factor",
        "Article Type", "Keywords", "DOI", "Full Text Link"
    ]
    df = df[columns]
    
    # 保存结果
    return save_to_excel(df, "pubmed_results.xlsx")
