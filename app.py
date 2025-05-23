import streamlit as st
from main_orchestrator import run_retrieval_workflow

st.set_page_config(page_title="医学文献检索工具", layout="wide")

st.title("📚 医学文献检索工具")

# 输入区域
query_en = st.text_input("🔍 请输入PubMed 检索式", value="obesity AND type 2 diabetes mellitus")

time_range = st.selectbox("🕒 选择时间范围", ["近一年", "近六个月", "近三个月", "近一个月", "近一周"])

max_pubmed = st.slider("PubMed 结果数量", 5, 50, 10)

# 启动按钮
if st.button("🚀 开始检索"):
    with st.spinner("正在检索中，请稍候..."):
        pubmed_file = run_retrieval_workflow(
            query_en, 
            time_range,
            max_pubmed_results=max_pubmed
        )

    st.success("检索完成！📄 文件已保存。")

    # 提供下载链接
    with open(pubmed_file, "rb") as f:
        st.download_button("📥 下载 PubMed 结果 Excel", f, file_name="pubmed_literature_results.xlsx")
