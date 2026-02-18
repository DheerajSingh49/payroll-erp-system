import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
from streamlit_gsheets import GSheetsConnection
import io

st.set_page_config(page_title="Payroll ERP System", layout="wide")

# Your Sheet ID
SHEET_ID = "1bAPy07MVYIVAcTtAhgVVJAVBagoHtpbZDF5xIpNFX8w"
sheet_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit?usp=sharing"


# --- AUTOMATIC MONTH DISCOVERY ---
def get_all_sheets():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        spreadsheet = conn.client.open_by_url(sheet_url)
        sheet_names = [s.title for s in spreadsheet.worksheets()]
        return sheet_names
    except Exception:
        # Fallback to current sheets if API detection hits an issue
        return ["JUNE", "JULY"]


# --- ROBUST DATA LOADER ---
@st.cache_data(ttl=300)
def load_data(worksheet_name):
    csv_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={worksheet_name}"
    try:
        data = pd.read_csv(csv_url)
        data = data.dropna(axis=1, how='all')
        data.columns = data.columns.str.strip()

        target_numeric = [
            "Salary", "Incentive Pay", "Allowances", "Professional Tax",
            "Absent Deduction", "Late Deduction", "Total Deduction", "Net Salary",
            "TP", "TA", "LA", "SL", "CL", "Total Working Hours"
        ]

        for col in target_numeric:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
            else:
                data[col] = 0.0

        if "Total Working Hours" not in data.columns or data["Total Working Hours"].sum() == 0:
            if "TP" in data.columns:
                data["Total Working Hours"] = data["TP"] * 8
        return data
    except Exception as e:
        st.error(f"Error loading {worksheet_name}: {e}")
        return pd.DataFrame()


# --- LOGIN SYSTEM ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_role'] = None
    st.session_state['user_id'] = None


def login_page():
    current_sheets = get_all_sheets()
    df_login = load_data(current_sheets[0])

    st.title("Payroll ERP Secure Login")
    if df_login.empty:
        st.error("Cannot connect to Google Sheets. Please ensure the sheet is set to 'Anyone with the link can view'.")
        return

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
                else:
                    st.error("Incorrect Password")
            else:
                st.error("ID not found")

    with tab_adm:
        adm_user = st.text_input("Username", key="adm_user")
        adm_pwd = st.text_input("Password", type="password", key="adm_pwd")
        if st.button("Admin Access", key="adm_btn"):
            if adm_user == "admin" and adm_pwd == "admin123":
                st.session_state.update({'logged_in': True, 'user_role': 'Admin'})
                st.rerun()
            else:
                st.error("Invalid Admin Credentials")


if not st.session_state['logged_in']:
    login_page()
else:
    if st.sidebar.button("Logout"):
        st.session_state.update({'logged_in': False, 'user_role': None, 'user_id': None})
        st.rerun()

    st.sidebar.divider()

    # --- AUTOMATIC MONTH SWITCHER ---
    available_months = get_all_sheets()
    selected_month = st.sidebar.selectbox("Select Payroll Month", available_months)
    df = load_data(selected_month)


    # --- PDF GENERATOR ---
    def generate_pdf(data):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", 'B', 16)
        pdf.cell(190, 10, "SALARY PAYMENT SLIP", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Helvetica", '', 10)
        pdf.cell(45, 7, "Employee Name:", 0, 0);
        pdf.set_font("Helvetica", 'B', 10);
        pdf.cell(50, 7, f"{data['Employee Name']}", 0, 0)
        pdf.set_font("Helvetica", '', 10);
        pdf.cell(45, 7, "Employee ID:", 0, 0);
        pdf.set_font("Helvetica", 'B', 10);
        pdf.cell(50, 7, f"{data['E_Id']}", 0, 1)
        pdf.set_font("Helvetica", '', 10);
        pdf.cell(45, 7, "Department:", 0, 0);
        pdf.set_font("Helvetica", 'B', 10);
        pdf.cell(50, 7, f"{data['Department']}", 0, 0)
        pdf.set_font("Helvetica", '', 10);
        pdf.cell(45, 7, "Working Days:", 0, 0);
        pdf.set_font("Helvetica", 'B', 10);
        pdf.cell(50, 7, f"{int(data['TP'])}", 0, 1)
        pdf.set_font("Helvetica", '', 10);
        pdf.cell(45, 7, "Total Hours:", 0, 0);
        pdf.set_font("Helvetica", 'B', 10);
        pdf.cell(50, 7, f"{data['Total Working Hours']}", 0, 0)
        pdf.set_font("Helvetica", '', 10);
        pdf.cell(45, 7, "Payment Period:", 0, 0);
        pdf.set_font("Helvetica", 'B', 10);
        pdf.cell(50, 7, f"{selected_month}", 0, 1)
        pdf.ln(5)
        pdf.set_fill_color(230, 230, 230);
        pdf.set_font("Helvetica", 'B', 10)
        pdf.cell(65, 10, "Earnings", 1, 0, 'C', True);
        pdf.cell(30, 10, "Amount", 1, 0, 'C', True)
        pdf.cell(65, 10, "Deductions", 1, 0, 'C', True);
        pdf.cell(30, 10, "Amount", 1, 1, 'C', True)
        pdf.set_font("Helvetica", '', 10)
        pdf.cell(65, 8, "Basic Salary", 1, 0, 'L');
        pdf.cell(30, 8, f"{data['Salary']:.2f}", 1, 0, 'R')
        pdf.cell(65, 8, "Absent Deduction", 1, 0, 'L');
        pdf.cell(30, 8, f"{data['Absent Deduction']:.2f}", 1, 1, 'R')
        pdf.cell(65, 8, "Incentive Pay", 1, 0, 'L');
        pdf.cell(30, 8, f"{data['Incentive Pay']:.2f}", 1, 0, 'R')
        pdf.cell(65, 8, "Professional Tax", 1, 0, 'L');
        pdf.cell(30, 8, f"{data['Professional Tax']:.2f}", 1, 1, 'R')
        pdf.cell(65, 8, "Allowances", 1, 0, 'L');
        pdf.cell(30, 8, f"{data['Allowances']:.2f}", 1, 0, 'R')
        pdf.cell(65, 8, "Late Deduction", 1, 0, 'L');
        pdf.cell(30, 8, f"{data['Late Deduction']:.2f}", 1, 1, 'R')
        total_earn = data['Salary'] + data['Incentive Pay'] + data['Allowances']
        pdf.set_font("Helvetica", 'B', 10);
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(65, 8, "Total Earnings", 1, 0, 'L', True);
        pdf.cell(30, 8, f"{total_earn:.2f}", 1, 0, 'R', True)
        pdf.cell(65, 8, "Total Deductions", 1, 0, 'L', True);
        pdf.cell(30, 8, f"{data['Total Deduction']:.2f}", 1, 1, 'R', True)
        pdf.ln(5);
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(160, 10, "NET PAYABLE:", 0, 0, 'R')
        pdf.set_fill_color(220, 230, 255);
        pdf.cell(30, 10, f"{data['Net Salary']:.2f}", 1, 1, 'C', True)
        pdf.ln(20);
        pdf.set_font("Helvetica", '', 10)
        pdf.cell(95, 10, "__________________________", 0, 0, 'C');
        pdf.cell(95, 10, "__________________________", 0, 1, 'C')
        pdf.cell(95, 5, "Employee Signature", 0, 0, 'C');
        pdf.cell(95, 5, "Employer Signature", 0, 1, 'C')
        return pdf.output()


    # --- ADMIN VIEW ---
    if st.session_state['user_role'] == 'Admin':
        st.title(f"Admin Portal - {selected_month}")

        # --- RESTORED LINK TO EDIT DATASET ---
        st.markdown(f"[Edit Dataset]({sheet_url})")

        view_mode = st.radio("Select View", ["Company Statistics", "Individual Records"], horizontal=True)
        if view_mode == "Company Statistics":
            st.subheader(f"Global Payroll ({selected_month})")
            c1, c2 = st.columns(2)
            with c1:
                dept_sal = df.groupby("Department")["Net Salary"].sum().reset_index()
                st.plotly_chart(
                    px.bar(dept_sal, x="Department", y="Net Salary", title="Net Payout by Dept", color="Department",
                           text_auto=True), use_container_width=True)
            with c2:
                st.plotly_chart(
                    px.bar(df.sort_values("Total Working Hours"), x="Employee Name", y="Total Working Hours",
                           color="Department", title="Employee Productivity (Hours)"), use_container_width=True)
            st.dataframe(df)
        else:
            selected_name = st.selectbox("Search Employee Name", df["Employee Name"].unique())
            emp_rec = df[df["Employee Name"] == selected_name]
            st.dataframe(emp_rec)
            v1, v2 = st.columns(2)
            with v1:
                attn = pd.DataFrame({'Status': ['Present', 'Absent', 'Late', 'Sick', 'Casual'],
                                     'Days': [emp_rec.iloc[0]['TP'], emp_rec.iloc[0]['TA'], emp_rec.iloc[0]['LA'],
                                              emp_rec.iloc[0]['SL'], emp_rec.iloc[0]['CL']]})
                st.plotly_chart(
                    px.bar(attn, x='Status', y='Days', color='Status', title="Individual Attendance Summary"),
                    use_container_width=True)
            with v2:
                st.plotly_chart(px.pie(names=["Basic Salary", "Incentive Pay", "Allowances"],
                                       values=[emp_rec.iloc[0]['Salary'], emp_rec.iloc[0]['Incentive Pay'],
                                               emp_rec.iloc[0]['Allowances']], title="Earnings Breakdown", hole=0.5),
                                use_container_width=True)
            pdf_bytes = generate_pdf(emp_rec.iloc[0])
            st.download_button(f"Download Payslip ({selected_month})", data=bytes(pdf_bytes),
                               file_name=f"Payslip_{selected_name}_{selected_month}.pdf")

    # --- EMPLOYEE VIEW ---
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
                my_attn = pd.DataFrame({'Status': ['Present', 'Absent', 'Late', 'Sick', 'Casual'],
                                        'Days': [user_row.iloc[0]['TP'], user_row.iloc[0]['TA'], user_row.iloc[0]['LA'],
                                                 user_row.iloc[0]['SL'], user_row.iloc[0]['CL']]})
                st.plotly_chart(
                    px.bar(my_attn, x='Status', y='Days', title="My Attendance Performance", color='Status'),
                    use_container_width=True)
            with v2:
                st.plotly_chart(px.pie(names=["Absent Deduction", "Net Salary", "Hours Deduction","Professional Tax"],
                                       values=[user_row.iloc[0]['Absent Deduction'],
                                               user_row.iloc[0]['Net Salary'],
                                               user_row.iloc[0]['Hours Deduction'],
                                               user_row.iloc[0]['Professional Tax']], title="My Deductions Breakdown",
                                       hole=0.5), use_container_width=True)
            pdf_out = generate_pdf(user_row.iloc[0])
            st.download_button(f"Download {selected_month} Payslip (PDF)", data=bytes(pdf_out),
                               file_name=f"Payslip_{selected_month}.pdf")