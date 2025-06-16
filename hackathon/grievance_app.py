
import streamlit as st
import pandas as pd
import uuid
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# === CONFIGURATION ===
CSV_FILE = "grievance_data.csv"

# Static Admin Credentials
ADMIN_CREDENTIALS = {
    "admin": "admin@123",
    "tharan": "tharan@123"
}

# Email configuration (uses Streamlit secrets or static)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = st.secrets["email"]["smtp_email"]
SMTP_PASSWORD = st.secrets["email"]["smtp_password"]

# === FUNCTIONS ===
def load_data():
    try:
        return pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            "Timestamp", "Student College", "Student Register Number", "Name", "Student Email",
            "Contact Number", "Type", "Complaint", "Grievance ID",
            "SPOC Name", "SPOC Email", "Status", "Deadline"
        ])

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

def send_email(to_email, grievance_id, spoc_name, complaint):
    subject = f"[New Grievance Assigned] ID: {grievance_id}"
    body = f"""
Dear {spoc_name},

You have been assigned a new grievance.

Grievance ID: {grievance_id}
Complaint Summary: {complaint}

Please take necessary action.

Regards,
Grievance Cell System
"""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
        st.success(f"Notification email sent to {spoc_name} ({to_email})")
    except Exception as e:
        st.error(f"Failed to send email: {e}")

def generate_grievance_id():
    return f"G-{str(uuid.uuid4())[:8].upper()}"

# === MAIN PAGE ===
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
        submit = st.form_submit_button("Submit")

        if submit:
            grievance_id = generate_grievance_id()
            spoc_name = "Dr. A. Kumar"
            spoc_email = "spoc@example.com"
            status = "Open"
            deadline = datetime.today().strftime("%Y-%m-%d")

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
                "Deadline": deadline
            }

            df = load_data()
            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
            save_data(df)

            send_email(spoc_email, grievance_id, spoc_name, complaint)
            st.success(f"Grievance submitted successfully! Your Grievance ID is {grievance_id}")

# === ADMIN PANEL ===
def admin_panel():
    st.subheader("🔐 Admin Login")

    if "admin_logged_in" not in st.session_state:
        st.session_state["admin_logged_in"] = False

    if not st.session_state["admin_logged_in"]:
        with st.form("admin_login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login")

            if login_btn:
                if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password:
                    st.success("Login successful!")
                    st.session_state["admin_logged_in"] = True
                    st.rerun()
                else:
                    st.error("Invalid credentials!")

    if st.session_state["admin_logged_in"]:
        st.success("✅ Logged in as admin")
        if st.button("Logout"):
            st.session_state["admin_logged_in"] = False
            st.rerun()

        st.header("📋 Grievance Dashboard")
        df = load_data()
        st.dataframe(df)

        # Filter and update section
        st.markdown("### 🔎 Filter/Search")
        with st.expander("Filter Options"):
            search_email = st.text_input("Search by Student Email")
            filter_type = st.selectbox("Filter by Type", ["All"] + df["Type"].unique().tolist())
            filter_date = st.date_input("Filter by Date", value=None)

            if search_email:
                df = df[df["Student Email"].str.contains(search_email, case=False)]
            if filter_type != "All":
                df = df[df["Type"] == filter_type]
            if filter_date:
                df = df[df["Timestamp"].str.startswith(str(filter_date))]

            st.dataframe(df)

        st.markdown("### 🛠 Update Grievance Status")
        grievance_ids = df["Grievance ID"].tolist()
        selected_id = st.selectbox("Select Grievance ID to Update", grievance_ids)
        new_status = st.selectbox("New Status", ["Open", "In Progress", "Resolved"])
        new_deadline = st.date_input("New Deadline")

        if st.button("Update Status"):
            df.loc[df["Grievance ID"] == selected_id, "Status"] = new_status
            df.loc[df["Grievance ID"] == selected_id, "Deadline"] = str(new_deadline)
            save_data(df)
            st.success("Status updated successfully!")

# === APP ROUTING ===
st.sidebar.title("Navigation")
choice = st.sidebar.radio("Go to", ["Submit Grievance", "Admin Panel"])

if choice == "Submit Grievance":
    grievance_form()
elif choice == "Admin Panel":
    admin_panel()
