

import os
import streamlit as st
import black
import subprocess
from radon.complexity import cc_visit, SCORE
import difflib
import tempfile


st.set_page_config(layout="wide")
st.title(":blue[Ai] Code Reveiwer")

file = st.file_uploader("Upload your file", type=".py")


def cc_score_to_grade(score):
    if score < 5:
        return "A"
    elif score < 10:
        return "B"
    elif score < 20:
        return "C"
    elif score < 30:
        return "D"
    elif score < 40:
        return "E"
    else:
        return "F"


def grade_to_color(grade):
    return {
        "A": "green",
        "B": "lightgreen",
        "C": "orange",
        "D": "darkorange",
        "E": "orangered",
        "F": "red",
    }.get(grade, "gray")


def grade_summary_text(avg_grade):
    summaries = {
        "A": "**Excellent!** Your code is very simple and easy to maintain. Great job!",
        "B": "**Good.** Your code is relatively simple with minor complexity. Keep it up!",
        "C": "**Moderate.** Your code has a fair amount of complexity. Consider refactoring some functions.",
        "D": "**Complex.** Your code is getting harder to read and maintain. Break down large functions or logic.",
        "E": "**Very Complex.** Your code has significant complexity. Refactoring is strongly recommended.",
        "F": "**Unmaintainable.** Your code is extremely complex and should be restructured immediately to avoid bugs and maintenance issues.",
    }
    return summaries.get(avg_grade, "No summary available for this grade.")



if file is not None:
    code_bytes = file.read()
    code_str = code_bytes.decode("utf-8").replace("\r\n", "\n")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp:
        tmp.write(code_str.encode("utf-8"))
        temp_file_path = tmp.name

    ct1, ct2 = st.columns(2,border=True)
    try:

        with ct1:
            st.header("Original Code")
            st.code(code_str, language="python")

        with ct2:
            st.header("Formatted Code")

            try:
                formatted_code = black.format_str(code_str, mode=black.Mode())
            except black.InvalidInput:
                st.error("❌ Black could not format the code due to syntax errors.")
                formatted_code = code_str

        

            diff = difflib.unified_diff(
                code_str.splitlines(),
                formatted_code.splitlines(),
                fromfile="Original",
                tofile="Formatted",
                lineterm="",
            )

            diff_text = "\n".join(diff)
            opts = ["Difference", "Formatted Code"]
            sel = st.selectbox("select what you want to see ", opts)
            if sel == opts[0]:
                st.code(diff_text, language="diff")
            elif sel == opts[1]:
                st.subheader("Formatted using black")
                st.code(formatted_code, language="python")


        st.subheader("Flake8 errors")
        try:
            result2 = subprocess.run(["flake8", temp_file_path], capture_output=True, text=True)
        except FileNotFoundError:
            st.error("⚠️ Flake8 not found. Please install it with `pip install flake8`.")
            result2 = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        cleaned_output = result2.stdout.replace(temp_file_path, file.name)
        st.code(cleaned_output, language="bash")

        error_lines = cleaned_output.strip().split("\n")
        error_count = 0 if error_lines == [''] else len(error_lines)

        st.info(f"🔍 Total Flake8 Issues: {error_count}")

        st.subheader("Complexity of code using radon ")
        with open(temp_file_path, "r") as f:
            code = f.read()
        results = cc_visit(code)

        if results:
            avg_score = sum(r.complexity for r in results) / len(results)
            avg_grade = cc_score_to_grade(avg_score)
            color = grade_to_color(avg_grade)
        else:
            avg_score, avg_grade, color = 0, "N/A", "gray"

        st.markdown(f"""
        <b>Average Cyclomatic Complexity Score:</b>
        <span style='color:{color}'>{avg_score:.2f}</span>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <b>Average Cyclomatic Complexity Grade:</b>
        <span style='color:{color}'>{avg_grade}</span>
        """, unsafe_allow_html=True)


        summary = grade_summary_text(avg_grade)
        st.info(summary)

        file_name = f"{file.name}"

        report_text = f"""
    ===========================
    📄 AI Code Review Summary
    ===========================

    📁 File Name: {file_name}

    Cyclomatic Complexity Score: {avg_score:.2f}
    Cyclomatic Complexity Grade: {avg_grade}
    Summary: {grade_summary_text(avg_grade)}

    ---------------------------
    ❌ Flake8 Issues:
    ---------------------------
    {result2.stdout}

    ---------------------------
    👨‍💻 Original Code:
    ---------------------------
    {code_str}

    ---------------------------
    ✨ Formatted Code:
    ---------------------------
    {formatted_code}
    """
        st.download_button(
            label="📥 Download Full Report",
            data=report_text,
            file_name="code_review_report.txt",
            mime="text/plain",
        )
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

else:
    st.markdown("### Please upload a file to move forward")




