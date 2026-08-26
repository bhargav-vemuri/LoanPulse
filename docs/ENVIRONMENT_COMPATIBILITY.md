# Environment Compatibility

| Category | Details |
| :--- | :--- |
| **Environment** | Sandbox execution container |
| **Python Version** | Python 3.14.0 |
| **Dependency Versions** | `streamlit==1.51.0`, `pandas==2.3.3`, `pyarrow==25.0.1`, `lightgbm==4.7.0`, `shap==0.52.0` |
| **Expected Supported Environment** | Python 3.10, 3.11, or 3.12 |
| **Actual Launch Result** | `FAIL` (Application crashes on startup) |
| **Known Incompatibilities** | Python 3.14 breaks `protobuf` (dependency of Streamlit) due to `TypeError: Metaclasses with custom tp_new are not supported.` |
| **Recommended Execution Environment** | Run `streamlit run app.py` on a standard Python 3.10/3.11 local workstation. |
