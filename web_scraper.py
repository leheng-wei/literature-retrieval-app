
import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin, quote_plus

# --- 通用配置 ---
REQUEST_TIMEOUT = 15
REQUEST_DELAY = 2.0
COMMON_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
}

def make_request(url):
    try:
        response = requests.get(url, headers=COMMON_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or 'utf-8'
        return response.text
    except Exception as e:
        print(f"Request failed: {e}")
        return None

# --- 百度学术 ---
def search_baidu_xueshu(query, max_results=5):
    search_url = f"https://xueshu.baidu.com/s?wd={quote_plus(query)}"
    html = make_request(search_url)
    if not html:
        print("Empty response from Baidu.")
        return []

    soup = BeautifulSoup(html, 'html.parser')
    results = []

    candidate_selectors = [
        ('div', {'class': 'result sc_default_result xpath-log'}),
        ('div', {'class': 'sc_content'}),
        ('div', {'class': 'c_container'}),
        ('div', {'class': 'result'}),
        ('div', {})
    ]

    containers = []
    for tag, attrs in candidate_selectors:
        containers = soup.find_all(tag, attrs=attrs)
        if containers:
            break

    for item in containers[:max_results]:
        try:
            title_tag = item.find('h3') or item.find('a', href=True)
            if not title_tag:
                continue
            title_link = title_tag.find('a') if title_tag.name != 'a' else title_tag
            title = title_link.get_text(strip=True)
            href = title_link.get('href')
            if not href.startswith('http'):
                href = urljoin("https://xueshu.baidu.com", href)

            abstract_tag = item.find('div', class_=re.compile('abstract|c-abstract'))                          or item.find('p', class_=re.compile('abstract|c-abstract'))
            abstract = abstract_tag.get_text(strip=True).replace("摘要：", "") if abstract_tag else "N/A"

            info_div = item.find('div', class_=re.compile('sc_info|c_subtext|author_text'))
            authors = "N/A"
            journal = "N/A"
            year = "N/A"
            if info_div:
                text = info_div.get_text(" ", strip=True)
                authors_match = re.findall(r'[一-龥]{2,4}', text)
                authors = ", ".join(authors_match[:5]) if authors_match else "N/A"
                year_match = re.search(r'\b(20\d{2}|19\d{2})\b', text)
                if year_match:
                    year = year_match.group(0)
                journal_match = re.search(r'[《](.*?)[》]', text)
                if journal_match:
                    journal = journal_match.group(1)

            results.append({
                "Title": title,
                "Title (中文翻译版)": title,
                "Abstract": abstract,
                "Abstract (中文翻译版)": abstract,
                "Publication Date": year,
                "Authors": authors,
                "DOI": "N/A",
                "Article Type": "N/A",
                "Journal": journal,
                "Impact Factor": "N/A",
                "Keywords": "N/A",
                "Full Text Link": href
            })
        except Exception as e:
            print(f"Error parsing Baidu item: {e}")
            continue

    print(f"[Baidu学术] 抓取完成，获取到 {len(results)} 条结果。")
    return results

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
        if not title or not query in title:
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
