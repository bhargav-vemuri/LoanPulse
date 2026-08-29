import sys
print(f"Python version: {sys.version}")

imports_to_test = [
    "pandas", "numpy", "sklearn", "lightgbm", "shap",
    "pyarrow", "joblib", "streamlit", "lifelines"
]

failed = []
for pkg in imports_to_test:
    try:
        __import__(pkg)
        print(f"Successfully imported {pkg}")
    except Exception as e:
        print(f"Failed to import {pkg}: {e}")
        failed.append(pkg)

try:
    import app
    print("Successfully imported app")
except Exception as e:
    print(f"Failed to import app: {e}")
    failed.append("app")

if failed:
    sys.exit(1)
else:
    print("ALL IMPORTS OK")
