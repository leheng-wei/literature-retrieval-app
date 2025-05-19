# web_scraper.py - Module for scraping Chinese literature and policy information
import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin, quote_plus

# --- Configuration ---
REQUEST_TIMEOUT = 15 # seconds, increased timeout
REQUEST_DELAY = 1.5 # second between requests to the same domain, slightly increased
COMMON_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
}

# --- Helper Functions ---
def make_request(url, headers=None, params=None, method='GET', data=None):
    """Makes a request to the given URL with appropriate error handling."""
    try:
        full_headers = COMMON_HEADERS.copy()
        if headers:
            full_headers.update(headers)
        
        if method.upper() == 'POST':
            response = requests.post(url, headers=full_headers, params=params, data=data, timeout=REQUEST_TIMEOUT)
        else:
            response = requests.get(url, headers=full_headers, params=params, timeout=REQUEST_TIMEOUT)
        
        response.raise_for_status() 
        try:
            response.encoding = response.apparent_encoding if response.apparent_encoding else 'utf-8'
            content = response.text
        except Exception as e:
            print(f"Encoding detection failed for {url}, trying utf-8. Error: {e}")
            content = response.content.decode('utf-8', errors='replace')
        return content
    except requests.exceptions.RequestException as e:
        print(f"Error during request to {url}: {e}")
        return None

# --- Chinese Literature Scrapers ---

def search_baidu_xueshu(query, max_results=5):
    search_url = f"https://xueshu.baidu.com/s?wd={quote_plus(query)}&pn=0&tn=SE_baiduxueshu_c1gjeupa&ie=utf-8&sc_f_para=sc_tasktype%3D%7BfirstSimpleSearch%7D&sc_hit=1"
    print(f"Searching Baidu Xueshu: {search_url}")
    
    html_content = make_request(search_url)
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    results = []
    
    # Try to find result containers with more specific class or structure
    result_containers = soup.find_all('div', class_='result sc_default_result xpath-log', limit=max_results)
    if not result_containers:
        result_containers = soup.find_all('div', class_='sc_content', limit=max_results)

    for item in result_containers:
        try:
            title_tag = item.find('h3', class_=re.compile(r't|title'))
            if not title_tag or not title_tag.find('a'):
                continue
            
            title = title_tag.find('a').text.strip()
            link = title_tag.find('a')['href']
            if not link.startswith('http'):
                link = urljoin("https://xueshu.baidu.com", link)

            # Abstract: Look for 'c-abstract', 'abstract_content', or 'abs'
            abstract_snippet_tag = item.find('div', class_=re.compile(r'c-abstract|abstract_content|abstract'))
            if not abstract_snippet_tag:
                 abstract_snippet_tag = item.find('p', class_=re.compile(r'c-abstract|abstract_content|abstract'))
            abstract_snippet = abstract_snippet_tag.text.strip().replace("摘要：","") if abstract_snippet_tag else "N/A"
            
            authors_str = "N/A"
            source_str = "N/A"
            year_str = "N/A"

            # Authors, source, year are often in 'sc_info' or 'c-subtext'
            info_div = item.find('div', class_=re.compile(r'sc_info|c-subtext'))
            if info_div:
                # Authors
                author_tags = info_div.find_all('a', {'data-click': re.compile(r'.*authoruri.*')})
                if not author_tags: # Fallback for authors if specific data-click not found
                    author_tags = info_div.find_all('a', href=re.compile(r'/s.*checktype=author'))
                
                authors_list = [a.text.strip() for a in author_tags if a.text.strip()]
                if authors_list:
                    authors_str = ", ".join(authors_list)
                else: # Fallback if authors are in spans without links
                    author_spans = info_div.find_all('span', class_=None) # Generic spans
                    temp_authors = []
                    for s in author_spans:
                        # Avoid year or journal name in author list
                        if not re.search(r'\d{4}', s.text) and not any(kw in s.text for kw in ['《', 'Journal', 'Conference']):
                            cleaned_author = s.text.replace("作者：","").strip()
                            if cleaned_author and len(cleaned_author) < 30: # Heuristic for author name length
                                temp_authors.append(cleaned_author)
                    if temp_authors:
                         authors_str = ", ".join(temp_authors)

                # Journal/Source and Year
                source_tag = info_div.find('a', {'data-click': re.compile(r'.*journaluri.*')})
                if source_tag:
                    source_str = source_tag.text.strip()
                else: # Fallback for source
                    source_span = info_div.find('span', class_=re.compile(r'sc_journal|journal_title'))
                    if source_span:
                        source_str = source_span.text.strip()
                    else: # Try to find journal in a span that looks like a journal title (e.g., in quotes)
                        journal_match = re.search(r'《([^》]+)》', info_div.text)
                        if journal_match:
                            source_str = journal_match.group(1)
                
                year_match = re.search(r'(\b\d{4}\b)(?![:\d])', info_div.text) # Match 4-digit year not followed by colon or digit (to avoid issue numbers)
                if year_match:
                    year_str = year_match.group(1)
                else: # Try to find year in a specific span if available
                    year_span = info_div.find('span', class_=re.compile(r'sc_year|year'))
                    if year_span:
                        year_match_in_span = re.search(r'\d{4}', year_span.text)
                        if year_match_in_span:
                            year_str = year_match_in_span.group(0)
            
            # Keywords are usually not on the search results page directly
            keywords_str = "N/A"

            results.append({
                "Title": title,
                "Title (中文翻译版)": title, 
                "Abstract": abstract_snippet,
                "Abstract (中文翻译版)": abstract_snippet, 
                "Publication Date": year_str, 
                "Authors": authors_str,
                "DOI": "N/A", 
                "Article Type": "N/A",
                "Journal": source_str,
                "Impact Factor": "N/A",
                "Keywords": keywords_str,
                "Full Text Link": link
            })
            time.sleep(REQUEST_DELAY / 2)
        except Exception as e:
            print(f"Error parsing Baidu Xueshu item: {e} for item {item.prettify()[:500]}")
            continue
    
    print(f"Baidu Xueshu: Found {len(results)} results for query '{query}'.")
    return results

# --- Policy Information Scrapers ---

def search_nmpa_news(query, max_results=5):
    base_url = "https://www.nmpa.gov.cn"
    # NMPA search seems to be dynamic. Let's try a different approach: search on their main search page.
    # The search URL structure for NMPA is often like: https://www.nmpa.gov.cn/search/search?channelid=xxxx&searchword=query
    # After inspecting NMPA, a general search URL is: https://www.nmpa.gov.cn/search/search?siteid=cmL2F0LzI=&q=QUERY_TERM
    # However, this page uses JavaScript to load results. A simple GET won't work well.
    # Let's try a news list page and filter, as previously attempted, but with better headers and error handling.
    # Targetting a news list page: e.g., '综合新闻' (Comprehensive News)
    news_list_url = "https://www.nmpa.gov.cn/xwzh/zhyw/index.html" # Changed to '综合新闻' which might be more general
    print(f"Fetching NMPA news list: {news_list_url} (will filter by query '{query}' client-side)")

    # Add a referer for NMPA
    nmpa_headers = COMMON_HEADERS.copy()
    nmpa_headers['Referer'] = base_url + "/"

    html_content = make_request(news_list_url, headers=nmpa_headers)
    if not html_content:
        print("Failed to fetch NMPA news list page.")
        return []
    
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []
    
    # Selector for NMPA news list items (needs verification by inspecting the actual page)
    # Common patterns: '.list ul li a', 'ul.rightlist_box li a'
    news_items_container = soup.find('ul', class_=re.compile(r'list_style_1|rightlist_box|list'))
    if not news_items_container:
        print("Could not find news items container on NMPA page.")
        # Try another common selector for news lists
        news_items_elements = soup.select("div.list_content_box ul li a") 
    else:
        news_items_elements = news_items_container.find_all('a', href=True)

    if not news_items_elements:
        print("No news item links found with the current selectors for NMPA.")
        return []

    count = 0
    for item_link_tag in news_items_elements:
        if count >= max_results:
            break
        
        title = item_link_tag.text.strip()
        if not title: # Skip empty titles
            title = item_link_tag.get('title', '').strip()
            if not title:
                continue

        link = item_link_tag.get('href')
        if not link:
            continue
        
        # Resolve relative URLs
        if link.startswith("./"):
            link = urljoin(news_list_url, link)
        elif not link.startswith('http'):
            link = urljoin(base_url, link)
        
        # Client-side filtering for the query in title
        if query.lower() in title.lower():
            date_str = "N/A"
            parent_li = item_link_tag.find_parent('li')
            if parent_li:
                date_tag = parent_li.find('span', class_=re.compile(r'date|time|fr')) # Common classes for date
                if date_tag:
                    date_str = date_tag.text.strip()
                else: 
                    date_match = re.search(r'(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})', parent_li.text)
                    if date_match:
                        date_str = date_match.group(1)
            
            results.append({
                "title": title,
                "link": link,
                "source": "NMPA",
                "publication_date": date_str,
                "summary": "N/A" # Fetching summary would require visiting each link
            })
            count += 1
            time.sleep(REQUEST_DELAY / 2)
            
    print(f"NMPA: Found {len(results)} potential items for query '{query}' by filtering news list.")
    return results

# --- Placeholder for other scrapers (FDA, WHO, etc.) ---
def search_fda_news(query, max_results=5):
    # FDA News & Events: https://www.fda.gov/news-events/fda-newsroom/press-announcements
    # Search URL: https://www.fda.gov/search?s=QUERY&sort_bef_combine=published_date_DESC
    base_url = "https://www.fda.gov"
    search_url = f"https://www.fda.gov/search?s={quote_plus(query)}&sort_bef_combine=published_date_DESC"
    print(f"Searching FDA News: {search_url}")
    html_content = make_request(search_url)
    if not html_content:
        return []
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []
    # Selector for FDA search results (needs verification)
    # Example: 'div.views-row article'
    articles = soup.select('div.views-row article.node--type-press-release', limit=max_results) # More specific
    if not articles:
        articles = soup.select('div.views-row', limit=max_results) # General row

    for article in articles:
        try:
            title_tag = article.find('h3')
            if not title_tag or not title_tag.find('a'):
                title_tag = article.find('h2') # Fallback
                if not title_tag or not title_tag.find('a'):
                    continue
            
            title = title_tag.find('a').text.strip()
            link = urljoin(base_url, title_tag.find('a')['href'])
            
            date_tag = article.find('div', class_='field--name-published-date')
            if not date_tag:
                date_tag = article.find('span', class_='date-display-single') # Fallback
            date_str = date_tag.text.strip() if date_tag else "N/A"
            
            summary_tag = article.find('div', class_=re.compile(r'field--name-body|field--name-field-summary'))
            summary = summary_tag.text.strip()[:250] + "..." if summary_tag else "N/A"

            results.append({
                "title": title,
                "link": link,
                "source": "FDA",
                "publication_date": date_str,
                "summary": summary
            })
            time.sleep(REQUEST_DELAY / 2)
        except Exception as e:
            print(f"Error parsing FDA item: {e}")
            continue
    print(f"FDA: Found {len(results)} results for query '{query}'.")
    return results

def search_who_news(query, max_results=5):
    # WHO News: https://www.who.int/news
    # Search: https://www.who.int/news-room/search?query=QUERY
    base_url = "https://www.who.int"
    search_url = f"https://www.who.int/news-room/search?query={quote_plus(query)}"
    print(f"Searching WHO News: {search_url}")
    html_content = make_request(search_url)
    if not html_content:
        return []
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []
    # Selector for WHO search results (needs verification)
    # Example: 'div.sf-search-results div.sf-result-item'
    items = soup.select('div.sf-search-results div.sf-result-item', limit=max_results)

    for item in items:
        try:
            title_tag = item.find('a', class_='sf-result-item-link')
            if not title_tag:
                continue
            title = title_tag.text.strip()
            link = urljoin(base_url, title_tag['href'])
            
            date_tag = item.find('div', class_='sf-result-item-type-n-date')
            date_str = "N/A"
            if date_tag:
                date_match = re.search(r'\d{1,2}\s+\w+\s+\d{4}', date_tag.text) # e.g., 10 May 2025
                if date_match:
                    date_str = date_match.group(0)
            
            summary_tag = item.find('div', class_='sf-result-item-summary')
            summary = summary_tag.text.strip()[:250] + "..." if summary_tag else "N/A"

            results.append({
                "title": title,
                "link": link,
                "source": "WHO",
                "publication_date": date_str,
                "summary": summary
            })
            time.sleep(REQUEST_DELAY / 2)
        except Exception as e:
            print(f"Error parsing WHO item: {e}")
            continue
    print(f"WHO: Found {len(results)} results for query '{query}'.")
    return results

# --- Main Test --- 
if __name__ == '__main__':
    print("--- Testing Chinese Literature Scraper (Baidu Xueshu) ---")
    query_cn = "肥胖与T2DM"
    baidu_results = search_baidu_xueshu(query_cn, max_results=3)
    if baidu_results:
        for res in baidu_results:
            print(f"  Title: {res['Title']}")
            print(f"  Link: {res['Full Text Link']}")
            print(f"  Authors: {res['Authors']}")
            print(f"  Journal: {res['Journal']}")
            print(f"  Year: {res['Publication Date']}")
            print(f"  Abstract Snippet: {res['Abstract'][:100]}...")
            print("---")
    else:
        print("No results from Baidu Xueshu or an error occurred.")
    
    time.sleep(REQUEST_DELAY)

    print("\n--- Testing Policy Information Scraper (NMPA News) ---")
    policy_query_nmpa = "医疗器械"
    nmpa_results = search_nmpa_news(policy_query_nmpa, max_results=3)
    if nmpa_results:
        for res in nmpa_results:
            print(f"  Title: {res['title']}")
            print(f"  Link: {res['link']}")
            print(f"  Source: {res['source']}")
            print(f"  Date: {res['publication_date']}")
            print("---")
    else:
        print("No results from NMPA or an error occurred.")

    time.sleep(REQUEST_DELAY)
    print("\n--- Testing Policy Information Scraper (FDA News) ---")
    policy_query_fda = "drug safety"
    fda_results = search_fda_news(policy_query_fda, max_results=2)
    if fda_results:
        for res in fda_results:
            print(f"  Title: {res['title']}")
            print(f"  Link: {res['link']}")
            print(f"  Source: {res['source']}")
            print(f"  Date: {res['publication_date']}")
            print(f"  Summary: {res['summary'][:100]}...")
            print("---")
    else:
        print("No results from FDA or an error occurred.")

    time.sleep(REQUEST_DELAY)
    print("\n--- Testing Policy Information Scraper (WHO News) ---")
    policy_query_who = "pandemic preparedness"
    who_results = search_who_news(policy_query_who, max_results=2)
    if who_results:
        for res in who_results:
            print(f"  Title: {res['title']}")
            print(f"  Link: {res['link']}")
            print(f"  Source: {res['source']}")
            print(f"  Date: {res['publication_date']}")
            print(f"  Summary: {res['summary'][:100]}...")
            print("---")
    else:
        print("No results from WHO or an error occurred.")


