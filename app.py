from pathlib import Path
import streamlit as st
from doctor import Repository, diagnose

st.set_page_config(page_title="Repo Doctor", page_icon="🔎")
st.title("Repo Doctor")
st.caption("Version 0.6 · One corrective retry")
st.write("Investigate a code failure with a model running on your Mac.")
st.caption("Source access is read-only. Suggested fixes are unverified; no code or tests are executed.")
repo_path = st.text_input("Repository folder", str(Path(__file__).parent / "demo_repo"))
model = st.selectbox("Local model", ["qwen3:1.7b", "qwen3:0.6b"])
issue = st.text_area("Error log or problem", 'pipeline.py report_duration(2500) returns 2500000 instead of 2.5 seconds.', max_chars=2000, height=150)
focus = st.text_input("Optional focus file (relative path)", placeholder="pipeline.py")
signature = (repo_path, issue, focus, model)
if st.button("1. Inspect repository"):
    try:
        repo = Repository(repo_path)
        context = repo.context(issue, focus)
        st.session_state["inspection"] = {"signature": signature, "files": repo.files, "context": context, "selection": repo.selection, "notes": repo.retrieval_notes}
        st.session_state.pop("result", None)
    except (ValueError, OSError) as exc:
        st.error(str(exc))
inspection = st.session_state.get("inspection")
if inspection and inspection["signature"] == signature:
    with st.expander(f"Eligible source files ({len(inspection['files'])})"):
        st.code("\n".join(inspection["files"]))
    st.subheader("Selected evidence")
    st.table(inspection["selection"])
    for note in inspection["notes"]:
        st.info(note)
    st.subheader("Evidence to send to your local model")
    st.code(inspection["context"] or "No matching source. Add a filename or symbol to the error description.")
    st.caption("These excerpts and your error description are sent locally; the second call also receives the first diagnosis. Review for embedded secrets. Re-inspect after editing repository files.")
    if st.button("2. Diagnose", disabled=not bool(inspection["context"])):
        st.session_state.pop("result", None)
        progress = st.empty()
        with st.spinner("Your local model is investigating…"):
            try:
                st.session_state["result"] = diagnose(issue, inspection["context"], model, repo_path, progress=progress.info)
            except (ValueError, RuntimeError, OSError) as exc:
                st.error(str(exc))
            finally:
                progress.empty()
    if "result" in st.session_state:
        result = st.session_state["result"]
        st.subheader("Suggested diagnosis")
        if result["edit_status"] == "checks_passed":
            st.success("Edit checks passed: exact unique source match, changed replacement, and Python syntax where applicable. Correctness is not verified; no changes applied or tests run.")
        elif result["edit_status"] == "rejected":
            st.warning("Proposed edit rejected. See the reason below.")
        st.caption(f"Corrective retries used: {result.get('retry_count', 0)}/1")
        st.markdown(result["answer"])
        with st.expander("Raw responses — diagnosis and edit attempts"):
            st.code(result["raw_response"], language="text")
        st.caption(f"{result['elapsed_seconds']} seconds total · {result['model']}")
        with st.expander("Run details"):
            st.json(result["settings"])
            st.json(result.get("attempts", []))
            for stage in result["stages"]:
                st.write(f"{stage['stage']}: {stage['elapsed_seconds']} s; {stage['tokens_per_second']} generated tokens/s (may include thinking)")
        if result["output_truncated"]:
            st.warning("A stage hit the output limit. No patch was accepted.")
        st.download_button("Download diagnosis", result["answer"], "diagnosis.md")
elif inspection:
    st.info("Inputs changed. Inspect the repository again before diagnosing.")
