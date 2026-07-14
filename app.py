import streamlit as st
import pandas as pd
import os
import glob
from datetime import datetime
from dateutil.relativedelta import relativedelta

# إعداد الصفحة لتناسب الموبايل بشكل عمودي ومريح
st.set_page_config(
    page_title="تفاصيل شركات التأمين - صيدلية H2O",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# إدارة التنقل بين الصفحات عبر الذاكرة المؤقتة (Session State)
if "page" not in st.session_state:
    st.session_state.page = "main"
if "selected_company" not in st.session_state:
    st.session_state.selected_company = None

# تصفيف مخصص لمحاكاة تصميم البطاقات الزرقاء
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

# مجلد قراءة الملفات
CLAIMS_DIR = "."
excel_files = glob.glob(os.path.join(CLAIMS_DIR, "*.xlsx"))

if not excel_files:
    st.warning("⚠️ لا توجد ملفات إكسل داخل المجلد حالياً.")
else:
    companies_data = {}
    last_modified_time = None
    all_dates = []
    
    # قراءة وتجهيز البيانات الأساسية
    for file in excel_files:
        try:
            mtime = os.path.getmtime(file)
            f_time = datetime.fromtimestamp(mtime)
            if last_modified_time is None or f_time > last_modified_time:
                last_modified_time = f_time
                
            df_file = pd.read_excel(file)
            
            if "تاريخ البيع" in df_file.columns:
                df_file["تاريخ البيع"] = pd.to_datetime(df_file["تاريخ البيع"], errors='coerce')
                all_dates.extend(df_file["تاريخ البيع"].dropna().tolist())
                
            if "تاريخ الدفعة" in df_file.columns:
                df_file["تاريخ الدفعة"] = pd.to_datetime(df_file["تاريخ الدفعة"], errors='coerce')
                
            df_file["القيمة المطلوبة"] = pd.to_numeric(df_file["القيمة المطلوبة"], errors='coerce').fillna(0)
            df_file["المدفوع"] = pd.to_numeric(df_file["المدفوع"], errors='coerce').fillna(0)
            df_file["المتبقي"] = df_file["القيمة المطلوبة"] - df_file["المدفوع"]
            
            company_name = os.path.splitext(os.path.basename(file))[0]
            companies_data[company_name] = df_file
            
        except Exception as e:
            st.error(f"خطأ في قراءة الملف {os.path.basename(file)}: {e}")

    if companies_data:
        # تحديد نطاق الـ 12 شهراً الأخيرة
        if all_dates:
            latest_date_in_data = max(all_dates)
            start_date_12m = latest_date_in_data - relativedelta(months=11)
            start_date_12m = start_date_12m.replace(day=1)
            date_range_str = f"من {start_date_12m.strftime('%Y/%m')} وحتى {latest_date_in_data.strftime('%Y/%m')}"
        else:
            latest_date_in_data = datetime.now()
            start_date_12m = latest_date_in_data - relativedelta(months=11)
            start_date_12m = start_date_12m.replace(day=1)
            date_range_str = "آخر 12 شهر"

        # عرض الشعار العلوي
        if os.path.exists("logo.png"):
            st.image("logo.png", width=180, use_container_width=False)
        elif os.path.exists("logo.jpg"):
            st.image("logo.jpg", width=180, use_container_width=False)

        # ==================== الصفحة الأولى ====================
        if st.session_state.page == "main":
            st.markdown("<h3 style='text-align: center; color: #333;'>تفاصيل شركات التأمين</h3>", unsafe_allow_html=True)
            update_str = last_modified_time.strftime('%Y/%m/%d') if last_modified_time else "2026/07/13"
            st.markdown(f"<div style='text-align: center; font-size: 18px; color: #555;'>آخر تحديث {update_str}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: center; font-size: 18px; color: #555; margin-bottom: 20px;'>{date_range_str}</div>", unsafe_allow_html=True)

            for comp_name, df_orig in companies_data.items():
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
                        <div class="metric-row"><span class="metric-val">{comp_requested:,.3f}</span> <span>المطالبات</span></div>
                        <div class="metric-row"><span class="metric-val">{comp_paid:,.3f}</span> <span>المدفوع</span></div>
                        <div class="metric-row"><span class="metric-val">{comp_remaining:,.3f}</span> <span>المتبقي</span></div>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"🔎 عرض تفاصيل وتقارير {comp_name}", key=f"btn_{comp_name}"):
                    st.session_state.selected_company = comp_name
                    st.session_state.page = "details"
                    st.rerun()

        # ==================== الصفحة الثانية ====================
        elif st.session_state.page == "details":
            comp_name = st.session_state.selected_company
            df_orig_target = companies_data[comp_name].copy()

            if "تاريخ البيع" in df_orig_target.columns and all_dates:
                df_target = df_orig_target[(df_orig_target["تاريخ البيع"] >= pd.Timestamp(start_date_12m)) & 
                                           (df_orig_target["تاريخ البيع"] <= pd.Timestamp(latest_date_in_data))].copy()
            else:
                df_target = df_orig_target.copy()

            if st.button("⬅️ عودة للصفحة الرئيسية"):
                st.session_state.page = "main"
                st.session_state.selected_company = None
                st.rerun()

            st.markdown(f"<h2 style='text-align: center; color: #104e70;'>شركة: {comp_name}</h2>", unsafe_allow_html=True)
            st.markdown("---")

            if "Insurance Company Name" in df_target.columns:
                box_options = ["الكل"] + list(df_target["Insurance Company Name"].dropna().unique())
                selected_box = st.selectbox("🎯 تصفية حسب صندوق التأمين الفرعي:", box_options)
                if selected_box != "الكل":
                    df_target = df_target[df_target["Insurance Company Name"] == selected_box]

            st.markdown("### 📅 التقرير المالي الشهري (آخر 12 شهر)")
            if "تاريخ البيع" in df_target.columns and not df_target.empty:
                df_target["الشهر"] = df_target["تاريخ البيع"].dt.to_period("M")
                
                monthly_df = df_target.groupby("الشهر").agg({
                    "القيمة المطلوبة": "sum",
                    "المدفوع": "sum",
                    "المتبقي": "sum"
                }).sort_index(ascending=False).head(12)
                
                total_remaining_sum = monthly_df["المتبقي"].sum()
                
                monthly_df.index = monthly_df.index.astype(str)
                monthly_df.columns = ["مجموع المطالبات", "مجموع المدفوع", "المجموع المتبقي"]
                
                st.dataframe(monthly_df.style.format("{:,.3f} د.أ"), use_container_width=True)
                st.info(f"📊 **إجمالي المتبقي المستحق لكافة الأشهُر المذكورة أعلاه:** {total_remaining_sum:,.3f} د.أ")
            else:
                st.info("لا توجد بيانات تواريخ متوفرة لتوليد جدول الأشهر.")

            st.markdown("---")

            st.markdown("### 💳 سجل وتاريخ الدفعات المستلمة")
            if "تاريخ الدفعة" in df_target.columns and "المدفوع" in df_target.columns:
                df_payments = df_target[df_target["تاريخ الدفعة"].notna() & (df_target["المدفوع"] > 0)].copy()
                
                if "تاريخ الدفعة" in df_payments.columns and all_dates:
                    df_payments = df_payments[(df_payments["تاريخ الدفعة"] >= pd.Timestamp(start_date_12m)) & 
                                              (df_payments["تاريخ الدفعة"] <= pd.Timestamp(latest_date_in_data))].copy()

                if not df_payments.empty:
                    df_payments = df_payments.sort_values(by="تاريخ الدفعة", ascending=False)
                    df_payments["تاريخ الدفعة"] = df_payments["تاريخ الدفعة"].dt.strftime('%Y-%m-%d')
                    payments_summary = df_payments.groupby("تاريخ الدفعة")["المدفوع"].sum().reset_index()
                    payments_summary.columns = ["📆 تاريخ الدفعة", "💰 قيمة الدفعة المستلمة"]
                    
                    payments_summary = payments_summary.sort_values(by="📆 تاريخ الدفعة", ascending=False)
                    st.dataframe(payments_summary.style.format({"💰 قيمة الدفعة المستلمة": "{:,.3f} د.أ"}), use_container_width=True)
                else:
                    st.info("لا توجد دفعات مسجلة ومرحلة بـ 'تاريخ الدفعة' داخل هذا الملف لهذه الفترة.")
            else:
                st.warning("لم يتم العثور على حقول 'تاريخ الدفعة' أو 'المدفوع' لإنشاء كشف الدفعات.")