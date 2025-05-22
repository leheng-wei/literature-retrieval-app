from Bio import Entrez
import datetime
from typing import List, Dict, Optional  # 添加这行导入

def get_date_range(time_period: str) -> tuple:
    """根据中文时间描述返回日期范围"""
    today = datetime.date.today()
    periods = {
        "近一年": 365,
        "近六个月": 180,
        "近三个月": 90,
        "近一个月": 30,
        "近一周": 7
    }
    days = periods.get(time_period, 365)
    start_date = today - datetime.timedelta(days=days)
    return start_date.strftime("%Y/%m/%d"), today.strftime("%Y/%m/%d")

def parse_author(author: Dict) -> str:  # 使用Dict类型
    """解析单个作者信息"""
    if "CollectiveName" in author:
        return author["CollectiveName"]
    
    last = author.get("LastName", "")
    fore = author.get("ForeName", "")
    initials = author.get("Initials", "")
    
    if last and fore:
        return f"{last} {fore}"
    elif last and initials:
        return f"{last} {initials}"
    return last or fore or initials

def parse_authors(author_list: List[Dict]) -> str:  # 使用List和Dict类型
    """解析作者列表"""
    if not author_list:
        return "N/A"
    return ", ".join(filter(None, [parse_author(a) for a in author_list]))

def parse_keywords(article: Dict) -> str:  # 使用Dict类型
    """提取关键词"""
    keywords = set()
    
    # MeSH术语
    mesh = article.get("MedlineCitation", {}).get("MeshHeadingList", [])
    if mesh:
        for item in mesh:
            if "DescriptorName" in item:
                keywords.add(item["DescriptorName"])
    
    # 作者关键词
    kw_list = article.get("MedlineCitation", {}).get("Article", {}).get("KeywordList", [])
    if kw_list:
        for kw in kw_list:
            if "Keyword" in kw:
                keywords.add(kw["Keyword"])
    
    return ", ".join(sorted(keywords)) if keywords else "N/A"

def parse_article_type(article: Dict) -> str:  # 使用Dict类型
    """提取文献类型"""
    types = article.get("MedlineCitation", {}).get("Article", {}).get("PublicationTypeList", [])
    if types:
        return ", ".join([t for t in types if t])
    return "N/A"

def search_pubmed(query: str, time_period_str: str, email: str, api_key: str, max_results: int = 20) -> List[Dict]:  # 使用List和Dict类型
    """执行PubMed检索"""
    Entrez.email = email
    Entrez.api_key = api_key
    
    # 构建检索式
    mindate, maxdate = get_date_range(time_period_str)
    search_term = f"{query} AND ({mindate}[Date - Publication] : {maxdate}[Date - Publication])"
    
    # 执行检索
    try:
        # 第一步：获取PMID列表
        handle = Entrez.esearch(db="pubmed", term=search_term, retmax=max_results, sort="relevance")
        record = Entrez.read(handle)
        handle.close()
        
        if not record["IdList"]:
            return []
        
        # 第二步：获取详细记录
        handle = Entrez.efetch(db="pubmed", id=record["IdList"], retmode="xml")
        data = Entrez.read(handle)
        handle.close()
        
        # 解析结果
        results = []
        for article in data["PubmedArticle"]:
            medline = article["MedlineCitation"]
            article_data = medline["Article"]
            journal = article_data.get("Journal", {})
            
            results.append({
                "PMID": medline["PMID"],
                "Title": article_data["ArticleTitle"],
                "Abstract": " ".join([t for t in article_data.get("Abstract", {}).get("AbstractText", []) if t]),
                "Publication Date": journal.get("JournalIssue", {}).get("PubDate", ""),
                "Authors": parse_authors(article_data.get("AuthorList", [])),
                "Journal": journal.get("Title", ""),
                "Article Type": parse_article_type(article),
                "Keywords": parse_keywords(article),
                "DOI": next((id for id in article.get("PubmedData", {}).get("ArticleIdList", []) 
                           if id.attributes["IdType"] == "doi"), "N/A"),
                "Full Text Link": f"https://pubmed.ncbi.nlm.nih.gov/{medline['PMID']}/"
            })
        
        return results
        
    except Exception as e:
        print(f"PubMed检索错误: {str(e)}")
        return []
