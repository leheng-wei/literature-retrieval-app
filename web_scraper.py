import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote_plus, urljoin

# --- 万方数据替代CNKI ---
def search_wanfang(query, max_results=5):
    search_url = f"http://s.wanfangdata.com.cn/Paper.aspx?q={quote_plus(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/91.0 Safari/537.36"
    }

    try:
        response = requests.get(search_url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"[万方] 请求失败: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    articles = soup.find_all("div", class_="record-item")[:max_results]
    if not articles:
        print("[万方] 没有找到文章结果")
        return []

    for art in articles:
        try:
            # 标题和链接
            title_tag = art.find("a", class_="title")
            title = title_tag.get_text(strip=True)
            href = title_tag["href"]
            if not href.startswith("http"):
                href = urljoin("http://www.wanfangdata.com.cn/", href)

            # 作者信息
            authors_tag = art.find("div", class_="authors")
            authors = authors_tag.get_text(strip=True).replace("作者：", "") if authors_tag else "N/A"

            # 期刊和年份信息
            source_tag = art.find("div", class_="source")
            journal, year = "N/A", "N/A"
            if source_tag:
                text = source_tag.get_text(strip=True)
                journal_match = re.search(r"《(.*?)》", text)
                if journal_match:
                    journal = journal_match.group(1)
                year_match = re.search(r"(19|20)\d{2}", text)
                if year_match:
                    year = year_match.group(0)

            # 摘要
            abstract_tag = art.find("div", class_="abstract")
            abstract = abstract_tag.get_text(strip=True).replace("摘要：", "") if abstract_tag else "N/A"

            # DOI
            doi_tag = art.find("div", class_="doi")
            doi = doi_tag.get_text(strip=True).replace("DOI：", "") if doi_tag else "N/A"

            results.append({
                "Title": title,
                "Title (中文翻译版)": title,  # 万方是中文文献，不需要翻译
                "Abstract": abstract,
                "Abstract (中文翻译版)": abstract,  # 同上
                "Publication Date": year,
                "Authors": authors,
                "DOI": doi,
                "Article Type": "N/A",  # 万方搜索结果不直接提供文章类型
                "Journal": journal,
                "Impact Factor": "N/A",  # 需要后续处理
                "Keywords": "N/A",  # 万方搜索结果不直接提供关键词
                "Full Text Link": href
            })
        except Exception as e:
            print(f"[万方] 解析出错: {e}")
            continue

    print(f"[万方] 获取成功，共 {len(results)} 条文献")
    return results

# --- 请求工具函数 ---
def make_request(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or 'utf-8'
        return resp.text
    except Exception as e:
        print(f"Request failed: {e}")
        return None

# --- NMPA ---
def search_nmpa_news(query, max_results=5):
    base_url = "https://www.nmpa.gov.cn"
    list_url = f"{base_url}/xwzh/zhyw/index.html"
    html = make_request(list_url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a", href=True)
    results = []
    for link in links:
        if len(results) >= max_results:
            break
        title = link.get_text(strip=True)
        href = link['href']
        if not title or query not in title:
            continue
        if not href.startswith("http"):
            href = urljoin(base_url, href)
        results.append({
            "Title": title,
            "Link": href,
            "Source": "NMPA",
            "Publication Date": "N/A",
            "Summary": "N/A"
        })
    return results

# --- FDA ---
def search_fda_news(query, max_results=5):
    search_url = f"https://www.fda.gov/search?s={quote_plus(query)}"
    html = make_request(search_url)
    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    articles = soup.select("div.views-row")
    results = []
    for item in articles[:max_results]:
        try:
            title_tag = item.find('a')
            title = title_tag.get_text(strip=True)
            href = urljoin("https://www.fda.gov", title_tag['href'])
            summary = item.get_text(strip=True)
            results.append({
                "Title": title,
                "Link": href,
                "Source": "FDA",
                "Publication Date": "N/A",
                "Summary": summary[:300]
            })
        except:
            continue
    return results

# --- WHO ---
def search_who_news(query, max_results=5):
    search_url = f"https://www.who.int/news-room/search?query={quote_plus(query)}"
    html = make_request(search_url)
    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    items = soup.select("div.sf-result-item")
    results = []
    for item in items[:max_results]:
        try:
            title_tag = item.find("a", class_="sf-result-item-link")
            title = title_tag.get_text(strip=True)
            href = urljoin("https://www.who.int", title_tag["href"])
            summary_tag = item.find("div", class_="sf-result-item-summary")
            summary = summary_tag.get_text(strip=True) if summary_tag else "N/A"
            results.append({
                "Title": title,
                "Link": href,
                "Source": "WHO",
                "Publication Date": "N/A",
                "Summary": summary
            })
        except:
            continue
    return results
