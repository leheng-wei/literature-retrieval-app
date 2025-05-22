
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

# 搜索函数
def search_wanfang(query, max_results=10):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    url = f"https://s.wanfangdata.com.cn/paper?q={quote_plus(query)}"
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        st.error("请求失败，请稍后再试。")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    items = soup.select("div.result-item")[:max_results]

    results = []
    for item in items:
        try:
            title_tag = item.find("a", class_="title")
            title = title_tag.get_text(strip=True)
            link = title_tag["href"]

            summary_tag = item.find("p", class_="summary")
            summary = summary_tag.get_text(strip=True) if summary_tag else "N/A"

            author_tag = item.find("div", class_="author")
            authors = author_tag.get_text(strip=True) if author_tag else "N/A"

            source_tag = item.find("span", class_="source")
            source = source_tag.get_text(strip=True) if source_tag else "N/A"

            results.append({
                "标题": title,
                "摘要": summary,
                "作者": authors,
                "期刊": source,
                "链接": link
            })
        except Exception as e:
            st.warning(f"解析失败：{e}")
            continue

    return results


# Streamlit UI
st.set_page_config(page_title="万方文献搜索", layout="wide")

st.title("📚 万方中文文献检索工具")

query = st.text_input("请输入搜索关键词：", placeholder="例如：人工智能 医疗", max_chars=50)
max_results = st.slider("最多显示结果数：", 5, 50, 10)

if st.button("🔍 开始检索") and query.strip():
    with st.spinner("正在检索中，请稍候..."):
        data = search_wanfang(query.strip(), max_results=max_results)
        if data:
            df = pd.DataFrame(data)
            st.success(f"共获取到 {len(df)} 条结果。")
            st.dataframe(df, use_container_width=True)

            # 下载按钮
            st.download_button(
                label="📥 下载为 Excel 文件",
                data=df.to_excel(index=False, engine='openpyxl'),
                file_name=f"万方文献_{query}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("未获取到任何文献数据。")


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
