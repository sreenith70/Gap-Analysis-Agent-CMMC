import streamlit as st
import json
import pandas as pd
from pathlib import Path

# Corrected path for local run (inside /ui/)
base_dir = Path(__file__).resolve().parent.parent
policy_path = base_dir / "data" / "sample_policy.txt"
controls_path = base_dir / "controls" / "sample_controls.json"
report_path = base_dir / "outputs" / "gap_report.json"

st.set_page_config(page_title="CMMC Gap Analysis", layout="wide")
st.title("🛡️ CMMC Gap Analysis Dashboard")

# Sidebar Navigation
page = st.sidebar.radio("Navigate", ["View Policy", "View Controls", "View Gap Report"])

# ----------------------------
# File Loaders
# ----------------------------

def load_policy():
    try:
        if not policy_path.exists():
            return "Policy file not found."
        return policy_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error loading policy: {str(e)}"

def load_controls():
    try:
        if not controls_path.exists():
            return []
        with controls_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else [data]
    except Exception as e:
        st.error(f"Error loading controls: {str(e)}")
        return []

def load_gap_report():
    try:
        if not report_path.exists():
            return []
        with report_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else [data]
    except Exception as e:
        st.error(f"Error loading gap report: {str(e)}")
        return []

# ----------------------------
# Page: Policy Viewer
# ----------------------------
if page == "View Policy":
    st.subheader("📄 Sample Policy")
    policy_content = load_policy()
    if policy_content:
        st.code(policy_content, language="markdown")
    else:
        st.warning("No policy content available.")

# ----------------------------
# Page: Controls Viewer
# ----------------------------
elif page == "View Controls":
    st.subheader("🔍 CMMC Controls")
    controls_data = load_controls()
    
    if controls_data:
        try:
            df = pd.DataFrame(controls_data)
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Error displaying controls: {str(e)}")
            st.json(controls_data)
    else:
        st.warning("No control data available.")

# ----------------------------
# Page: Gap Report Viewer
# ----------------------------
elif page == "View Gap Report":
    st.subheader("📊 Gap Analysis Results")
    gap_data = load_gap_report()
    
    if not gap_data:
        st.warning("No gap report data found.")
    else:
        try:
            df = pd.DataFrame(gap_data)

            if df.empty:
                st.warning("Gap report is empty.")
            else:
                # Show columns
                st.markdown(f"**Available Columns:** {', '.join(df.columns)}")

                # Filter by status
                if "status" in df.columns:
                    status_options = df["status"].dropna().unique().tolist()
                    selected = st.multiselect("Filter by Status", status_options, default=status_options)
                    df = df[df["status"].isin(selected)]

                # Keyword Search
                text_columns = [c for c in df.columns if df[c].dtype == 'object']
                if text_columns:
                    col_to_search = st.selectbox("Search column:", text_columns)
                    keyword = st.text_input("Keyword:")
                    if keyword:
                        df = df[df[col_to_search].astype(str).str.contains(keyword, case=False, na=False)]

                # Display result
                st.dataframe(df, use_container_width=True)

                # Export
                if not df.empty:
                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button("⬇ Download CSV", csv, "gap_report_filtered.csv", "text/csv")
        except Exception as e:
            st.error(f"Error rendering gap report: {str(e)}")
            st.json(gap_data)
