import streamlit as st
from main_orchestrator import run_retrieval_workflow

st.set_page_config(page_title="医学文献与政策信息检索", layout="wide")

st.title("📚 医学文献与政策信息检索工具")

# 输入区域
query_en = st.text_input("🔍 输入英文关键词（PubMed 检索）", value="obesity AND type 2 diabetes mellitus")
query_cn = st.text_input("🔍 输入中文关键词（百度学术 & 政策）", value="肥胖与T2DM")

time_range = st.selectbox("🕒 选择时间范围", ["近一年", "近六个月", "近三个月", "近一个月", "近一周"])

max_pubmed = st.slider("PubMed 结果数量", 5, 50, 10)
max_baidu = st.slider("百度学术结果数量", 3, 20, 5)
max_policy = st.slider("政策信息来源（每来源最多）", 1, 10, 3)

# 启动按钮
if st.button("🚀 开始检索"):
    with st.spinner("正在检索中，请稍候..."):
        pubmed_file, baidu_file, policy_file = run_retrieval_workflow(
            query_en, query_cn, time_range,
            max_pubmed_results=max_pubmed,
            max_baidu_results=max_baidu,
            max_policy_results=max_policy
        )

    st.success("检索完成！📄 文件已保存。")

    # 提供下载链接
    with open(pubmed_file, "rb") as f:
        st.download_button("📥 下载 PubMed 结果 Excel", f, file_name="pubmed_literature_results.xlsx")

    with open(baidu_file, "rb") as f:
        st.download_button("📥 下载 百度学术 结果 Excel", f, file_name="chinese_literature_results.xlsx")

    with open(policy_file, "rb") as f:
        st.download_button("📥 下载 政策信息摘要 TXT", f, file_name="policy_information_summary.txt")
