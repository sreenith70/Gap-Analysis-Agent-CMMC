import streamlit as st
import json
import pandas as pd
from pathlib import Path

# Adjusted paths based on your setup
policy_path = Path("../cmmc_agent/data/sample_policy.txt")
controls_path = Path("controls/sample_controls.json")
report_path = Path("outputs/gap_report.json")

st.set_page_config(page_title="CMMC Gap Analysis", layout="wide")
st.title("🛡️ CMMC Gap Analysis Dashboard")

# Sidebar
page = st.sidebar.radio("Navigate", ["View Policy", "View Controls", "View Gap Report"])

def load_policy():
    """Load policy file with error handling"""
    try:
        if not policy_path.exists():
            return "Policy file not found. Please check the file path."
        return policy_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error loading policy: {str(e)}"

def load_controls():
    """Load controls JSON with error handling"""
    try:
        if not controls_path.exists():
            return []
        with controls_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            # Handle both list and dict formats
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'controls' in data:
                return data['controls']
            else:
                return [data]  # Single control object
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON in controls file: {str(e)}")
        return []
    except Exception as e:
        st.error(f"Error loading controls: {str(e)}")
        return []

def load_gap_report():
    """Load gap report JSON with error handling"""
    try:
        if not report_path.exists():
            return []
        with report_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            # Handle different JSON structures
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                if "results" in data:
                    return data["results"]
                elif "gaps" in data:
                    return data["gaps"]
                else:
                    return [data]  # Single result object
            else:
                return []
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON in gap report file: {str(e)}")
        return []
    except Exception as e:
        st.error(f"Error loading gap report: {str(e)}")
        return []

# Page routing
if page == "View Policy":
    st.subheader("📄 Sample Policy")
    policy_content = load_policy()
    if policy_content:
        st.code(policy_content, language="markdown")
    else:
        st.warning("No policy content available.")

elif page == "View Controls":
    st.subheader("🔍 CMMC Controls")
    controls_data = load_controls()
    
    if controls_data:
        try:
            df = pd.DataFrame(controls_data)
            if df.empty:
                st.warning("Controls data is empty.")
            else:
                st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating dataframe from controls: {str(e)}")
            st.json(controls_data)  # Show raw data as fallback
    else:
        st.warning("No controls data available.")

elif page == "View Gap Report":
    st.subheader("📊 Gap Analysis Results")
    gap_data = load_gap_report()
    
    if gap_data:
        try:
            df = pd.DataFrame(gap_data)
            
            if df.empty:
                st.warning("Gap report data is empty.")
            else:
                # Check if required columns exist
                available_columns = df.columns.tolist()
                st.info(f"Available columns: {', '.join(available_columns)}")
                
                # Filters - only add if columns exist
                if "status" in df.columns:
                    status_options = df["status"].unique()
                    status_filter = st.multiselect(
                        "Filter by Status", 
                        status_options, 
                        default=status_options
                    )
                    df = df[df["status"].isin(status_filter)]
                
                # Search functionality
                search_columns = [col for col in df.columns if df[col].dtype == 'object']
                if search_columns:
                    search_column = st.selectbox("Search in column:", search_columns)
                    keyword = st.text_input(f"Search in {search_column}")
                    
                    if keyword:
                        df = df[df[search_column].astype(str).str.contains(keyword, case=False, na=False)]
                
                # Display filtered dataframe
                st.dataframe(df, use_container_width=True)
                
                # CSV Download
                if not df.empty:
                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "⬇️ Download CSV", 
                        csv, 
                        "filtered_gap_report.csv", 
                        "text/csv"
                    )
                else:
                    st.info("No data matches the current filters.")
                    
        except Exception as e:
            st.error(f"Error processing gap report data: {str(e)}")
            st.json(gap_data)  # Show raw data as fallback
    else:
        st.warning("No gap report data available.")