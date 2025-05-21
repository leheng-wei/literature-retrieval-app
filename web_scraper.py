
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote_plus, urljoin

# --- 百度学术 ---
def search_baidu_xueshu(query, max_results=5):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
    }
    url = f"https://xueshu.baidu.com/s?wd={quote_plus(query)}"

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"[Baidu学术] 请求失败: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    containers = soup.find_all("div", class_=re.compile(r"result|sc_content|c_content"))
    if not containers:
        print("[Baidu学术] 没有找到有效结果容器")
        return []

    for item in containers[:max_results]:
        try:
            title_tag = item.find("h3")
            if not title_tag or not title_tag.find("a"):
                continue
            title = title_tag.get_text(strip=True)
            href = title_tag.find("a")["href"]
            if not href.startswith("http"):
                href = urljoin("https://xueshu.baidu.com", href)

            abstract_tag = item.find("div", class_=re.compile("abstract|c_abstract|c-span18"))
            abstract = abstract_tag.get_text(strip=True).replace("摘要：", "") if abstract_tag else "N/A"

            info_tag = item.find("div", class_=re.compile("sc_info|author_text|c_subtext"))
            authors, journal, year = "N/A", "N/A", "N/A"
            if info_tag:
                text = info_tag.get_text(" ", strip=True)
                authors_match = re.findall(r'[一-龥]{2,4}', text)
                authors = ", ".join(authors_match[:5]) if authors_match else "N/A"
                journal_match = re.search(r'[《](.*?)[》]', text)
                if journal_match:
                    journal = journal_match.group(1)
                year_match = re.search(r'(19|20)\d{2}', text)
                if year_match:
                    year = year_match.group(0)

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
            print(f"解析文献出错: {e}")
            continue

    print(f"[Baidu学术] 成功获取 {len(results)} 条记录")
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
