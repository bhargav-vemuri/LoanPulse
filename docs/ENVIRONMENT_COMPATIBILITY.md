# Environment Compatibility

| Category | Details |
| :--- | :--- |
| **Supported Deployment Python Version** | Python 3.11 (Recommended for stability and pre-built PyArrow wheels) |
| **Local Development Python Version** | Python 3.14.0 (Supported with streamlit>=1.52.0) |
| **Dependency Versions** | streamlit==1.52.0, pandas==2.3.3, pyarrow==22.0.0, lightgbm==4.7.0, shap==0.52.0 |
| **Actual Launch Result** | PASS |
| **Installation Command** | pip install -r requirements.txt |
| **Startup Command** | streamlit run app.py |

## Notes
- To resolve PyArrow compilation issues on modern Python environments (e.g. Python 3.14 without MSVC tools), the Streamlit and PyArrow versions are pinned to 1.52.0 and 22.0.0 respectively. 
- The application utilizes repository-relative paths for all serialized artifacts (data/processed/*) and models (models/*), requiring no absolute paths or specific usernames.
- The raw dataset, training-time dependencies, and massive prediction snapshot arrays are omitted from runtime requirements.
