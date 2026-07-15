import streamlit as st
import pandas as pd
import os
import glob
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Page configuration optimized for mobile viewport
st.set_page_config(
    page_title="Insurance Claims - H2O Pharmacy",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Navigation state management
if "page" not in st.session_state:
    st.session_state.page = "main"
if "selected_company" not in st.session_state:
    st.session_state.selected_company = None

# Custom styling for professional blue cards
st.markdown("""
    <style>
    .company-card {
        background: linear-gradient(135deg, #2b688a, #0f4c6e);
        color: white;
        padding: 20px;
        border-radius: 25px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        margin-bottom: 20px;
        text-align: right;
    }
    .company-title {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 15px;
        border-bottom: 1px solid rgba(255,255,255,0.2);
        padding-bottom: 5px;
    }
    .metric-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        font-size: 18px;
    }
    .metric-val {
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Cache data loading for 10 minutes to prevent continuous disk reading and freeze issues
@st.cache_data(ttl=600, show_spinner="Loading insurance dashboard data... ⏳")
def load_all_claims_data():
    CLAIMS_DIR = "."
    excel_files_list = glob.glob(os.path.join(CLAIMS_DIR, "*.xlsx"))
    
    comp_data = {}
    last_mod_time = None
    all_dt = []
    
    if not excel_files_list:
        return excel_files_list, comp_data, last_mod_time, all_dt

    for file in excel_files_list:
        try:
            mtime = os.path.getmtime(file)
            f_time = datetime.fromtimestamp(mtime)
            if last_mod_time is None or f_time > last_mod_time:
                last_mod_time = f_time
                
            df_file = pd.read_excel(file)
            
            if "تاريخ البيع" in df_file.columns:
                df_file["تاريخ البيع"] = pd.to_datetime(df_file["تاريخ البيع"], errors='coerce')
                all_dt.extend(df_file["تاريخ البيع"].dropna().tolist())
                
            if "تاريخ الدفعة" in df_file.columns:
                df_file["تاريخ الدفعة"] = pd.to_datetime(df_file["تاريخ الدفعة"], errors='coerce')
                
            # Numeric conversions
            df_file["القيمة المطلوبة"] = pd.to_numeric(df_file["القيمة المطلوبة"], errors='coerce').fillna(0)
            df_file["المدفوع"] = pd.to_numeric(df_file["المدفوع"], errors='coerce').fillna(0)
            df_file["المتبقي"] = df_file["القيمة المطلوبة"] - df_file["المدفوع"]
            
            company_name = os.path.splitext(os.path.basename(file))[0]
            comp_data[company_name] = df_file
            
        except Exception as e:
            st.error(f"Error reading file {os.path.basename(file)}: {e}")
            
    return excel_files_list, comp_data, last_mod_time, all_dt

# Load optimized data
excel_files, companies_data, last_modified_time, all_dates = load_all_claims_data()

# Render interface
if not excel_files:
    st.warning("⚠️ No Excel files found in the directory.")
elif companies_data:
    # Filter the last 12 months based on the latest available transaction date
    if all_dates:
        latest_date_in_data = max(all_dates)
        start_date_12m = latest_date_in_data - relativedelta(months=11)
        start_date_12m = start_date_12m.replace(day=1)
        date_range_str = f"From {start_date_12m.strftime('%Y/%m')} To {latest_date_in_data.strftime('%Y/%m')}"
    else:
        latest_date_in_data = datetime.now()
        start_date_12m = latest_date_in_data - relativedelta(months=11)
        start_date_12m = start_date_12m.replace(day=1)
        date_range_str = "Last 12 Months"

    # Logo display
    if os.path.exists("logo.png"):
        st.image("logo.png", width=180, use_container_width=False)
    elif os.path.exists("logo.jpg"):
        st.image("logo.jpg", width=180, use_container_width=False)

    # ==================== MAIN PAGE ====================
    if st.session_state.page == "main":
        st.markdown("<h3 style='text-align: center; color: #333;'>Insurance Companies Overview</h3>", unsafe_allow_html=True)
        update_str = last_modified_time.strftime('%Y/%m/%d') if last_modified_time else datetime.now().strftime('%Y/%m/%d')
        st.markdown(f"<div style='text-align: center; font-size: 18px; color: #555;'>Last updated: {update_str}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align: center; font-size: 18px; color: #555; margin-bottom: 20px;'>{date_range_str}</div>", unsafe_allow_html=True)

        for comp_name, df_orig in companies_data.items():
            # Apply 12-month boundary
            if "تاريخ البيع" in df_orig.columns and all_dates:
                df_comp = df_orig[(df_orig["تاريخ البيع"] >= pd.Timestamp(start_date_12m)) & 
                                  (df_orig["تاريخ البيع"] <= pd.Timestamp(latest_date_in_data))].copy()
            else:
                df_comp = df_orig.copy()

            comp_requested = df_comp["القيمة المطلوبة"].sum()
            comp_paid = df_comp["المدفوع"].sum()
            comp_remaining = df_comp["المتبقي"].sum()
            
            st.markdown(f"""
                <div class="company-card">
                    <div class="company-title">{comp_name}</div>
                    <div class="metric-row"><span class="metric-val">{comp_requested:,.3f}</span> <span>المطالبات (Requested)</span></div>
                    <div class="metric-row"><span class="metric-val">{comp_paid:,.3f}</span> <span>المدفوع (Paid)</span></div>
                    <div class="metric-row"><span class="metric-val">{comp_remaining:,.3f}</span> <span>المتبقي (Remaining)</span></div>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"🔎 View details for {comp_name}", key=f"btn_{comp_name}"):
                st.session_state.selected_company = comp_name
                st.session_state.page = "details"
                st.rerun()

    # ==================== DETAILS PAGE ====================
    elif st.session_state.page == "details":
        comp_name = st.session_state.selected_company
        df_orig_target = companies_data[comp_name].copy()

        # Apply 12-month boundary
        if "تاريخ البيع" in df_orig_target.columns and all_dates:
            df_target = df_orig_target[(df_orig_target["تاريخ البيع"] >= pd.Timestamp(start_date_12m)) & 
                                       (df_orig_target["تاريخ البيع"] <= pd.Timestamp(latest_date_in_data))].copy()
        else:
            df_target = df_orig_target.copy()

        if st.button("⬅️ Back to Main Page"):
            st.session_state.page = "main"
            st.session_state.selected_company = None
            st.rerun()

        st.markdown(f"<h2 style='text-align: center; color: #104e70;'>Company: {comp_name}</h2>", unsafe_allow_html=True)
        st.markdown("---")

        if "Insurance Company Name" in df_target.columns:
            box_options = ["All"] + list(df_target["Insurance Company Name"].dropna().unique())
            selected_box = st.selectbox("🎯 Filter by sub-insurance fund:", box_options)
            if selected_box != "All":
                df_target = df_target[df_target["Insurance Company Name"] == selected_box]

        st.markdown("### 📅 Monthly Financial Report (Last 12 Months)")
        if "تاريخ البيع" in df_target.columns and not df_target.empty:
            df_target["Month"] = df_target["تاريخ البيع"].dt.to_period("M")
            
            monthly_df = df_target.groupby("Month").agg({
                "القيمة المطلوبة": "sum",
                "المدفوع": "sum",
                "المتبقي": "sum"
            }).sort_index(ascending=False).head(12)
            
            total_remaining_sum = monthly_df["المتبقي"].sum()
            
            monthly_df.index = monthly_df.index.astype(str)
            monthly_df.columns = ["Total Claims", "Total Paid", "Total Remaining"]
            
            st.dataframe(monthly_df.style.format("{:,.3f} JOD"), use_container_width=True)
            st.info(f"📊 **Total outstanding balance for the listed period:** {total_remaining_sum:,.3f} JOD")
        else:
            st.info("No transaction date records available to generate monthly statistics.")

        st.markdown("---")

        st.markdown("### 💳 Received Payments Ledger")
        if "تاريخ الدفعة" in df_target.columns and "المدفوع" in df_target.columns:
            df_payments = df_target[df_target["تاريخ الدفعة"].notna() & (df_target["المدفوع"] > 0)].copy()
            
            if "تاريخ الدفعة" in df_payments.columns and all_dates:
                df_payments = df_payments[(df_payments["تاريخ الدفعة"] >= pd.Timestamp(start_date_12m)) & 
                                          (df_payments["تاريخ الدفعة"] <= pd.Timestamp(latest_date_in_data))].copy()

            if not df_payments.empty:
                df_payments = df_payments.sort_values(by="تاريخ الدفعة", ascending=False)
                df_payments["Payment Date"] = df_payments["تاريخ الدفعة"].dt.strftime('%Y-%m-%d')
                payments_summary = df_payments.groupby("Payment Date")["المدفوع"].sum().reset_index()
                payments_summary.columns = ["📆 Payment Date", "💰 Received Amount"]
                
                payments_summary = payments_summary.sort_values(by="📆 Payment Date", ascending=False)
                st.dataframe(payments_summary.style.format({"💰 Received Amount": "{:,.3f} JOD"}), use_container_width=True)
            else:
                st.info("No recorded payments found for this period.")
        else:
            st.warning("Could not find payment data columns to generate payments ledger.")