# main_orchestrator.py - Main script to orchestrate literature and policy retrieval

import datetime
import pandas as pd
import os

# Import modules from the project
from pubmed_retriever import search_pubmed
from web_scraper import search_baidu_xueshu, search_nmpa_news, search_fda_news, search_who_news
from data_processor_fixed import (
    translate_text, 
    load_impact_factors, 
    get_impact_factor, 
    process_articles_common,
    process_policy_info,
    IMPACT_FACTOR_FILE_PATH
)

# --- Configuration ---
# User-specific (can be moved to a config file or CLI args later)
USER_EMAIL = "mingdan1021@gmail.com"  # Provided by user
USER_API_KEY = "fde2962074b8ec291444140a1325fe9d0707"  # Provided by user

OUTPUT_DIR = "D:/ASUS/3849801631/FileRecv/科研小助手/医学文献及政策信息检索代码实现/output"

# --- Helper function to write to Excel ---
def save_to_excel(dataframe, filename, sheet_name="Results"):
    """Saves a pandas DataFrame to an Excel file."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    filepath = os.path.join(OUTPUT_DIR, filename)
    try:
        dataframe.to_excel(filepath, index=False, sheet_name=sheet_name, engine="openpyxl")
        print(f"Successfully saved data to {filepath}")
        return filepath
    except Exception as e:
        print(f"Error saving data to Excel file {filepath}: {e}")
        return None

# --- Helper function to write policy summary to text file ---
def save_policy_summary_to_txt(policy_data, filename):
    """Saves policy information summary to a text file."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    filepath = os.path.join(OUTPUT_DIR, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            if not policy_data:
                f.write("No policy information found or an error occurred during retrieval.\n")
            else:
                f.write("医学领域政策信息总结\n")
                f.write("=========================\n\n")
                for item in policy_data:
                    f.write(f"标题: {item.get('Title', 'N/A')}\n")
                    f.write(f"来源: {item.get('Source', 'N/A')}\n")
                    f.write(f"发布日期: {item.get('Publication Date', 'N/A')}\n")
                    f.write(f"链接: {item.get('Link', 'N/A')}\n")
                    summary = item.get("Summary", "N/A")
                    if summary != "N/A" and summary:
                        f.write(f"摘要: {summary}\n")
                    f.write("-------------------------\n")
        print(f"Successfully saved policy summary to {filepath}")
        return filepath
    except Exception as e:
        print(f"Error saving policy summary to text file {filepath}: {e}")
        return None 

# --- Main Workflow ---
def run_retrieval_workflow(query_en, query_cn, time_period_str, max_pubmed_results=20, max_baidu_results=5, max_policy_results=5):
    """Runs the complete retrieval and processing workflow."""
    print(f"Starting retrieval workflow for queries: EN=	'{query_en}'	, CN=	'{query_cn}'	, Time Period: 	'{time_period_str}'	")

    # 1. Load Impact Factors
    print("\n--- Loading Impact Factors ---")
    impact_factors_data = load_impact_factors(IMPACT_FACTOR_FILE_PATH)
    if not impact_factors_data:
        print("Warning: Could not load impact factors. Impact Factor column will be N/A.")

    # 2. PubMed English Literature Retrieval and Processing
    print("\n--- Retrieving English Literature from PubMed ---")
    pubmed_articles_raw = search_pubmed(query_en, time_period_str, USER_EMAIL, USER_API_KEY, max_results=max_pubmed_results)
    
    processed_pubmed_articles = []
    if pubmed_articles_raw:
        print(f"Translating {len(pubmed_articles_raw)} PubMed articles...")
        for i, article in enumerate(pubmed_articles_raw):
            print(f"Processing PubMed article {i+1}/{len(pubmed_articles_raw)}: PMID {article.get(	'PMID'	)}")
            article["Title (中文翻译版)"] = translate_text(article.get("Title"))
            article["Abstract (中文翻译版)"] = translate_text(article.get("Abstract"))
            article["Impact Factor"] = get_impact_factor(article.get("Journal"), impact_factors_data)
            processed_pubmed_articles.append(article)
        standardized_pubmed_data = process_articles_common(processed_pubmed_articles, source_type="PubMed")
        pubmed_df = pd.DataFrame(standardized_pubmed_data)
        save_to_excel(pubmed_df, "pubmed_literature_results.xlsx", sheet_name="PubMed Results")
    else:
        print("No articles retrieved from PubMed or an error occurred.")
        # Create empty DataFrame to still generate the file if needed
        standardized_pubmed_data = process_articles_common([], source_type="PubMed")
        pubmed_df = pd.DataFrame(standardized_pubmed_data)
        save_to_excel(pubmed_df, "pubmed_literature_results.xlsx", sheet_name="PubMed Results")

    # 3. Chinese Literature Retrieval (Baidu Xueshu)
    print("\n--- Retrieving Chinese Literature from Baidu Xueshu ---")
    baidu_articles_raw = search_baidu_xueshu(query_cn, max_results=max_baidu_results)
    if baidu_articles_raw:
        # For Baidu results, Title and Abstract are already Chinese.
        # We just need to ensure the columns match the final Excel structure.
        # Impact factor and keywords are typically N/A from Baidu search results directly.
        for article in baidu_articles_raw:
            article["Title (中文翻译版)"] = article.get("Title") # Already Chinese
            article["Abstract (中文翻译版)"] = article.get("Abstract") # Already Chinese
            article["Impact Factor"] = get_impact_factor(article.get("Journal"), impact_factors_data)
            # Other fields like PMID, DOI, Article Type are often N/A from Baidu
        standardized_baidu_data = process_articles_common(baidu_articles_raw, source_type="BaiduXueshu")
        baidu_df = pd.DataFrame(standardized_baidu_data)
        save_to_excel(baidu_df, "chinese_literature_results.xlsx", sheet_name="Chinese Literature Results")
    else:
        print("No articles retrieved from Baidu Xueshu or an error occurred.")
        standardized_baidu_data = process_articles_common([], source_type="BaiduXueshu")
        baidu_df = pd.DataFrame(standardized_baidu_data)
        save_to_excel(baidu_df, "chinese_literature_results.xlsx", sheet_name="Chinese Literature Results")

    # 4. Policy Information Retrieval
    print("\n--- Retrieving Policy Information ---")
    all_policy_items = []
    # NMPA (query_cn is likely more relevant for NMPA)
    print("Searching NMPA...")
    nmpa_policy = search_nmpa_news(query_cn, max_results=max_policy_results)
    if nmpa_policy: all_policy_items.extend(nmpa_policy)
    
    # FDA (query_en is more relevant)
    print("Searching FDA...")
    fda_policy = search_fda_news(query_en, max_results=max_policy_results)
    if fda_policy: all_policy_items.extend(fda_policy)

    # WHO (query_en is more relevant)
    print("Searching WHO...")
    who_policy = search_who_news(query_en, max_results=max_policy_results)
    if who_policy: all_policy_items.extend(who_policy)
    
    # IDF, CDS - Not implemented in web_scraper.py yet, can be added later
    # print("Searching IDF (Placeholder)...")
    # print("Searching CDS (Placeholder)...")

    standardized_policy_data = process_policy_info(all_policy_items)
    save_policy_summary_to_txt(standardized_policy_data, "policy_information_summary.txt")

    print("\n--- Workflow Completed ---")
    print(f"Output files should be available in: {OUTPUT_DIR}")
    return os.path.join(OUTPUT_DIR, "pubmed_literature_results.xlsx"), \
           os.path.join(OUTPUT_DIR, "chinese_literature_results.xlsx"), \
           os.path.join(OUTPUT_DIR, "policy_information_summary.txt")

# if __name__ == "__main__":
#     # Example usage based on user's request
#     # User query: "肥胖与T2DM", time: "近一年"
#     # For PubMed, we need an English equivalent for the query.
#     # Let's assume a simple translation or a predefined English version for the example.
#     english_query = "obesity AND type 2 diabetes mellitus" # Or "obesity AND T2DM"
#     chinese_query = "肥胖与T2DM"
#     search_time_period = "近一年" # User can change this

#     # Define maximum results for each source (can be adjusted)
#     max_pubmed = 10 # Reduced for faster testing, user might want more
#     max_baidu = 5
#     max_policy = 3

#     print(f"Script started at {datetime.datetime.now().strftime(	'%Y-%m-%d %H:%M:%S'	)}")
#     run_retrieval_workflow(
#         english_query, 
#         chinese_query, 
#         search_time_period,
#         max_pubmed_results=max_pubmed,
#         max_baidu_results=max_baidu,
#         max_policy_results=max_policy
#     )
#     print(f"Script finished at {datetime.datetime.now().strftime(	'%Y-%m-%d %H:%M:%S'	)}")

