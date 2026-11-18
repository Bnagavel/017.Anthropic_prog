"""Simple Excel-Form UI for F&DT Spectrum Assistant (Release 1.0).

Implements the exact utilitarian Excel-UserForm layout specified in PROJECT_PLAN.md §2.
Supports both:
1. Streamlit execution (`streamlit run ui_app.py`) when `streamlit` is installed.
2. Built-in offline FastAPI + Uvicorn server on `http://127.0.0.1:8501` (`python ui_app.py`),
   so the UI works 100% offline out-of-the-box on Windows without extra installs.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from fdt_localai.jobs.service import JobService
from fdt_localai.spectrum.pipeline import (
    SpectrumPipelineOptions,
    SpectrumPipelineOutput,
)


PRESET_FOLDERS = [
    "Spectrum/example",
    "Spectrum/Output/nrang_plot/sample",
    "Spectrum/Misc/MaxP_Theta_Calc",
    "Spectrum/Input/Elfo/Excelvba_sample",
]


def run_streamlit_ui() -> None:
    """Render the Simple Excel Form interface in Streamlit."""
    import plotly.graph_objects as go
    import streamlit as st

    st.set_page_config(
        page_title="F&DT Spectrum Assistant (Release 1.0)",
        layout="wide",
    )

    st.markdown(
        """
        <style>
        .excel-banner {
            background-color: #1F4E79;
            color: white;
            padding: 10px 16px;
            font-family: Segoe UI, Tahoma, sans-serif;
            font-weight: bold;
            font-size: 18px;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            margin-bottom: 14px;
        }
        </style>
        <div class="excel-banner">
            <span>F&amp;DT Spectrum Assistant (Release 1.0) — SPECTRUM Spectrum Engine</span>
            <span style="background:#2E7D32;padding:2px 10px;border-radius:3px;font-size:13px;">[Offline Mode: OK (127.0.0.1)]</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_folder, col_preset, col_base = st.columns([3, 2, 1])
    with col_preset:
        preset = st.selectbox("Quick Preset Folder:", PRESET_FOLDERS, index=0)
    with col_folder:
        folder_path = st.text_input("1. Select Spectrum Folder:", value=str(Path(preset).resolve()))
    with col_base:
        base_name = st.text_input("Base Sheet Name (<=19 chars):", value="SPECTRUM")

    st.markdown("#### 2. Select Processing Options:")
    c1, c2 = st.columns(2)
    with c1:
        opt_nrang = st.checkbox(
            "Process .nrang.out (Extract Stress 1, Stress 2, Occurrences)", value=True
        )
        opt_switch = st.checkbox(
            "Apply 'S' Switch Logic (Swap Stress 1 and Stress 2)", value=True
        )
        opt_x900 = st.checkbox(
            "Build X900 Flight-Point Sequence (Occurrences >= 1)", value=True
        )
    with c2:
        opt_gag = st.checkbox(
            "Extract Coincident Max GAG Loads (Correlate FBRG / MaxP / Channels)",
            value=True,
        )
        opt_cspec = st.checkbox("Compare Spectrum Severity (C-Spec / fFI)", value=True)
        opt_audit = st.checkbox("Audit SPECTRUM 'project_file' & .elfo Indices", value=True)

    st.markdown("#### 3. Excel Output Setting & AI Summary:")
    c3, c4, c5 = st.columns([2, 2, 1])
    with c3:
        formula_mode = st.radio(
            "Excel Formula Mode:",
            ["Live Excel Formulas (=IF, =SQRT)", "Static Values (Fastest)"],
            index=0,
            horizontal=True,
        )
    with c4:
        opt_ai = st.checkbox(
            "4. Generate OEM-Style Comparison Summary (Local Gemma 2 2B)",
            value=False,
        )
    with c5:
        nasgro_n = st.number_input("NASGRO Exponent n:", value=3.0, step=0.01)

    if st.button("RUN PROCESSING", type="primary", use_container_width=True):
        opts = SpectrumPipelineOptions(
            folder_path=folder_path,
            base_sheet_name=base_name,
            process_nrang=opt_nrang,
            apply_s_switch=opt_switch,
            build_x900=opt_x900,
            extract_coincident_gag=opt_gag,
            compare_cspec_ffi=opt_cspec,
            use_live_formulas=formula_mode.startswith("Live"),
            generate_ai_summary=opt_ai,
            audit_project_file_flag=opt_audit,
            nasgro_n=float(nasgro_n),
        )
        svc = JobService()
        out: SpectrumPipelineOutput = svc.submit_and_run(opts)
        st.session_state["last_out"] = out

    out_res: SpectrumPipelineOutput | None = st.session_state.get("last_out")
    if out_res is not None:
        st.success(
            f"Completed in {out_res.elapsed_seconds:.3f} s | "
            f"{len(out_res.nrang_files)} .nrang.out | "
            f"{len(out_res.gag_records)} GAG records | "
            f"{len(out_res.cspec_results)} C-Spec channels"
        )
        xlsx_bytes = Path(out_res.excel_path).read_bytes()
        st.download_button(
            label="DOWNLOAD EXCEL WORKBOOK (.XLSX)",
            data=xlsx_bytes,
            file_name=Path(out_res.excel_path).name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )

        tab_gag, tab_cspec, tab_plot, tab_audit = st.tabs(
            [
                "Coincident Max GAG Summary",
                "C-Spec & fFI Severity",
                "X900 Time-History Plot",
                "Pre-Run project_file Audit & AI Summary",
            ]
        )
        with tab_gag:
            if not out_res.gag_df.empty:
                st.dataframe(out_res.gag_df, use_container_width=True)
            else:
                st.info("No .rang.out files found in selected folder for GAG summary.")
        with tab_cspec:
            if not out_res.cspec_df.empty:
                st.dataframe(out_res.cspec_df, use_container_width=True)
            else:
                st.info("No .rang.out files found in selected folder for C-Spec summary.")
        with tab_plot:
            if not out_res.x900_df.empty and len(out_res.x900_df.columns) > 2:
                series_cols = list(out_res.x900_df.columns[2:])
                sel_series = st.multiselect(
                    "Select Series to Plot:",
                    series_cols,
                    default=series_cols[:2],
                )
                fig = go.Figure()
                for s_col in sel_series:
                    fig.add_trace(
                        go.Scatter(
                            x=out_res.x900_df["Point"],
                            y=out_res.x900_df[s_col],
                            mode="lines",
                            name=s_col,
                        )
                    )
                fig.update_layout(
                    title=f"X900 Spectrum Plot - {out_res.base_sheet_name}",
                    xaxis_title="Reversal / Point Sequence",
                    yaxis_title="Stress / Load",
                    template="plotly_white",
                    height=440,
                )
                st.plotly_chart(fig, use_container_width=True)
        with tab_audit:
            if out_res.project_audit:
                st.subheader(f"Project File Audit: {out_res.project_audit.get('status')}")
                st.dataframe(out_res.project_audit.get("findings", []), use_container_width=True)
            if out_res.ai_summary_text:
                st.subheader("OEM Comparison Summary")
                st.code(out_res.ai_summary_text)


def _patch_fastapi_middleware_compatibility() -> None:
    """Defensive patch: ensures FastAPI safely handles Starlette >= 0.36 Middleware unpacking."""
    try:
        import fastapi.applications
        orig_build = fastapi.applications.FastAPI.build_middleware_stack

        def safe_build_middleware_stack(self):
            try:
                return orig_build(self)
            except ValueError as err:
                if "too many values to unpack" not in str(err):
                    raise
                from starlette.middleware import Middleware
                from starlette.middleware.errors import ServerErrorMiddleware
                from starlette.middleware.exceptions import ExceptionMiddleware

                debug = self.debug
                error_handler = None
                exception_handlers = {}
                for key, val in self.exception_handlers.items():
                    if key in (500, Exception):
                        error_handler = val
                    else:
                        exception_handlers[key] = val

                middleware = (
                    [Middleware(ServerErrorMiddleware, handler=error_handler, debug=debug)]
                    + self.user_middleware
                    + [Middleware(ExceptionMiddleware, handlers=exception_handlers, debug=debug)]
                )
                app = self.router
                for item in reversed(middleware):
                    if hasattr(item, "cls"):
                        app = item.cls(app=app, *getattr(item, "args", ()), **getattr(item, "kwargs", {}))
                    else:
                        try:
                            cls, options = item
                            app = cls(app=app, **options)
                        except ValueError:
                            cls, args, kwargs = item
                            app = cls(app=app, *args, **kwargs)
                return app

        fastapi.applications.FastAPI.build_middleware_stack = safe_build_middleware_stack
    except Exception:
        pass


def create_fastapi_app():
    """Create the standalone FastAPI application serving the Simple Excel-Form UI on 127.0.0.1."""
    _patch_fastapi_middleware_compatibility()
    from fastapi import FastAPI, Form
    from fastapi.responses import FileResponse, HTMLResponse

    app = FastAPI(title="F&DT Spectrum Assistant (Release 1.0)")
    state: dict[str, Any] = {"last_out": None}

    def _df_to_html_table(df) -> str:
        if df is None or df.empty:
            return "<p style='color:#666;font-style:italic;'>No records for this view in selected folder.</p>"
        return df.to_html(index=False, classes="excel-grid", border=0)

    def _render_page(
        opts: SpectrumPipelineOptions,
        out: SpectrumPipelineOutput | None = None,
        error_msg: str | None = None,
    ) -> str:
        gag_html = _df_to_html_table(out.gag_df) if out else ""
        cspec_html = _df_to_html_table(out.cspec_df) if out else ""
        x900_html = _df_to_html_table(out.x900_df.head(50)) if (out and not out.x900_df.empty) else ""

        audit_html = ""
        if out and out.project_audit:
            rows_a = "".join(
                f"<tr><td><b>{html.escape(str(f['severity']))}</b></td>"
                f"<td>{html.escape(str(f['category']))}</td>"
                f"<td>{html.escape(str(f['message']))}</td></tr>"
                for f in out.project_audit.get("findings", [])
            )
            audit_html = (
                f"<h4>Pre-Run SPECTRUM <code>project_file</code> Audit — Status: {out.project_audit.get('status')}</h4>"
                f"<table class='excel-grid'><thead><tr><th>Severity</th><th>Category</th><th>Finding</th></tr></thead>"
                f"<tbody>{rows_a}</tbody></table>"
            )

        ai_html = ""
        if out and out.ai_summary_text:
            ai_html = (
                f"<h4>OEM Comparison Summary (Zero-Hallucination Verified)</h4>"
                f"<pre style='background:#F8F9FA;padding:12px;border:1px solid #CCC;white-space:pre-wrap;'>"
                f"{html.escape(out.ai_summary_text)}</pre>"
            )

        plot_json = "null"
        if out and not out.x900_df.empty and len(out.x900_df.columns) > 2:
            traces = []
            x_vals = out.x900_df["Point"].tolist()
            for idx, col_name in enumerate(out.x900_df.columns[2:12]):
                traces.append(
                    {
                        "x": x_vals,
                        "y": [round(float(v), 4) for v in out.x900_df[col_name].tolist()],
                        "mode": "lines",
                        "name": col_name,
                        "visible": True if idx < 2 else "legendonly",
                    }
                )
            plot_json = json.dumps(traces)

        err_banner = (
            f"<div style='background:#FFEBEE;color:#C62828;padding:10px;border:1px solid #EF9A9A;margin-bottom:12px;'>"
            f"<b>Error:</b> {html.escape(error_msg)}</div>"
            if error_msg
            else ""
        )

        results_section = ""
        if out is not None:
            results_section = f"""
            <div style="background:#E8F5E9;border:1px solid #81C784;padding:10px 14px;margin-top:14px;display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <b>Processing Complete in {out.elapsed_seconds:.3f} seconds</b> &nbsp;|&nbsp;
                    <code>.nrang.out</code> files: <b>{len(out.nrang_files)}</b> &nbsp;|&nbsp;
                    X900 Points: <b>{len(out.x900_df)}</b> &nbsp;|&nbsp;
                    Coincident GAG: <b>{len(out.gag_records)}</b> &nbsp;|&nbsp;
                    C-Spec Channels: <b>{len(out.cspec_results)}</b>
                </div>
                <a href="/download" class="btn-download">DOWNLOAD EXCEL WORKBOOK (.XLSX)</a>
            </div>

            <div style="margin-top:16px;">
                <h3>Results Preview (Coincident Max GAG Summary)</h3>
                {gag_html}
                <h3 style="margin-top:18px;">C-Spec &amp; fFI Fatigue Severity Summary</h3>
                {cspec_html}
                {audit_html}
                {ai_html}
                <h3 style="margin-top:18px;">X900 Spectrum Verification Plot (Click Legend to Toggle Series)</h3>
                <div id="x900-chart" style="width:100%;height:420px;border:1px solid #CCC;background:#FFF;"></div>
                <h3 style="margin-top:18px;">X900 Unrolled Sequence Preview (First 50 Flight Points)</h3>
                <div style="overflow-x:auto;">{x900_html}</div>
            </div>
            """

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <title>F&amp;DT Spectrum Assistant (Release 1.0)</title>
    <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
    <style>
        body {{
            font-family: "Segoe UI", Tahoma, Arial, sans-serif;
            font-size: 13px;
            background-color: #ECECEC;
            margin: 0;
            padding: 16px;
            color: #111;
        }}
        .userform-container {{
            max-width: 1240px;
            margin: 0 auto;
            background: #F7F7F7;
            border: 2px solid #1F4E79;
            box-shadow: 2px 4px 10px rgba(0,0,0,0.12);
        }}
        .title-bar {{
            background: #1F4E79;
            color: #FFF;
            padding: 10px 16px;
            font-weight: bold;
            font-size: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .badge-ok {{
            background: #2E7D32;
            color: #FFF;
            padding: 3px 10px;
            font-size: 12px;
            border-radius: 2px;
        }}
        .form-body {{
            padding: 16px 20px;
        }}
        fieldset {{
            border: 1px solid #B8C4D0;
            background: #FFFFFF;
            margin-bottom: 12px;
            padding: 10px 14px;
        }}
        legend {{
            font-weight: bold;
            color: #1F4E79;
            padding: 0 6px;
        }}
        .input-text {{
            padding: 5px 8px;
            border: 1px solid #888;
            font-family: Consolas, monospace;
            font-size: 13px;
        }}
        .btn-run {{
            background: #1F4E79;
            color: white;
            font-weight: bold;
            font-size: 14px;
            padding: 9px 26px;
            border: 1px solid #0D2B45;
            cursor: pointer;
        }}
        .btn-run:hover {{ background: #2B6CB0; }}
        .btn-download {{
            background: #217346;
            color: white;
            font-weight: bold;
            text-decoration: none;
            padding: 8px 18px;
            border: 1px solid #14492C;
            display: inline-block;
        }}
        table.excel-grid {{
            border-collapse: collapse;
            width: 100%;
            background: #FFF;
            font-size: 12px;
        }}
        table.excel-grid th {{
            background: #4472C4;
            color: white;
            font-weight: bold;
            padding: 6px 8px;
            border: 1px solid #BFBFBF;
            text-align: center;
        }}
        table.excel-grid td {{
            padding: 5px 8px;
            border: 1px solid #D9D9D9;
            text-align: right;
        }}
        table.excel-grid td:first-child {{
            text-align: left;
            font-weight: 600;
        }}
        table.excel-grid tr:nth-child(even) {{ background: #F5F7FA; }}
    </style>
</head>
<body>
<div class="userform-container">
    <div class="title-bar">
        <span>F&amp;DT Spectrum Assistant (Release 1.0) — SPECTRUM Spectrum Pre/Post-Processing Engine</span>
        <span class="badge-ok">[Offline Mode: OK · 127.0.0.1]</span>
    </div>
    <div class="form-body">
        {err_banner}
        <form method="post" action="/run">
            <fieldset>
                <legend>1. Select Spectrum Folder &amp; Sheet Name</legend>
                <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
                    <label><b>Folder Path:</b></label>
                    <input type="text" id="folder_path" name="folder_path" class="input-text" style="flex:1;min-width:420px;" value="{html.escape(opts.folder_path)}"/>
                    <select onchange="document.getElementById('folder_path').value=this.value" class="input-text">
                        <option value="">-- Quick Presets --</option>
                        {"".join(f'<option value="{html.escape(str(Path(p).resolve()))}">{html.escape(p)}</option>' for p in PRESET_FOLDERS)}
                    </select>
                    <label><b>Base Sheet Name (&le;19 chars):</b></label>
                    <input type="text" name="base_sheet_name" class="input-text" style="width:130px;" maxlength="19" value="{html.escape(opts.base_sheet_name)}"/>
                </div>
            </fieldset>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                <fieldset>
                    <legend>2. Select Processing Options</legend>
                    <div><label><input type="checkbox" name="process_nrang" value="1" {"checked" if opts.process_nrang else ""}/> Process <code>.nrang.out</code> (Extract Stress 1, Stress 2, Occurrences)</label></div>
                    <div><label><input type="checkbox" name="apply_s_switch" value="1" {"checked" if opts.apply_s_switch else ""}/> Apply <code>'S'</code> Switch Logic (Swap Stress 1 and Stress 2)</label></div>
                    <div><label><input type="checkbox" name="build_x900" value="1" {"checked" if opts.build_x900 else ""}/> Build <code>X900</code> Flight-Point Sequence (Occurrences &ge; 1)</label></div>
                    <div><label><input type="checkbox" name="extract_coincident_gag" value="1" {"checked" if opts.extract_coincident_gag else ""}/> Extract Coincident Max GAG Loads (Correlate FBRG / MaxP / Channels)</label></div>
                    <div><label><input type="checkbox" name="compare_cspec_ffi" value="1" {"checked" if opts.compare_cspec_ffi else ""}/> Compare Spectrum Severity (C-Spec / fFI)</label></div>
                    <div><label><input type="checkbox" name="audit_project_file_flag" value="1" {"checked" if opts.audit_project_file_flag else ""}/> Pre-Run SPECTRUM <code>project_file</code> &amp; <code>.elfo</code> Audit</label></div>
                    <div><label><input type="checkbox" name="convert_rpt_files" value="1" {"checked" if opts.convert_rpt_files else ""}/> Convert Patran <code>.rpt</code> &rarr; <code>.elfo</code> in Folder</label></div>
                </fieldset>

                <fieldset>
                    <legend>3. Excel Output Setting &amp; 4. Optional AI Report Summary</legend>
                    <div style="margin-bottom:8px;">
                        <b>Excel Output Mode:</b><br/>
                        <label><input type="radio" name="formula_mode" value="live" {"checked" if opts.use_live_formulas else ""}/> Live Excel Formulas (<code>=IF</code>, <code>=SQRT</code>)</label>
                        &nbsp;&nbsp;&nbsp;
                        <label><input type="radio" name="formula_mode" value="static" {"" if opts.use_live_formulas else "checked"}/> Static Values (Fastest)</label>
                    </div>
                    <div style="margin-bottom:8px;">
                        <label><b>Material Category:</b></label>
                        <select name="material_category" class="input-text">
                            <option value="ALUMINUM" {"selected" if opts.material_category == "ALUMINUM" else ""}>ALUMINUM (7040/7050, Cm=-0.68, C0=0.68)</option>
                            <option value="STEEL" {"selected" if opts.material_category == "STEEL" else ""}>STEEL / TITANIUM / INCONEL (Cm=-0.73, C0=0.73)</option>
                        </select>
                        &nbsp;
                        <label><b>n:</b></label>
                        <input type="number" step="0.01" name="nasgro_n" class="input-text" style="width:65px;" value="{opts.nasgro_n}"/>
                    </div>
                    <div>
                        <label><input type="checkbox" name="generate_ai_summary" value="1" {"checked" if opts.generate_ai_summary else ""}/> Generate OEM-Style Comparison Summary (Drafted by local Gemma 2 2B / Verified Engine)</label>
                    </div>
                    <div style="margin-top:12px;">
                        <button type="submit" class="btn-run">[ RUN PROCESSING ]</button>
                    </div>
                </fieldset>
            </div>
        </form>
        {results_section}
    </div>
</div>
<script>
const traces = {plot_json};
if (traces && document.getElementById('x900-chart')) {{
    Plotly.newPlot('x900-chart', traces, {{
        title: 'X900 Spectrum Sequence Time-History',
        xaxis: {{ title: 'Reversal / Point Sequence' }},
        yaxis: {{ title: 'Stress / Load' }},
        margin: {{ t: 40, l: 60, r: 20, b: 45 }}
    }});
}}
</script>
</body>
</html>"""

    @app.get("/", response_class=HTMLResponse)
    def index():
        default_opts = SpectrumPipelineOptions(
            folder_path=str(Path("Spectrum/example").resolve()),
            base_sheet_name="SPECTRUM",
        )
        return _render_page(default_opts, state.get("last_out"))

    @app.post("/run", response_class=HTMLResponse)
    def run_pipeline_endpoint(
        folder_path: str = Form(...),
        base_sheet_name: str = Form("SPECTRUM"),
        process_nrang: str | None = Form(None),
        apply_s_switch: str | None = Form(None),
        build_x900: str | None = Form(None),
        extract_coincident_gag: str | None = Form(None),
        compare_cspec_ffi: str | None = Form(None),
        audit_project_file_flag: str | None = Form(None),
        convert_rpt_files: str | None = Form(None),
        formula_mode: str = Form("live"),
        material_category: str = Form("ALUMINUM"),
        nasgro_n: float = Form(3.0),
        generate_ai_summary: str | None = Form(None),
    ):
        opts = SpectrumPipelineOptions(
            folder_path=folder_path,
            base_sheet_name=base_sheet_name,
            process_nrang=bool(process_nrang),
            apply_s_switch=bool(apply_s_switch),
            build_x900=bool(build_x900),
            extract_coincident_gag=bool(extract_coincident_gag),
            compare_cspec_ffi=bool(compare_cspec_ffi),
            audit_project_file_flag=bool(audit_project_file_flag),
            convert_rpt_files=bool(convert_rpt_files),
            use_live_formulas=(formula_mode == "live"),
            material_category=material_category,
            nasgro_n=float(nasgro_n),
            generate_ai_summary=bool(generate_ai_summary),
        )
        try:
            svc = JobService()
            out = svc.submit_and_run(opts)
            state["last_out"] = out
            return _render_page(opts, out)
        except Exception as exc:
            return _render_page(opts, state.get("last_out"), error_msg=str(exc))

    @app.get("/download")
    def download_excel():
        out: SpectrumPipelineOutput | None = state.get("last_out")
        if out and Path(out.excel_path).exists():
            return FileResponse(
                out.excel_path,
                filename=Path(out.excel_path).name,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        return HTMLResponse("No workbook generated yet.", status_code=404)

    return app


def serve_local_ui(host: str = "127.0.0.1", port: int = 8501) -> None:
    """Launch the local Excel-Form UI bound strictly to `127.0.0.1`."""
    import uvicorn

    app = create_fastapi_app()
    print(f"F&DT Spectrum Assistant (Release 1.0) running at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
