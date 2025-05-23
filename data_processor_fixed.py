# data_processor.py - Module for translating text, processing, and standardizing data

import time
import pandas as pd
from googletrans import Translator
import re

# --- Configuration ---
TRANSLATION_DELAY = 3.5  # seconds between translation API calls to avoid rate limits
IMPACT_FACTOR_FILE_PATH = "J_Entrez1.xlsx"

# --- Translation Function ---
def translate_text(text, dest_lang=	"zh-cn"	, max_retries=3):
    """Translates a given text string to the destination language using Google Translate.
       Includes basic error handling and retries.
    """
    if not text or text == "N/A":
        return "N/A"
    
    translator = Translator(service_urls=['translate.google.com', 'translate.google.co.kr', 'translate.google.cn'])
    for attempt in range(max_retries):
        try:
            # Shorten long texts if they exceed Google Translate limits (e.g. 5000 chars for free tier)
            # This is a rough limit, actual might vary.
            # For abstracts, we might need to split and translate in chunks if they are very long.
            # For now, let's assume abstracts are within reasonable limits or truncate if extremely long.
            if len(text) > 4800:
                print(f"Warning: Text too long for translation ({len(text)} chars), truncating to 4800.")
                text_to_translate = text[:4800]
            else:
                text_to_translate = text

            translated = translator.translate(text_to_translate, dest=dest_lang)
            time.sleep(TRANSLATION_DELAY) # Respect API limits
            return translated.text
        except Exception as e:
            print(f"Error during translation (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(TRANSLATION_DELAY * (attempt + 2)) # Exponential backoff
            else:
                print(f"Failed to translate text after {max_retries} attempts: {text[:100]}...")
                return "Translation Error"
    return "Translation Error" # Should not be reached if loop completes

# --- Impact Factor Processing ---
def load_impact_factors(filepath=IMPACT_FACTOR_FILE_PATH):
    """Loads impact factors from the specified Excel file.
    Assumes the Excel file has columns like 	"Journal Name"	 and 	"Impact Factor 2024"	 (or similar).
    Returns a dictionary for easy lookup: {normalized_journal_name: impact_factor}
    """
    try:
        df = pd.read_excel(filepath, engine=	"openpyxl"	)
        impact_factors_data = {}
        # Try to find the correct columns. User mentioned "Impact Factor" (2024)
        # Let's be flexible with column names
        journal_col = None
        if_col = None
        for col in df.columns:
            col_lower = str(col).lower()
            if col_lower == "name" or ( "journal" in col_lower and ("name" in col_lower or "title" in col_lower)):
                journal_col = col
            if col_lower == "jif" or (("impact" in col_lower and "factor" in col_lower) or "if" == col_lower):
                if "2024" in col_lower or "jif" == col_lower or not if_col: # Prioritize 2024 or JIF if mentioned
                    if_col = col
        
        if not journal_col or not if_col:
            print(f"Error: Could not find Journal Name or Impact Factor columns in {filepath}. Columns found: {df.columns.tolist()}")
            return {}

        print(f"Using Journal Column: 	'{journal_col}'	 and Impact Factor Column: 	'{if_col}'	 from {filepath}")

        for index, row in df.iterrows():
            journal_name = str(row[journal_col]).strip()
            try:
                impact_factor = float(row[if_col])
                # Normalize journal name for matching (lowercase, remove punctuation and common terms)
                normalized_name = normalize_journal_name(journal_name)
                if normalized_name:
                    impact_factors_data[normalized_name] = impact_factor
            except (ValueError, TypeError):
                # print(f"Warning: Could not parse impact factor for {journal_name}: {row[if_col]}")
                continue
        print(f"Loaded {len(impact_factors_data)} journal impact factors.")
        return impact_factors_data
    except FileNotFoundError:
        print(f"Error: Impact factor file not found at {filepath}")
        return {}
    except Exception as e:
        print(f"Error loading impact factors from {filepath}: {e}")
        return {}

def normalize_journal_name(name):
    """Normalizes journal name for better matching."""
    if not isinstance(name, str):
        return ""
    name = name.lower()
    name = re.sub(r"[&\\\-.:,\t\"()\\[\\]]", " ", name)  # Replace punctuation with space
    name = re.sub(r"\s+", " ", name).strip()  # Remove multiple spaces   # Remove common terms like "the", "journal", "of", "and" - this might be too aggressive, use with caution
    # common_terms = ["the", "journal", "of", "and", "archives", "annals", "bulletin", "review", "clinical", "medical"]
    # words = name.split()
    # name = " ".join([word for word in words if word not in common_terms])
    return name

def get_impact_factor(journal_name, impact_factors_data):
    """Retrieves impact factor for a given journal name using normalized matching."""
    if not journal_name or journal_name == "N/A" or not impact_factors_data:
        return "N/A"
    
    norm_journal_name = normalize_journal_name(journal_name)
    if norm_journal_name in impact_factors_data:
        return impact_factors_data[norm_journal_name]
    
    # Try partial matching or abbreviation matching if direct match fails (can be complex)
    # For now, we rely on good normalization. Could be extended with fuzzy matching.
    # Example: check if any key in impact_factors_data is a substring of norm_journal_name or vice versa
    for key_norm, val_if in impact_factors_data.items():
        if key_norm in norm_journal_name or norm_journal_name in key_norm:
            # This is a very loose match, might lead to false positives.
            # A better approach would be to use Jaro-Winkler or Levenshtein distance for similarity.
            # print(f"Partial match for IF: 	"{journal_name}	" (normalized: {norm_journal_name}) with key {key_norm}")
            # return val_if # Disabled for now to avoid too many false positives
            pass 

    return "N/A"

# --- Data Processing and Standardization ---

def process_articles_common(articles, source_type="PubMed"):
    """Common processing for articles from any source.
       Adds placeholder for missing fields if any.
    """
    processed_articles = []
    expected_fields = [
        "PMID", "Title", "Title (中文翻译版)", "Abstract", "Abstract (中文翻译版)", 
        "Publication Date", "Authors", "DOI", "Article Type", "Journal", 
        "Impact Factor", "Keywords", "Full Text Link"
    ]
    for article in articles:
        processed_article = {}
        for field in expected_fields:
            processed_article[field] = article.get(field, "N/A")
        
        # Ensure specific fields are not empty if critical
        if not processed_article.get("Title") or processed_article.get("Title") == "N/A":
            if source_type == "PubMed" and processed_article.get("PMID"):                print(f"Warning: Article PMID {processed_article['PMID']} has no title. Skipping or marking.")            # continue # Optionally skip articles with no title

        processed_articles.append(processed_article)
    return processed_articles

def process_policy_info(policy_items):
    """Standardizes policy information items.
    Expected input: list of dicts with at least 	"title"	, 	"link"	, 	"source"	, 	"publication_date"	, 	"summary"	.
    Output: list of dicts with standardized fields.
    """
    standardized_items = []
    for item in policy_items:
        standardized_items.append({
            "Title": item.get("title", "N/A"),
            "Link": item.get("link", "N/A"),
            "Source": item.get("source", "N/A"),
            "Publication Date": item.get("publication_date", "N/A"),
            "Summary": item.get("summary", "N/A")
        })
    return standardized_items

# --- Main Test (Example Usage) ---
if __name__ == "__main__":
    print("--- Testing Translation ---")
    sample_text_en = "Obesity is a major risk factor for type 2 diabetes mellitus."
    translated_text_cn = translate_text(sample_text_en)
    print(f"Original: {sample_text_en}")
    print(f"Translated: {translated_text_cn}")

    sample_abstract_en = "BACKGROUND: The global epidemic of obesity has led to a parallel increase in type 2 diabetes (T2D). OBJECTIVE: This study aimed to investigate the molecular mechanisms linking obesity to insulin resistance and T2D. METHODS: A cohort of 500 participants (250 obese, 250 lean) was recruited. Adipose tissue biopsies and blood samples were collected. RESULTS: Obese individuals showed significantly higher levels of pro-inflammatory cytokines and markers of endoplasmic reticulum stress in adipose tissue. CONCLUSION: Chronic low-grade inflammation and ER stress in adipose tissue contribute to systemic insulin resistance in obesity, increasing T2D risk."
    translated_abstract_cn = translate_text(sample_abstract_en)
    print(f"\nOriginal Abstract (first 100 chars): {sample_abstract_en[:100]}...")
    print(f"Translated Abstract (first 100 chars): {translated_abstract_cn[:100]}...")

    print("\n--- Testing Impact Factor Loading ---")
    # Create a dummy impact factor file for testing if JSR_impact_factors.xlsx is not present or to ensure testability
    dummy_if_path = "/home/ubuntu/dummy_impact_factors.xlsx"
    try:
        # Check if user-provided file exists, otherwise use dummy for test
        with open(IMPACT_FACTOR_FILE_PATH, 	"r"	) as f:
            print(f"Using user-provided impact factor file: {IMPACT_FACTOR_FILE_PATH}")
            impact_factors = load_impact_factors(IMPACT_FACTOR_FILE_PATH)
    except FileNotFoundError:
        print(f"User impact factor file not found. Creating and using dummy file for testing: {dummy_if_path}")
        dummy_if_data = {
            	"Full Journal Name	": [	"The Lancet	", 	"New England Journal of Medicine	", 	"Nature Medicine	", 	"JAMA: Journal of the American Medical Association	", 	"Cell Metabolism	"],
            	"Abbreviation	": [	"Lancet	", 	"N Engl J Med	", 	"Nat Med	", 	"JAMA	", 	"Cell Metab	"],
            	"IF 2024	": [202.731, 176.079, 87.240, 157.335, 30.123]
        }
        dummy_df = pd.DataFrame(dummy_if_data)
        dummy_df.to_excel(dummy_if_path, index=False, engine=	"openpyxl"	)
        impact_factors = load_impact_factors(dummy_if_path)

    if impact_factors:
        print(f"Loaded {len(impact_factors)} impact factors.")
        print(f"Impact factor for 'The Lancet': {get_impact_factor('The Lancet', impact_factors)}")
        print(f"Impact factor for 'N Engl J Med': {get_impact_factor('N Engl J Med', impact_factors)}")
        print(f"Impact factor for 'nature medicine': {get_impact_factor('nature medicine', impact_factors)}")
        print(f"Impact factor for 'Journal of Clinical Oncology': {get_impact_factor('Journal of Clinical Oncology', impact_factors)} (Expected N/A if not in dummy)")
    else:
        print("Failed to load impact factors.")
    print("\n--- Testing Article Processing (Example) ---")
    sample_pubmed_articles = [
        {
            "PMID": "12345", "Title": "A study on T2DM", "Abstract": "This is an abstract.", 
            "Journal": "The Lancet", "Authors": "Doe J, Smith A", "Publication Date": "2023-01-01",
            "DOI": "10.1016/S0140-6736(23)00001-1", "Article Type": "Research Article", "Keywords": "T2DM, study",
            "Full Text Link": "http://example.com/12345"
        },
        {
            "PMID": "67890", "Title": "Obesity and its complications", "Abstract": "Another abstract here.", 
            "Journal": "Nature Medicine", "Authors": "Chan L", "Publication Date": "2023-02-15",
            "DOI": "10.1038/s41591-023-00002-2", "Article Type": "Review", "Keywords": "Obesity, complications",
            "Full Text Link": "http://example.com/67890"
        }
    ]

    # Simulate processing PubMed articles
    print("Processing PubMed articles...")
    final_pubmed_articles = []
    for article_data in sample_pubmed_articles:
        article_data["Title (中文翻译版)"] = translate_text(article_data["Title"])
        article_data["Abstract (中文翻译版)"] = translate_text(article_data["Abstract"])
        article_data["Impact Factor"] = get_impact_factor(article_data["Journal"], impact_factors)
        final_pubmed_articles.append(article_data)
    
    standardized_pubmed = process_articles_common(final_pubmed_articles, source_type="PubMed")
    for i, article in enumerate(standardized_pubmed):
        print(f"\nProcessed PubMed Article {i+1}:")
        for key, value in article.items():
            print(f"  {key}: {value}")

    print("\n--- Testing Policy Info Processing ---")
    sample_policy_items = [
        {"title": "New Drug Approved", "link": "http://nmpa.example/news/1", "source": "NMPA", "publication_date": "2024-01-10", "summary": "A new drug for X has been approved."},
        {"title": "Guideline Update", "link": "http://fda.example/guideline/2", "source": "FDA", "publication_date": "2024-02-20", "summary": "Updated guidelines for Y released."}
    ]
    processed_policies = process_policy_info(sample_policy_items)
    for i, policy in enumerate(processed_policies):
        print(f"\nProcessed Policy Item {i+1}:")
        for key, value in policy.items():
            print(f"  {key}: {value}")
from googletrans import Translator
import time
import json
import os
from tqdm import tqdm

# 配置参数
TRANSLATION_DELAY = 1.0  # 每次请求延迟（秒）
MAX_RETRIES = 5  # 最大重试次数
TIMEOUT = 10  # 请求超时时间（秒）
CACHE_FILE = "translation_cache.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load cache: {e}")
    return {}

def save_cache(cache):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Failed to save cache: {e}")

def translate_text(text, dest_lang="zh-cn", max_retries=MAX_RETRIES):
    if not text or text.strip() == "":
        return ""
    
    cache = load_cache()
    text_hash = str(hash(text))
    
    # 检查缓存
    if text_hash in cache:
        print(f"Using cached translation for text (hash: {text_hash[:8]}...)")
        return cache[text_hash]
    
    translator = Translator(service_urls=['translate.google.cn'], timeout=TIMEOUT)
    chunk_size = 4800
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    translated_chunks = []

    try:
        # 使用 tqdm 显示进度条
        for i, chunk in enumerate(tqdm(chunks, desc="Translating", unit="chunk")):
            if not chunk.strip():
                translated_chunks.append("")
                continue
                
            for attempt in range(max_retries):
                try:
                    print(f"Translating chunk {i+1}/{len(chunks)} (attempt {attempt+1}/{max_retries})...")
                    translated = translator.translate(chunk, dest=dest_lang)
                    time.sleep(TRANSLATION_DELAY)  # 控制请求频率
                    translated_chunks.append(translated.text)
                    
                    # 更新缓存
                    cache[text_hash] = ''.join(translated_chunks)
                    if i % 5 == 0:  # 每5个块保存一次缓存
                        save_cache(cache)
                    break
                except Exception as e:
                    print(f"Error during translation (chunk {i+1}/{len(chunks)}, attempt {attempt+1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        wait_time = TRANSLATION_DELAY * (attempt + 2)
                        print(f"Retrying in {wait_time:.1f} seconds...")
                        time.sleep(wait_time)
                    else:
                        print(f"Failed to translate chunk {i+1}/{len(chunks)} after {max_retries} attempts.")
                        return "Translation Error"
    except KeyboardInterrupt:
        print("\nTranslation interrupted by user. Saving progress...")
        if translated_chunks:
            cache[text_hash] = ''.join(translated_chunks)
            save_cache(cache)
            print(f"Progress saved. Resuming later will start from {len(translated_chunks)}/{len(chunks)} chunks.")
        raise  # 重新抛出异常，让调用者处理

    # 最终保存完整结果
    cache[text_hash] = ''.join(translated_chunks)
    save_cache(cache)
    return ''.join(translated_chunks)




import time
import json
import os
from googletrans import Translator
from tqdm import tqdm

TRANSLATION_DELAY = 1.0
MAX_RETRIES = 5
CACHE_FILE = "translation_cache.json"
CHUNK_SIZE = 4800

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(cache):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except:
        pass

def translate_text(text, dest_lang="zh-cn", max_retries=MAX_RETRIES):
    if not text or text.strip() == "":
        return ""

    cache = load_cache()
    text_hash = str(hash(text))
    if text_hash in cache:
        return cache[text_hash]

    translator = Translator(service_urls=['translate.google.com', 'translate.google.cn', 'translate.google.co.kr'])
    chunks = [text[i:i+CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
    translated_chunks = []

    for idx, chunk in enumerate(tqdm(chunks, desc="Translating", unit="chunk")):
        for attempt in range(max_retries):
            try:
                result = translator.translate(chunk, dest=dest_lang)
                translated_chunks.append(result.text)
                time.sleep(TRANSLATION_DELAY)
                break
            except Exception as e:
                print(f"[翻译失败] 第 {attempt+1}/{max_retries} 次尝试，错误：{e}")
                time.sleep(TRANSLATION_DELAY * (attempt + 2))
        else:
            print(f"[失败] 第 {idx+1} 段翻译失败，跳过")
            translated_chunks.append("")

    full_translation = "".join(translated_chunks)
    cache[text_hash] = full_translation
    save_cache(cache)
    return full_translation
