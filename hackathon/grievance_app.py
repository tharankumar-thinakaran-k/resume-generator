# grievance_app.py

import streamlit as st
import pandas as pd
import uuid
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import matplotlib.pyplot as plt
from io import BytesIO
from fpdf import FPDF
import base64
import os
import requests  # For n8n webhook

# === CONFIGURATION ===
CSV_FILE = "grievance_data.csv"
SPOC_FILE = "spocs.csv"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = st.secrets["email"]["smtp_email"]
SMTP_PASSWORD = st.secrets["email"]["smtp_password"]

ADMIN_CREDENTIALS = st.secrets["admins"]
ADMIN_ROLES = {
    "admin": "editor",
    "viewer": "viewer"
}

N8N_WEBHOOK_URL = "https://tharan.app.n8n.cloud/webhook-test/grievance"

# === SESSION STATE INIT ===
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "admin_user" not in st.session_state:
    st.session_state.admin_user = None
if "admin_role" not in st.session_state:
    st.session_state.admin_role = None

# === FUNCTIONS ===
def load_data():
    try:
        return pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            "Timestamp", "Student College", "Student Register Number", "Name", "Student Email",
            "Contact Number", "Type", "Complaint", "Grievance ID", "SPOC Name", "SPOC Email",
            "Status", "Deadline", "Image Path"
        ])

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
        st.success(f"Email sent to {to_email}")
    except Exception as e:
        st.error(f"Failed to send email: {e}")

def notify_n8n_workflow(payload):
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            st.toast("n8n workflow notified successfully.")
        else:
            st.warning(f"n8n notification failed: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Failed to notify n8n workflow: {e}")

def generate_grievance_id():
    return f"G-{str(uuid.uuid4())[:8].upper()}"

def generate_pdf_report(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Grievance Consolidated Report", ln=True, align='C')

    status_counts = df['Status'].value_counts().to_dict()
    for k, v in status_counts.items():
        pdf.cell(200, 10, txt=f"{k}: {v}", ln=True)

    fig, ax = plt.subplots()
    ax.pie(status_counts.values(), labels=status_counts.keys(), autopct='%1.1f%%')
    ax.axis('equal')
    img_buf = BytesIO()
    plt.savefig(img_buf, format='png')
    img_buf.seek(0)

    image_path = "temp_chart.png"
    with open(image_path, "wb") as f:
        f.write(img_buf.read())
    pdf.image(image_path, x=10, y=None, w=180)

    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Filtered Grievance Details", ln=True, align='C')

    columns = df.columns.tolist()
    column_widths = [25] * len(columns)
    row_height = 7

    pdf.set_fill_color(200, 220, 255)
    for i, col in enumerate(columns):
        pdf.cell(column_widths[i], row_height, col[:15], border=1, fill=True)
    pdf.ln(row_height)

    for _, row in df.iterrows():
        for i, col in enumerate(columns):
            text = str(row[col])[:30].replace('\n', ' ')
            pdf.cell(column_widths[i], row_height, text, border=1)
        pdf.ln(row_height)

    pdf_output = pdf.output(dest='S').encode('latin1')
    return BytesIO(pdf_output)

def load_spocs():
    try:
        df = pd.read_csv(SPOC_FILE)
        df.columns = ["SPOC Name", "SPOC Email"]
        return df
    except:
        return pd.DataFrame(columns=["SPOC Name", "SPOC Email"])

def save_spocs(df):
    df.to_csv(SPOC_FILE, index=False)

# === COMPONENTS ===
def admin_login():
    st.title("🔐 Admin Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login = st.form_submit_button("Login")
        if login:
            if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password:
                st.session_state.admin_logged_in = True
                st.session_state.admin_user = username
                st.session_state.admin_role = ADMIN_ROLES.get(username, "viewer")
                st.success(f"Welcome, {username}!")
                st.experimental_rerun()
            else:
                st.error("Invalid credentials.")

def logout_button():
    if st.session_state.admin_logged_in:
        if st.button("🔓 Logout"):
            st.session_state.admin_logged_in = False
            st.session_state.admin_user = None
            st.session_state.admin_role = None
            st.success("Logged out successfully.")
            st.experimental_rerun()

def grievance_form():
    st.title("🎓 Student Grievance Submission")
    with st.form("grievance_form"):
        college = st.text_input("Student College")
        reg_no = st.text_input("Student Register Number")
        name = st.text_input("Name")
        email = st.text_input("Student Email")
        contact = st.text_input("Contact Number")
        g_type = st.selectbox("Type", ["Academic", "Infrastructure", "Administration", "Others"])
        complaint = st.text_area("Complaint (detailed description)", height=200)
        uploaded_file = st.file_uploader("Upload Image (optional)", type=["png", "jpg", "jpeg"])
        submit = st.form_submit_button("Submit")

        if submit:
            grievance_id = generate_grievance_id()
            spocs = load_spocs()
            if not spocs.empty:
                spoc_row = spocs.sample(1).iloc[0]
                spoc_name, spoc_email = spoc_row['SPOC Name'], spoc_row['SPOC Email']
            else:
                spoc_name = "Default SPOC"
                spoc_email = SMTP_EMAIL

            status = "Open"
            deadline = datetime.today().strftime("%Y-%m-%d")
            image_path = ""
            if uploaded_file:
                image_path = f"images/{grievance_id}_image.png"
                os.makedirs("images", exist_ok=True)
                with open(image_path, "wb") as f:
                    f.write(uploaded_file.read())

            new_entry = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Student College": college,
                "Student Register Number": reg_no,
                "Name": name,
                "Student Email": email,
                "Contact Number": contact,
                "Type": g_type,
                "Complaint": complaint,
                "Grievance ID": grievance_id,
                "SPOC Name": spoc_name,
                "SPOC Email": spoc_email,
                "Status": status,
                "Deadline": deadline,
                "Image Path": image_path
            }
            df = load_data()
            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
            save_data(df)
            send_email(spoc_email, f"[New Grievance Assigned] ID: {grievance_id}", complaint)
            notify_n8n_workflow({
                "grievance_id": grievance_id,
                "student_name": name,
                "student_email": email,
                "type": g_type,
                "complaint": complaint,
                "spoc_email": spoc_email,
                "timestamp": datetime.now().isoformat()
            })
            st.success(f"Grievance submitted successfully! Your Grievance ID is {grievance_id}")

def spoc_management_page():
    st.title("👤 SPOC Management")

    spoc_df = load_spocs()
    st.dataframe(spoc_df, use_container_width=True)

    st.markdown("### ➕ Add New SPOC")
    new_name = st.text_input("SPOC Name")
    new_email = st.text_input("SPOC Email")
    if st.button("Add SPOC"):
        if new_name and new_email:
            new_row = pd.DataFrame([[new_name, new_email]], columns=["SPOC Name", "SPOC Email"])
            spoc_df = pd.concat([spoc_df, new_row], ignore_index=True)
            save_spocs(spoc_df)
            st.success("SPOC added successfully.")
            st.experimental_rerun()
        else:
            st.warning("Please enter both name and email.")

    st.markdown("### ❌ Delete SPOC")
    selected_index = st.selectbox("Select SPOC to Delete", spoc_df.index)
    selected_spoc = spoc_df.loc[selected_index]

    if st.checkbox("I confirm to delete this SPOC"):
        if st.button("Delete SPOC"):
            spoc_df = spoc_df.drop(index=selected_index).reset_index(drop=True)
            save_spocs(spoc_df)
            st.success("SPOC deleted.")
            st.experimental_rerun()

def admin_panel():
    if not st.session_state.admin_logged_in:
        admin_login()
        return

    st.sidebar.success(f"Logged in as {st.session_state.admin_user} ({st.session_state.admin_role})")
    logout_button()

    tab = st.sidebar.radio("Select Admin View", ["📊 Dashboard", "👤 SPOC Management"])

    if tab == "📊 Dashboard":
        df = load_data()
        st.header("📊 Admin Dashboard")

        st.subheader("🗂️ Generate Filtered PDF Report")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("From Date", value=pd.to_datetime(df["Timestamp"]).min().date())
        with col2:
            end_date = st.date_input("To Date", value=pd.to_datetime(df["Timestamp"]).max().date())

        grievance_types = ["All"] + sorted(df["Type"].unique())
        selected_type = st.selectbox("Filter by Type", grievance_types)

        spocs = ["All"] + sorted(df["SPOC Name"].unique())
        selected_spoc = st.selectbox("Filter by SPOC", spocs)

        filtered_df = df.copy()
        filtered_df["Timestamp"] = pd.to_datetime(filtered_df["Timestamp"])
        filtered_df = filtered_df[
            (filtered_df["Timestamp"].dt.date >= start_date) &
            (filtered_df["Timestamp"].dt.date <= end_date)
        ]

        if selected_type != "All":
            filtered_df = filtered_df[filtered_df["Type"] == selected_type]
        if selected_spoc != "All":
            filtered_df = filtered_df[filtered_df["SPOC Name"] == selected_spoc]

        st.dataframe(filtered_df)

        if not filtered_df.empty:
            st.download_button("📄 Download Filtered PDF Report",
                            generate_pdf_report(filtered_df),
                            file_name="filtered_grievance_report.pdf")
        else:
            st.warning("No data available for the selected filters.")

        st.metric("Total Grievances", len(df))
        st.metric("Open Grievances", (df['Status'] == "Open").sum())
        st.metric("Closed Grievances", (df['Status'] == "Closed").sum())

        st.subheader("📈 Status Distribution")
        status_counts = df['Status'].value_counts()
        fig, ax = plt.subplots()
        ax.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        st.pyplot(fig)

        st.subheader("📋 All Grievances")
        st.dataframe(df)
        st.download_button("📄 Download PDF Report", generate_pdf_report(df), file_name="grievance_report.pdf")

        if st.session_state.admin_role == "editor":
            st.subheader("📧 Send Email to SPOC")
            grievance_id = st.text_input("Enter Grievance ID")
            if st.button("Send Mail"):
                row = df[df["Grievance ID"] == grievance_id]
                if not row.empty:
                    send_email(row.iloc[0]["SPOC Email"], f"Reminder: Grievance {grievance_id}", row.iloc[0]["Complaint"])

    elif tab == "👤 SPOC Management":
        spoc_management_page()

# === MAIN ===
def main():
    st.sidebar.title("📂 Navigation")
    choice = st.sidebar.radio("Go to", ["Submit Grievance", "Admin Panel"])
    if choice == "Submit Grievance":
        grievance_form()
    elif choice == "Admin Panel":
        admin_panel()

if __name__ == "__main__":
    main()

# You can keep the rest of your app code unchanged here (spoc_management_page, admin_panel, main...)
# For brevity, those are omitted in this preview.
