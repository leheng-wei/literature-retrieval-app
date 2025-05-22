import streamlit as st
from main_orchestrator import run_retrieval_workflow

st.set_page_config(page_title="医学文献检索工具", layout="wide")

st.title("📚 医学文献检索工具 (PubMed)")

# 输入区域
query_en = st.text_input("🔍 输入英文检索词", value="obesity AND type 2 diabetes mellitus")
time_range = st.selectbox("🕒 选择时间范围", ["近一年", "近六个月", "近三个月", "近一个月", "近一周"])
max_results = st.slider("最大结果数量", 5, 50, 10)

if st.button("🚀 开始检索"):
    with st.spinner("正在从PubMed检索文献..."):
        try:
            output_file = run_retrieval_workflow(
                query_en=query_en,
                time_period_str=time_range,
                max_pubmed_results=max_results
            )
            st.success("检索完成！")
            
            with open(output_file, "rb") as f:
                st.download_button(
                    label="📥 下载Excel结果",
                    data=f,
                    file_name="pubmed_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        except Exception as e:
            st.error(f"检索失败: {str(e)}")
