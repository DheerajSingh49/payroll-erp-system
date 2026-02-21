# Employee MIS & Payroll ERP System

A robust, automated Payroll Management and MIS Dashboard built with **Python** and **Streamlit**. This system integrates directly with **Google Sheets** to provide real-time salary insights, attendance tracking, and automated PDF payslip generation.

## Key Features
* **Admin Dashboard:** Payroll statistics, department-wise payout visualizations, and employee productivity tracking using Plotly.
* **Employee Portal:** Secure login for staff to view their specific attendance performance and salary breakdowns.
* **PDF Generation:** One-click download for professional payslips featuring Indian Number-to-Words conversion.
* **Live Data Sync:** Reduced cache TTL and a manual sync button to ensure data is always up-to-date with Google Sheets.

## Tech Stack
* **Frontend:** Streamlit
* **Data Handling:** Pandas & NumPy
* **Visualization:** Plotly Express
* **PDF Engine:** FPDF
* **Database:** Google Sheets (via CSV API)

## 📁 Project Assets
* `payroll_app.py`: Main application code.
* `requirements.txt`: Necessary Python libraries.
* `nav-logo-BrPcRVjp.png`: Required branding asset for the UI header.

## 💻 How to Run Locally
1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt