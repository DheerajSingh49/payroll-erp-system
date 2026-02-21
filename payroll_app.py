import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import io
import os
import requests
import time

# --- APP CONFIG ---
st.set_page_config(page_title="Payroll ERP System", layout="wide")

SHEET_ID = "1bAPy07MVYIVAcTtAhgVVJAVBagoHtpbZDF5xIpNFX8w"
sheet_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit?usp=sharing"

# --- INDIAN NUMBER TO WORDS LOGIC ---
def number_to_words_indian(number):
    def get_words(n):
        units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", 
                 "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
        tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
        if n < 20: return units[int(n)]
        if n < 100: return tens[int(n // 10)] + (" " + units[int(n % 10)] if (n % 10 != 0) else "")
        if n < 1000: return units[int(n // 100)] + " Hundred" + (" " + get_words(n % 100) if (n % 100 != 0) else "")
        return ""

    try:
        num = int(float(str(number).replace(',', '')))
        if num == 0: return "Zero Only"
        res = ""
        if num >= 10000000:
            res += get_words(num // 10000000) + " Crore "
            num %= 10000000
        if num >= 100000:
            res += get_words(num // 100000) + " Lakh "
            num %= 100000
        if num >= 1000:
            res += get_words(num // 1000) + " Thousand "
            num %= 1000
        res += get_words(num)
        return f"{res.strip()} Only"
    except:
        return ""

# --- UPDATED DATA LOADER WITH CACHE BUSTER ---
@st.cache_data(ttl=5) # Reduced TTL for faster updates
def load_data(worksheet_name):
    try:
        encoded_name = worksheet_name.replace(" ", "%20")
        # Added 'timestamp' to the URL to force Google to provide fresh data
        csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={encoded_name}&t={int(time.time())}"
        
        response = requests.get(csv_url)
        if response.status_code != 200:
            return pd.DataFrame()

        data = pd.read_csv(io.StringIO(response.text)).dropna(how='all', axis=0)
        data.columns = data.columns.str.strip()

        target_numeric = [
            "Salary", "Incentive Pay", "Allowances", "Professional Tax",
            "Absent Deduction", "Late Deduction", "Total Deduction", "Net Salary",
            "TP", "TA", "LA", "SL", "CL", "Total Working Hours", "Hours Deduction"
        ]

        for col in target_numeric:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
            else:
                data[col] = 0.0
        return data
    except Exception:
        return pd.DataFrame()

# --- PDF GENERATOR ---
def generate_pdf(data, month_name):
    pdf = FPDF()
    pdf.add_page()
    
    def get_val(col_name):
        return str(data[col_name]) if col_name in data and pd.notna(data[col_name]) else ""

    logo_path = "nav-logo-BrPcRVjp.png"
    if os.path.exists(logo_path):
        pdf.image(logo_path, 10, 10, 80)
    else:
        pdf.set_font("Helvetica", 'B', 18)
        pdf.set_text_color(0, 162, 232)
        pdf.text(10, 18, "NOVANECTAR")
        pdf.set_text_color(50, 50, 50)
        pdf.text(10, 23, "SERVICES PVT. LTD.")

    pdf.set_draw_color(0, 0, 0)
    pdf.set_text_color(0, 0, 0)
    pdf.rect(135, 10, 65, 18) 
    pdf.set_xy(135, 12)
    pdf.set_font("Helvetica", '', 10)
    pdf.cell(65, 5, "Pay Slip for the Month", ln=True, align='C')
    pdf.set_font("Helvetica", 'B', 12)
    pdf.set_x(135)
    pdf.cell(65, 7, f"{month_name} 2025", align='C')

    pdf.set_xy(10, 32)
    pdf.set_font("Helvetica", '', 9)
    pdf.cell(190, 5, "info@novanectar.co.in      +91 89798 91708", ln=True, align='C')
    pdf.set_font("Helvetica", '', 8)
    pdf.multi_cell(190, 4, "KHASRA NO.-1336/3/1, HARIPURAM, KANWALI GMS RD, Kanwali Road,\nDehradun, Dehradun- 248001, Uttarakhand", align='C')
    pdf.ln(4)

    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", 'B', 9)
    pdf.cell(95, 7, " EMPLOYEE SUMMARY", 1, 0, 'L', True)
    pdf.cell(95, 7, " A/C SUMMARY", 1, 1, 'L', True)

    pdf.set_font("Helvetica", '', 8)
    fields = [
        ("Emp ID", get_val('E_Id'), "PF A/C No", get_val('PF A/C No')),
        ("Emp Name", get_val('Employee Name'), "UAN", get_val('UAN')),
        ("Designation", get_val('Designation'), "Bank Name", get_val('Bank Name')),
        ("Department", get_val('Department'), "A/C No", get_val('A/C No')),
        ("Date of Joining", get_val('Date of Joining'), "IFSC", get_val('IFSC')),
        ("Pan Card", get_val('Pan Card'), "", ""),
        ("Gender", get_val('Gender'), "", "")
    ]
    for f1, v1, f2, v2 in fields:
        pdf.cell(47.5, 7, f" {f1}", 1, 0); pdf.cell(47.5, 7, f"{v1} ", 1, 0, 'R')
        pdf.cell(47.5, 7, f" {f2}", 1, 0); pdf.cell(47.5, 7, f"{v2} ", 1, 1, 'R')

    pdf.ln(4)
    pdf.cell(47.5, 7, " Total Working Days", 1, 0); pdf.cell(47.5, 7, get_val('Total Working Days'), 1, 0, 'R')
    pdf.cell(47.5, 7, " Leaves", 1, 0); pdf.cell(47.5, 7, get_val('CL'), 1, 1, 'R')
    pdf.cell(47.5, 7, " LOP Days", 1, 0); pdf.cell(47.5, 7, get_val('TA'), 1, 0, 'R')
    pdf.cell(47.5, 7, " Paid Days", 1, 0); pdf.cell(47.5, 7, get_val('TP'), 1, 1, 'R')

    pdf.ln(4)
    pdf.set_font("Helvetica", 'B', 9)
    pdf.cell(65, 7, " EARNINGS", 1, 0, 'L', True); pdf.cell(30, 7, "AMOUNT ", 1, 0, 'R', True)
    pdf.cell(65, 7, " DEDUCTIONS", 1, 0, 'L', True); pdf.cell(30, 7, "AMOUNT ", 1, 1, 'R', True)
    
    pdf.set_font("Helvetica", '', 8)
    rows = [
        ("Basic Pay", get_val('Salary'), "Provident Fund", get_val('Provident Fund')),
        ("House Rent Allowance", get_val('HRA'), "Professional Tax", get_val('Professional Tax')),
        ("Special Allowance", get_val('Special Allowance'), "", ""),
        ("Leave Travel", get_val('LTA'), "", ""),
        ("Allowance", get_val('Allowances'), "", ""),
        ("Differential Allowance", get_val('Differential Allowance'), "", ""),
        ("Sodexo Encashment", get_val('Incentive Pay'), "", "")
    ]
    for e_n, e_a, d_n, d_a in rows:
        pdf.cell(65, 7, f" {e_n}", 1, 0); pdf.cell(30, 7, f"{e_a} ", 1, 0, 'R')
        pdf.cell(65, 7, f" {d_n}", 1, 0); pdf.cell(30, 7, f"{d_a} ", 1, 1, 'R')

    pdf.set_font("Helvetica", 'B', 8)
    gross = (data['Salary'] if 'Salary' in data else 0) + (data['Incentive Pay'] if 'Incentive Pay' in data else 0)
    pdf.cell(65, 7, " Gross Earnings", 1, 0); pdf.cell(30, 7, f"{gross:.0f} ", 1, 0, 'R')
    pdf.cell(65, 7, " Total Deductions", 1, 0); pdf.cell(30, 7, f"{get_val('Total Deduction')} ", 1, 1, 'R')

    pdf.ln(4)
    pdf.set_fill_color(33, 63, 33); pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", 'B', 10)
    net_val = get_val('Net Salary')
    pdf.cell(190, 10, f" TOTAL NET PAYABLE {' '*80} {net_val}", 1, 1, 'L', True)
    
    pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", '', 9); pdf.set_fill_color(255, 255, 255)
    pdf.cell(190, 15, "", 1, 1)
    pdf.set_y(pdf.get_y() - 10)
    words = number_to_words_indian(net_val)
    pdf.cell(185, 8, f"Amounts in Words: {words}", 0, 1, 'R')
    pdf.ln(10); pdf.set_font("Helvetica", 'B', 9)
    pdf.cell(190, 5, "Note:-", 0, 1)
    return pdf.output()

# --- AUTH STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user_role': None, 'user_id': None})

# --- MAIN LOGIC ---
if not st.session_state['logged_in']:
    df_login = load_data("Login ") 
    st.title("Payroll and ERP Login")
    if df_login.empty:
        st.error("Cannot connect to Google Sheets. Verify 'Login ' tab name and Sharing permissions.")
    else:
        tab_emp, tab_adm = st.tabs(["Employee Portal", "Admin Portal"])
        with tab_emp:
            emp_id = st.text_input("Employee ID", key="emp_id_login")
            emp_pwd = st.text_input("Password", type="password", key="emp_pwd_login")
            if st.button("Login", key="emp_btn"):
                user_match = df_login[df_login['E_Id'].astype(str) == str(emp_id)]
                if not user_match.empty:
                    initial = str(user_match.iloc[0]['Employee Name'])[0].upper()
                    if emp_pwd == f"{initial}@123456":
                        st.session_state.update({'logged_in': True, 'user_role': 'Employee', 'user_id': str(emp_id)})
                        st.rerun()
                    else: st.error("Incorrect Password")
                else: st.error("ID not found")
        with tab_adm:
            adm_user = st.text_input("Username", key="adm_user")
            adm_pwd = st.text_input("Password", type="password", key="adm_pwd")
            if st.button("Admin Access", key="adm_btn"):
                if adm_user == "admin" and adm_pwd == "admin123":
                    st.session_state.update({'logged_in': True, 'user_role': 'Admin'})
                    st.rerun()
                else: st.error("Invalid Admin Credentials")

else:
    # --- SIDEBAR WITH SYNC BUTTON ---
    with st.sidebar:
        if st.button("Logout"):
            st.session_state.update({'logged_in': False, 'user_role': None, 'user_id': None})
            st.rerun()
        st.divider()
        if st.button("🔄 Sync with Google Sheets"):
            st.cache_data.clear()
            st.toast("Fetching latest data...")
            st.rerun()
        st.divider()
        available_months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
        selected_month = st.selectbox("Select Payroll Month", available_months)

    df = load_data(selected_month)
    
    if df.empty:
        st.warning(f"No data found for {selected_month}. Check your Google Sheet tab name.")
    else:
        if st.session_state['user_role'] == 'Admin':
            st.title(f"Admin Portal - {selected_month}")
            st.markdown(f"[Edit Dataset]({sheet_url})")
            view_mode = st.radio("Select View", ["Company Statistics", "Individual Records"], horizontal=True)
            if view_mode == "Company Statistics":
                st.subheader(f"Global Payroll ({selected_month})")
                c1, c2 = st.columns(2)
                with c1:
                    dept_sal = df.groupby("Department")["Net Salary"].sum().reset_index()
                    st.plotly_chart(px.bar(dept_sal, x="Department", y="Net Salary", title="Net Payout by Dept", color="Department", text_auto=True), use_container_width=True)
                with c2:
                    st.plotly_chart(px.bar(df.sort_values("Total Working Hours"), x="Employee Name", y="Total Working Hours", color="Department", title="Employee Productivity (Hours)"), use_container_width=True)
                st.dataframe(df)
            else:
                selected_name = st.selectbox("Search Employee Name", df["Employee Name"].unique())
                emp_rec = df[df["Employee Name"] == selected_name]
                st.dataframe(emp_rec)
                v1, v2 = st.columns(2)
                with v1:
                    attn = pd.DataFrame({'Status': ['Present', 'Absent', 'Late', 'Sick', 'Casual'], 'Days': [emp_rec.iloc[0]['TP'], emp_rec.iloc[0]['TA'], emp_rec.iloc[0]['LA'], emp_rec.iloc[0]['SL'], emp_rec.iloc[0]['CL']]})
                    st.plotly_chart(px.bar(attn, x='Status', y='Days', color='Status', title="Individual Attendance Summary"), use_container_width=True)
                with v2:
                    st.plotly_chart(px.pie(names=["Basic Salary", "Incentive Pay", "Allowances"], values=[emp_rec.iloc[0]['Salary'], emp_rec.iloc[0]['Incentive Pay'], emp_rec.iloc[0]['Allowances']], title="Earnings Breakdown", hole=0.5), use_container_width=True)
                pdf_bytes = generate_pdf(emp_rec.iloc[0], selected_month)
                st.download_button(f"Download Payslip ({selected_month})", data=bytes(pdf_bytes), file_name=f"Payslip_{selected_name}_{selected_month}.pdf")
        else:
            user_row = df[df['E_Id'].astype(str) == st.session_state['user_id']]
            if user_row.empty:
                st.warning(f"No record found for you in {selected_month}.")
            else:
                st.title(f"Welcome, {user_row.iloc[0]['Employee Name']}")
                st.info(f"Viewing: {selected_month}")
                st.dataframe(user_row)
                m1, m2, m3 = st.columns(3)
                m1.metric("Net Salary", f"Rs.{user_row.iloc[0]['Net Salary']:.2f}")
                m2.metric("Days Present", f"{int(user_row.iloc[0]['TP'])} Days")
                m3.metric("Total Hours", f"{user_row.iloc[0]['Total Working Hours']} hrs")
                st.divider()
                v1, v2 = st.columns(2)
                with v1:
                    my_attn = pd.DataFrame({'Status': ['Present', 'Absent', 'Late', 'Sick', 'Casual'], 'Days': [user_row.iloc[0]['TP'], user_row.iloc[0]['TA'], user_row.iloc[0]['LA'], user_row.iloc[0]['SL'], user_row.iloc[0]['CL']]})
                    st.plotly_chart(px.bar(my_attn, x='Status', y='Days', title="My Attendance Performance", color='Status'), use_container_width=True)
                with v2:
                    st.plotly_chart(px.pie(names=["Absent Deduction", "Net Salary", "Hours Deduction","Professional Tax"], values=[user_row.iloc[0]['Absent Deduction'], user_row.iloc[0]['Net Salary'], user_row.iloc[0]['Hours Deduction'], user_row.iloc[0]['Professional Tax']], title="My Deductions Breakdown", hole=0.5), use_container_width=True)
                pdf_out = generate_pdf(user_row.iloc[0], selected_month)
                st.download_button(f"Download {selected_month} Payslip (PDF)", data=bytes(pdf_out), file_name=f"Payslip_{selected_month}.pdf")