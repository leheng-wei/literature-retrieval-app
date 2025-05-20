from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin, quote_plus

def search_baidu_xueshu(query, max_results=5):
    search_url = f"https://xueshu.baidu.com/s?wd={quote_plus(query)}"

    options = Options()
    options.add_argument('--headless')  # 无头模式
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)

    try:
        driver.get(search_url)
        time.sleep(3)  # 等待页面加载
        html = driver.page_source
    except Exception as e:
        print(f"Selenium 获取页面失败: {e}")
        driver.quit()
        return []
    finally:
        driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    results = []
    containers = soup.find_all('div', class_='result') or soup.find_all('div', class_='c_content')

    for item in containers[:max_results]:
        try:
            title_tag = item.find('h3')
            if not title_tag or not title_tag.find('a'):
                continue
            title = title_tag.get_text(strip=True)
            href = title_tag.find('a')['href']
            if not href.startswith("http"):
                href = urljoin("https://xueshu.baidu.com", href)

            abstract_tag = item.find('div', class_=re.compile(r'abstract|c-abstract'))
            abstract = abstract_tag.get_text(strip=True).replace("摘要：", "") if abstract_tag else "N/A"

            info_div = item.find('div', class_=re.compile(r'sc_info|c-subtext|author_text'))
            authors, journal, year = "N/A", "N/A", "N/A"
            if info_div:
                text = info_div.get_text(" ", strip=True)
                authors_match = re.findall(r'[\u4e00-\u9fa5]{2,4}', text)
                authors = ", ".join(authors_match[:5]) if authors_match else "N/A"
                journal_match = re.search(r'[《](.*?)[》]', text)
                if journal_match:
                    journal = journal_match.group(1)
                year_match = re.search(r'(19|20)\\d{2}', text)
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
            print(f"解析文献失败: {e}")
            continue

    print(f"[Selenium-Baidu] 获取到 {len(results)} 条文献")
    return results
