import streamlit as st
from main_orchestrator import run_retrieval_workflow
import pandas as pd
import os

st.set_page_config(page_title="医学文献与政策信息检索", layout="wide")
st.title("📚 医学文献与政策信息检索工具")

# 初始化 session 状态
if 'result_paths' not in st.session_state:
    st.session_state.result_paths = None

# ---- 用户输入区域 ----
query_en = st.text_input("🔍 输入英文关键词（PubMed）", value="obesity AND type 2 diabetes mellitus")
query_cn = st.text_input("🔍 输入中文关键词（百度学术 & 政策）", value="肥胖与T2DM")
time_range = st.selectbox("🕒 选择时间范围", ["近一年", "近六个月", "近三个月", "近一个月", "近一周"])

max_pubmed = st.slider("📈 PubMed 文献数量", min_value=10, max_value=500, step=10, value=50)
max_baidu = st.slider("📘 百度学术 文献数量", min_value=1, max_value=50, step=1, value=5)
translate_option = st.checkbox("🌐 翻译标题和摘要为中文", value=True)

if st.button("🚀 开始检索"):
    with st.spinner("正在检索中，请稍候..."):
        result_paths = run_retrieval_workflow(
            query_en,
            query_cn,
            time_range,
            max_pubmed_results=max_pubmed,
            max_baidu_results=max_baidu,
            max_policy_results=3,
            translate=translate_option
        )
        st.session_state.result_paths = result_paths

# ---- 检索结果展示 ----
if st.session_state.result_paths:
    pubmed_file, baidu_file, policy_file = st.session_state.result_paths

    st.success("🎉 检索完成，以下是 PubMed 结果预览：")

    if os.path.exists(pubmed_file):
        df = pd.read_excel(pubmed_file, engine="openpyxl")

        page_size = 5
        total_rows = df.shape[0]
        total_pages = (total_rows + page_size - 1) // page_size

        page = st.number_input("分页浏览（页码）", min_value=1, max_value=total_pages, value=1)
        start = (page - 1) * page_size
        end = start + page_size

        display_cols = ["PMID", "Title", "Abstract", "Journal", "Authors", "Publication Date", "Full Text Link"]
        if translate_option and "Title (中文翻译版)" in df.columns:
            display_cols.insert(2, "Title (中文翻译版)")
        if translate_option and "Abstract (中文翻译版)" in df.columns:
            display_cols.insert(4, "Abstract (中文翻译版)")

        st.dataframe(df.loc[start:end, display_cols], use_container_width=True)

        st.subheader("📥 下载所有生成的文件")
        with open(pubmed_file, "rb") as f:
            st.download_button("📥 下载 PubMed Excel", f, file_name="pubmed_literature_results.xlsx")
        with open(baidu_file, "rb") as f:
            st.download_button("📥 下载 中文文献 Excel", f, file_name="chinese_literature_results.xlsx")
        with open(policy_file, "rb") as f:
            st.download_button("📥 下载 政策摘要 TXT", f, file_name="policy_information_summary.txt")
    else:
        st.error("❌ 未找到 PubMed 结果文件。")
