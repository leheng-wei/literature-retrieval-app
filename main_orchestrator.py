import datetime
import pandas as pd
import os

# Import modules from the project
from pubmed_retriever import search_pubmed
from data_processor_fixed import (
    translate_text, 
    load_impact_factors, 
    get_impact_factor, 
    process_articles_common,
    IMPACT_FACTOR_FILE_PATH
)

# --- Configuration ---
USER_EMAIL = "mingdan1021@gmail.com"
USER_API_KEY = "fde2962074b8ec291444140a1325fe9d0707"
OUTPUT_DIR = "output"

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

def run_retrieval_workflow(query_en, time_period_str, max_pubmed_results=20):
    """Runs the PubMed retrieval and processing workflow."""
    print(f"Starting retrieval workflow for query: '{query_en}', Time Period: '{time_period_str}'")

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
            print(f"Processing PubMed article {i+1}/{len(pubmed_articles_raw)}: PMID {article.get('PMID')}")
            article["Title (中文翻译版)"] = translate_text(article.get("Title"))
            article["Abstract (中文翻译版)"] = translate_text(article.get("Abstract"))
            article["Impact Factor"] = get_impact_factor(article.get("Journal"), impact_factors_data)
            processed_pubmed_articles.append(article)
        standardized_pubmed_data = process_articles_common(processed_pubmed_article)
        pubmed_df = pd.DataFrame(standardized_pubmed_data)
        pubmed_file = save_to_excel(pubmed_df, "pubmed_literature_results.xlsx", sheet_name="PubMed Results")
    else:
        print("No articles retrieved from PubMed or an error occurred.")
        standardized_pubmed_data = process_articles_common([])
        pubmed_df = pd.DataFrame(standardized_pubmed_data)
        pubmed_file = save_to_excel(pubmed_df, "pubmed_literature_results.xlsx", sheet_name="PubMed Results")

    print("\n--- Workflow Completed ---")
    print(f"Output file should be available in: {OUTPUT_DIR}")
    return pubmed_file
