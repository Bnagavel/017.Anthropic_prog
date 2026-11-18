"""Root entry point for F&DT Spectrum Assistant UI (`ui_app.py`).

Supports both:
- `streamlit run ui_app.py`
- `py -3.12 ui_app.py` (standalone FastAPI/Uvicorn on http://127.0.0.1:8501)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))


def _is_running_in_streamlit() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx  # type: ignore

        return get_script_run_ctx() is not None
    except Exception:
        return False


if _is_running_in_streamlit():
    from fdt_localai.ui.app import run_streamlit_ui

    run_streamlit_ui()
elif __name__ == "__main__":
    from fdt_localai.ui.app import serve_local_ui

    serve_local_ui(host="127.0.0.1", port=8501)
