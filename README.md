# 医学文献与政策信息检索工具

## 概述

本工具旨在帮助医学编辑和研究人员从 PubMed、百度学术等数据库检索最新和相关的文献，并从 NMPA、FDA、WHO 等官方网站搜集相关医学领域的政策信息。工具会将检索到的文献信息（包括PMID、标题、摘要、发表日期、作者、DOI、文章类型、期刊、影响因子、关键词和全文链接）输出到 Excel 表格中，并将政策信息总结输出到文本文件中。

## 文件结构

```
medical_retrieval_tool/
├── main_orchestrator.py       # 主控制脚本，运行此脚本启动整个流程
├── pubmed_retriever.py        # PubMed文献检索模块
├── web_scraper.py             # 中文文献及政策信息抓取模块 (百度学术, NMPA, FDA, WHO)
├── data_processor.py          # 数据处理、翻译及影响因子匹配模块
├── output/                      # 输出文件夹，存放生成的Excel和文本文件
│   ├── pubmed_literature_results.xlsx
│   ├── chinese_literature_results.xlsx
│   └── policy_information_summary.txt
└── README.md                  # 本说明文件
```

## 环境要求

-   Python 3.8+
-   必要的Python库 (会自动尝试安装，但建议在虚拟环境中运行):
    -   `biopython`
    -   `requests`
    -   `beautifulsoup4`
    -   `googletrans==4.0.0-rc1` (注意版本)
    -   `pandas`
    -   `openpyxl`

## 配置

1.  **PubMed API 信息**:
    在 `main_orchestrator.py` 和 `pubmed_retriever.py` 文件顶部，您需要配置您的 PubMed API 邮箱和密钥。目前脚本中已硬编码了您提供的信息，请确认是否需要修改：
    ```python
    USER_EMAIL = "mingdan1021@gmail.com"
    USER_API_KEY = "fde2962074b8ec291444140a1325fe9d0707"
    ```

2.  **期刊影响因子文件**:
    脚本期望在 `/home/ubuntu/upload/JSR_impact_factors.xlsx` 路径下找到2024年的期刊影响因子数据。请确保该文件存在，或者修改 `data_processor.py` 文件中的 `IMPACT_FACTOR_FILE_PATH` 变量指向正确的文件路径。该Excel文件应至少包含两列，分别用于期刊名称和影响因子数值。脚本会尝试自动识别这两列（例如，列名包含 "Name" 或 "Journal" 以及 "JIF" 或 "Impact Factor"）。
    当前脚本识别的列名是：期刊名列为 `Name`，影响因子列为 `JIF`。

## 如何运行

1.  确保所有依赖库已安装。
2.  根据“配置”部分的说明，检查并设置好 PubMed API 信息和影响因子文件路径。
3.  打开终端或命令行，导航到 `medical_retrieval_tool` 文件夹。
4.  运行主脚本：
    ```bash
    python3 main_orchestrator.py
    ```
5.  脚本运行后，会在 `output` 文件夹内生成以下文件：
    -   `pubmed_literature_results.xlsx`: 包含从PubMed检索到的英文文献及其翻译和影响因子。
    -   `chinese_literature_results.xlsx`: 包含从百度学术检索到的中文文献。
    -   `policy_information_summary.txt`: 包含从NMPA、FDA、WHO等网站搜集到的政策信息总结。

## 修改检索参数

您可以在 `main_orchestrator.py` 脚本的 `if __name__ == "__main__":` 部分修改默认的检索参数：

-   `english_query`: PubMed 的英文检索词。
-   `chinese_query`: 百度学术及部分政策网站的中文检索词。
-   `search_time_period`: 文献检索的时间范围，例如 "近一年", "近三个月" 等 (具体支持的格式请参见 `pubmed_retriever.py` 中的 `get_date_range` 函数)。
-   `max_pubmed_results`: 从PubMed获取的最大文献数量。
-   `max_baidu_results`: 从百度学术获取的最大文献数量。
-   `max_policy_results`: 从每个政策信息源获取的最大条目数量。

## 注意事项与局限性

-   **网络抓取稳定性**: 中文文献检索（百度学术）和政策信息收集（NMPA, FDA, WHO等）依赖于网络抓取技术。这些网站的结构可能会发生变化，导致抓取脚本失效。如果遇到问题，`web_scraper.py` 文件中的选择器可能需要更新。NMPA等网站有较强的反爬机制，当前脚本的抓取成功率可能不高，可能需要更复杂的抓取策略（如使用Selenium等动态渲染技术）。
-   **翻译质量**: 标题和摘要的翻译由 `googletrans` 库提供，其质量可能无法完全达到专业人工翻译的水平，仅供参考。
-   **影响因子匹配**: 影响因子的匹配依赖于期刊名称的标准化处理。如果期刊名称在您的影响因子表格中与文献库中的名称差异较大，可能导致匹配失败。
-   **API使用限制**: 请遵守PubMed等API的使用频率限制，脚本中已加入少量延时，但大量或高频次使用仍需注意。
-   **错误处理**: 脚本包含基本的错误处理，但可能未覆盖所有异常情况。运行日志会打印在控制台，有助于排查问题。

## 未来可扩展方向

-   增加更多文献数据库的接口（如Web of Science API，若有权限）。
-   优化网络抓取模块，提高稳定性和覆盖范围，例如使用Selenium处理动态加载的页面。
-   引入更高级的自然语言处理技术，优化检索词转换和关键词提取。
-   提供图形用户界面（GUI）或Web界面，方便用户操作。
-   将配置项移至单独的配置文件中。

希望这个工具能为您的工作带来便利！

