# PubMed Retriever v3: Focused on robust parsing of Authors, ArticleType, Keywords
import datetime
import time
from Bio import Entrez

# --- Helper Functions ---

def get_date_range(time_period_str):
    today = datetime.date.today()
    maxdate = today.strftime("%Y/%m/%d")
    mindate = None
    try:
        if time_period_str == "近一年":
            mindate = (today - datetime.timedelta(days=365)).strftime("%Y/%m/%d")
        elif time_period_str == "近六个月":
            mindate = (today - datetime.timedelta(days=180)).strftime("%Y/%m/%d")
        elif time_period_str == "近三个月":
            mindate = (today - datetime.timedelta(days=90)).strftime("%Y/%m/%d")
        elif time_period_str == "近一个月" or time_period_str == "近30天":
            mindate = (today - datetime.timedelta(days=30)).strftime("%Y/%m/%d")
        elif time_period_str == "近一周" or time_period_str == "近7天":
            mindate = (today - datetime.timedelta(days=7)).strftime("%Y/%m/%d")
        # Add more specific date ranges if needed
    except Exception as e:
        print(f"Error parsing date range 	'{time_period_str}	': {e}")
    return mindate, maxdate

def safe_get_text(element, key=None):
    """Safely get text from a Biopython Entrez parsed element."""
    if key:
        item = element.get(key)
    else:
        item = element
    
    if item is None:
        return ""
    if isinstance(item, str):
        return item
    if hasattr(item, 'decode'): # Handle bytes if any
        try:
            return item.decode(	'utf-8	')
        except:
            return str(item) # Fallback
    return str(item).strip() # General fallback, strip whitespace

def parse_author_list(author_list_node):
    authors = []
    if not author_list_node or 'Author' not in author_list_node:
        return "N/A"

    author_elements = author_list_node['Author']
    if not isinstance(author_elements, list):
        author_elements = [author_elements]

    for author_node in author_elements:
        if not isinstance(author_node, dict): # Or DictionaryElement
            continue
        collective_name = safe_get_text(author_node, 'CollectiveName')
        if collective_name:
            authors.append(collective_name)
            continue
        
        last_name = safe_get_text(author_node, 'LastName')
        fore_name = safe_get_text(author_node, 'ForeName')
        initials = safe_get_text(author_node, 'Initials')
        
        full_name = ""
        if fore_name and last_name:
            full_name = f"{fore_name} {last_name}"
        elif last_name and initials:
            full_name = f"{last_name} {initials}"
        elif last_name:
            full_name = last_name
        elif fore_name:
            full_name = fore_name
        elif initials:
            full_name = initials
        
        if full_name:
            authors.append(full_name)
            
    return ", ".join(authors) if authors else "N/A"

def parse_publication_date(pub_date_node):
    if not pub_date_node or not isinstance(pub_date_node, dict):
        return "N/A"
    
    year = safe_get_text(pub_date_node, "Year")
    month_val = safe_get_text(pub_date_node, "Month")
    day = safe_get_text(pub_date_node, "Day")
    medline_date = safe_get_text(pub_date_node, "MedlineDate")

    month_map = {
        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
        "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
    }
    month = ""
    if month_val:
        if month_val.isdigit() and len(month_val) <=2:
            month = month_val.zfill(2)
        elif month_val in month_map:
            month = month_map[month_val]
        else: 
            month = month_val # Keep original if not recognized, e.g. 'Spring'

    if year and month and day:
        return f"{year}-{month}-{day.zfill(2) if day.isdigit() else day}"
    elif year and month:
        return f"{year}-{month}"
    elif year:
        return f"{year}"
    elif medline_date:
        return medline_date
    return "N/A"

def get_abstract_text(abstract_node):
    if not abstract_node or 'AbstractText' not in abstract_node:
        return "N/A"

    abstract_text_elements = abstract_node['AbstractText']
    parts = []

    if not isinstance(abstract_text_elements, list):
        abstract_text_elements = [abstract_text_elements]

    for item in abstract_text_elements:
        text_content = safe_get_text(item)
        label = ""
        if hasattr(item, 'attributes') and isinstance(item.attributes, dict):
            label = item.attributes.get('Label', '')
        
        if label:
            parts.append(f"{label}: {text_content}")
        elif text_content:
            parts.append(text_content)
            
    return "\n".join(parts) if parts else "N/A"

def get_doi(article_node, pubmed_data_node):
    if article_node and isinstance(article_node, dict):
        elocation_ids = article_node.get('ELocationID', [])
        if not isinstance(elocation_ids, list):
            elocation_ids = [elocation_ids]
        for eid in elocation_ids:
            if hasattr(eid, 'attributes') and isinstance(eid.attributes, dict) and \
               eid.attributes.get("EIdType") == "doi" and eid.attributes.get("ValidYN") == "Y":
                return safe_get_text(eid)

    if pubmed_data_node and isinstance(pubmed_data_node, dict) and 'ArticleIdList' in pubmed_data_node:
        article_id_list = pubmed_data_node['ArticleIdList']
        if article_id_list and isinstance(article_id_list, dict):
            article_ids = article_id_list.get('ArticleId', [])
            if not isinstance(article_ids, list):
                article_ids = [article_ids]
            for aid_node in article_ids:
                if hasattr(aid_node, 'attributes') and isinstance(aid_node.attributes, dict) and \
                   aid_node.attributes.get("IdType") == "doi":
                    return safe_get_text(aid_node)
    return "N/A"

def get_full_text_link(doi, pmid, pubmed_data_node):
    if doi and doi != "N/A":
        return f"https://doi.org/{doi}"
    
    pmc_id = None
    if pubmed_data_node and isinstance(pubmed_data_node, dict) and 'ArticleIdList' in pubmed_data_node:
        article_id_list = pubmed_data_node['ArticleIdList']
        if article_id_list and isinstance(article_id_list, dict):
            article_ids = article_id_list.get('ArticleId', [])
            if not isinstance(article_ids, list):
                article_ids = [article_ids]
            for aid_node in article_ids:
                if hasattr(aid_node, 'attributes') and isinstance(aid_node.attributes, dict) and \
                   aid_node.attributes.get("IdType") == "pmc":
                    pmc_id_val = safe_get_text(aid_node)
                    if pmc_id_val:
                        pmc_id = pmc_id_val if pmc_id_val.upper().startswith("PMC") else "PMC" + pmc_id_val
                        break
    if pmc_id:
        return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/"
    return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

def get_keywords(medline_citation_node):
    keywords_set = set()
    # MeSH Headings
    if medline_citation_node and isinstance(medline_citation_node, dict):
        mesh_heading_list_node = medline_citation_node.get('MeshHeadingList')
        if mesh_heading_list_node and isinstance(mesh_heading_list_node, dict) and 'MeshHeading' in mesh_heading_list_node:
            mesh_headings = mesh_heading_list_node['MeshHeading']
            if not isinstance(mesh_headings, list):
                mesh_headings = [mesh_headings]
            for mh_node in mesh_headings:
                if not isinstance(mh_node, dict): continue
                desc_name_node = mh_node.get('DescriptorName')
                if desc_name_node:
                    desc_name = safe_get_text(desc_name_node)
                    is_major_desc = hasattr(desc_name_node, 'attributes') and desc_name_node.attributes.get('MajorTopicYN') == 'Y'
                    keywords_set.add(("*" if is_major_desc else "") + desc_name)
                    
                    qualifier_name_nodes = mh_node.get('QualifierName', [])
                    if not isinstance(qualifier_name_nodes, list):
                        qualifier_name_nodes = [qualifier_name_nodes]
                    for qual_node in qualifier_name_nodes:
                        if qual_node:
                            qual_name = safe_get_text(qual_node)
                            is_major_qual = hasattr(qual_node, 'attributes') and qual_node.attributes.get('MajorTopicYN') == 'Y'
                            full_qual_keyword = f"{desc_name}/{qual_name}"
                            keywords_set.add(("*" if is_major_qual else "") + full_qual_keyword)
        # Author Keywords (from KeywordList)
        article_node = medline_citation_node.get('Article')
        if article_node and isinstance(article_node, dict) and 'KeywordList' in article_node:
            keyword_lists = article_node.get('KeywordList', [])
            if not isinstance(keyword_lists, list):
                keyword_lists = [keyword_lists]
            for kw_list_node in keyword_lists:
                if kw_list_node and isinstance(kw_list_node, dict) and 'Keyword' in kw_list_node:
                    author_keywords = kw_list_node['Keyword']
                    if not isinstance(author_keywords, list):
                        author_keywords = [author_keywords]
                    for kw_node in author_keywords:
                        if kw_node:
                            kw_text = safe_get_text(kw_node)
                            is_major_kw = hasattr(kw_node, 'attributes') and kw_node.attributes.get('MajorTopicYN') == 'Y'
                            keywords_set.add(("*" if is_major_kw else "") + kw_text)
    return ", ".join(sorted(list(keywords_set))) if keywords_set else "N/A"

def get_article_types(article_node):
    article_type_parts = []
    if article_node and isinstance(article_node, dict):
        pub_type_list_node = article_node.get('PublicationTypeList')
        if pub_type_list_node and isinstance(pub_type_list_node, dict) and 'PublicationType' in pub_type_list_node:
            pub_types = pub_type_list_node['PublicationType']
            if not isinstance(pub_types, list):
                pub_types = [pub_types]
            for pt_node in pub_types:
                pt_text = safe_get_text(pt_node)
                if pt_text:
                    article_type_parts.append(pt_text)
    return ", ".join(article_type_parts) if article_type_parts else "N/A"

# --- Main PubMed Search Function ---
def search_pubmed(query, time_period_str, email, api_key, max_results=20):
    Entrez.email = email
    Entrez.api_key = api_key
    mindate, maxdate = get_date_range(time_period_str)
    search_term = query
    if mindate and maxdate:
        search_term += f" AND ((\"{mindate}\"[Date - Publication] : \"{maxdate}\"[Date - Publication]))"
    print(f"Searching PubMed with term: {search_term}")
    try:
        handle = Entrez.esearch(db="pubmed", term=search_term, retmax=str(max_results), sort="relevance")
        record = Entrez.read(handle)
        handle.close()
        pmids = record["IdList"]
    except Exception as e:
        print(f"Error during PubMed esearch: {e}")
        return []
    if not pmids:
        print("No articles found.")
        return []
    print(f"Found {len(pmids)} PMIDs. Fetching details...")
    try:
        handle = Entrez.efetch(db="pubmed", id=pmids, rettype="xml", retmode="xml")
        parsed_xml_set = Entrez.read(handle)
        handle.close()
    except Exception as e:
        print(f"Error during PubMed efetch: {e}")
        return []

    articles_to_process = []
    if isinstance(parsed_xml_set, dict) and 'PubmedArticle' in parsed_xml_set:
        raw_articles = parsed_xml_set['PubmedArticle']
        if isinstance(raw_articles, list):
            articles_to_process.extend(raw_articles)
        elif isinstance(raw_articles, dict): # Single article
            articles_to_process.append(raw_articles)
    # Add PubmedBookArticle handling here if needed later

    results = []    
    for article_entry in articles_to_process:
        if not isinstance(article_entry, dict):
            continue
        medline_citation = article_entry.get('MedlineCitation')
        pubmed_data = article_entry.get('PubmedData')
        if not medline_citation or not isinstance(medline_citation, dict):
            pmid_unknown = safe_get_text(article_entry.get('PMID', 'Unknown'))
            print(f"Skipping entry without valid MedlineCitation (PMID: {pmid_unknown}).")
            continue

        pmid = safe_get_text(medline_citation, 'PMID')
        article_node = medline_citation.get('Article')
        if not article_node or not isinstance(article_node, dict):
            print(f"Skipping article {pmid} due to missing or invalid Article node.")
            continue
        
        title = safe_get_text(article_node, 'ArticleTitle')
        abstract_data = article_node.get('Abstract')
        abstract = get_abstract_text(abstract_data)
        
        pub_date_data = None
        journal_node = article_node.get('Journal')
        if journal_node and isinstance(journal_node, dict):
            journal_issue_node = journal_node.get('JournalIssue')
            if journal_issue_node and isinstance(journal_issue_node, dict):
                pub_date_data = journal_issue_node.get('PubDate')
        pub_date = parse_publication_date(pub_date_data)
        
        author_list_data = article_node.get('AuthorList')
        authors = parse_author_list(author_list_data)
        
        journal_title = "N/A"
        if journal_node and isinstance(journal_node, dict):
            title_text = safe_get_text(journal_node, 'Title')
            iso_abbr_text = safe_get_text(journal_node, 'ISOAbbreviation')
            journal_title = title_text if title_text else iso_abbr_text if iso_abbr_text else "N/A"
        
        article_type = get_article_types(article_node)
        doi = get_doi(article_node, pubmed_data)
        full_text_link = get_full_text_link(doi, pmid, pubmed_data)
        keywords = get_keywords(medline_citation)

        results.append({
            "PMID": pmid if pmid else "N/A",
            "Title": title if title else "N/A",
            "Abstract": abstract,
            "Publication Date": pub_date,
            "Authors": authors,
            "DOI": doi,
            "Article Type": article_type,
            "Journal": journal_title,
            "Keywords": keywords,
            "Full Text Link": full_text_link
        })
        time.sleep(0.11) 

    print(f"Successfully fetched details for {len(results)} articles.")
    return results

if __name__ == '__main__':
    USER_EMAIL = "mingdan1021@gmail.com" 
    USER_API_KEY = "fde2962074b8ec291444140a1325fe9d0707"
    query_term = "obesity AND type 2 diabetes mellitus"
    time_frame = "近一年"
    print(f"Running PubMed search for: 	'{query_term}	' within 	'{time_frame}	'")
    articles = search_pubmed(query_term, time_frame, USER_EMAIL, USER_API_KEY, max_results=5)
    if articles:
        print("\n--- Search Results ---")
        for i, article in enumerate(articles):
            print(f"\nArticle {i+1}:")
            for key, value in article.items():
                # Truncate abstract for display
                if key == "Abstract" and isinstance(value, str) and len(value) > 200:
                    print(f"  {key}: {value[:200]}...")
                elif key == "Keywords" and isinstance(value, str) and len(value) > 200:
                    print(f"  {key}: {value[:200]}...")
                else:
                    print(f"  {key}: {value}")
    else:
        print("No articles retrieved or an error occurred.")


