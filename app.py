import streamlit as st
from main_orchestrator import run_retrieval_workflow
import os

st.set_page_config(page_title="医学文献与政策信息检索", layout="wide")

st.title("📚 医学文献与政策信息检索工具")

# 使用session_state来保存检索结果
if 'results_ready' not in st.session_state:
    st.session_state.results_ready = False
if 'output_files' not in st.session_state:
    st.session_state.output_files = {}

# 输入区域
query_en = st.text_input("🔍 输入英文关键词（PubMed 检索）", value="obesity AND type 2 diabetes mellitus")
query_cn = st.text_input("🔍 输入中文关键词（万方 & 政策）", value="肥胖与T2DM")

time_range = st.selectbox("🕒 选择时间范围", ["近一年", "近六个月", "近三个月", "近一个月", "近一周"])

max_pubmed = st.slider("PubMed 结果数量", 5, 50, 10)
max_baidu = st.slider("万方结果数量", 3, 20, 5)
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
        
        # 保存文件路径到session_state
        st.session_state.output_files = {
            "pubmed": pubmed_file,
            "baidu": baidu_file,
            "policy": policy_file
        }
        st.session_state.results_ready = True
    
    st.success("检索完成！📄 文件已保存。")

# 显示下载按钮（仅在结果就绪时显示）
if st.session_state.results_ready:
    st.subheader("📥 下载检索结果")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if os.path.exists(st.session_state.output_files["pubmed"]):
            with open(st.session_state.output_files["pubmed"], "rb") as f:
                st.download_button(
                    label="下载 PubMed 结果 Excel",
                    data=f,
                    file_name="pubmed_literature_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.warning("PubMed 结果文件不存在")
    
    with col2:
        if os.path.exists(st.session_state.output_files["baidu"]):
            with open(st.session_state.output_files["baidu"], "rb") as f:
                st.download_button(
                    label="下载 万方 结果 Excel",
                    data=f,
                    file_name="chinese_literature_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.warning("万方结果文件不存在")
    
    with col3:
        if os.path.exists(st.session_state.output_files["policy"]):
            with open(st.session_state.output_files["policy"], "rb") as f:
                st.download_button(
                    label="下载 政策信息摘要 TXT",
                    data=f,
                    file_name="policy_information_summary.txt",
                    mime="text/plain"
                )
        else:
            st.warning("政策信息文件不存在")
# app.py
# 在页面中添加新步骤
st.markdown("### 步骤3: 补充文献信息")
uploaded_supplement_file = st.file_uploader("上传翻译后的Excel文件", type=["xlsx"], key="supplement_file")

if uploaded_supplement_file is not None:
    # 保存上传的文件
    temp_input_path = "temp_translated_file.xlsx"
    with open(temp_input_path, "wb") as f:
        f.write(uploaded_supplement_file.getbuffer())
    
    if st.button("补充文献信息"):
        with st.spinner("正在补充文献信息，请稍候..."):
            output_file = "final_supplemented_results.xlsx"
            success = supplement_literature_info(temp_input_path, output_file, USER_EMAIL, USER_API_KEY)
            
            if success:
                st.success("文献信息补充完成！")
                # 更新下载按钮，只下载最终文件
                with open(output_file, "rb") as f:
                    st.download_button(
                        label="下载最终结果文件",
                        data=f,
                        file_name="final_supplemented_results.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.error("补充文献信息失败，请检查文件格式或稍后重试。")
