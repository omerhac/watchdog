import streamlit as st
import json
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import pandas as pd  # For handling dataframes

ATTENDANCE_FILE = 'attendance.json'
STUDENTS = ["Alice", "Bob", "Charlie", "David", "Eve"]
ADMIN_EMAILS = ["admin@example.com"]

def load_attendance():
    try:
        with open(ATTENDANCE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_attendance(data):
    with open(ATTENDANCE_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def check_anomalies(data):
    anomalies = []
    one_week_ago = datetime.now() - timedelta(weeks=1)
    for student in STUDENTS:
        absences = sum(
            1 for date, names in data.items()
            if student not in names and datetime.strptime(date, '%Y-%m-%d') >= one_week_ago
        )
        if absences >= 5:
            anomalies.append(f"{student} has missed {absences} classes this week.")
    return anomalies

def send_email(anomalies):
    if not anomalies:
        return
    msg = MIMEText("\n".join(anomalies))
    msg['Subject'] = 'Attendance Anomalies Detected'
    msg['From'] = 'noreply@example.com'
    msg['To'] = ", ".join(ADMIN_EMAILS)

    with smtplib.SMTP('smtp.example.com', 587) as server:
        server.starttls()
        server.login('your_email@example.com', 'password')
        server.send_message(msg)

st.title("📚 Watchdog Tzora Attendance App")

# Define 'today' before it's used
today = datetime.now().strftime('%Y-%m-%d')

# Create tabs for different functionalities
tab1, tab2 = st.tabs(["✅ Mark Attendance", "📊 View Attendance"])

with tab1:
    st.header(f"Date: {today}")

    # Initialize present_students in session state
    if 'present_students' not in st.session_state:
        st.session_state.present_students = []

    st.subheader("Select Present Students:")

    # Display student buttons in a grid layout
    cols = st.columns(3)  # Adjust the number of columns as needed
    for idx, student in enumerate(STUDENTS):
        col = cols[idx % 3]
        if col.button(student, key=f"button_{student}"):
            if student not in st.session_state.present_students:
                st.session_state.present_students.append(student)
            else:
                st.session_state.present_students.remove(student)

    st.markdown("### Selected Students:")
    for student in st.session_state.present_students:
        st.markdown(f"✅ **{student} Present**")

    st.markdown("---")

    # Layout the Send button to stand out
    send_col1, send_col2, send_col3 = st.columns([1, 2, 1])  # Center the button
    with send_col2:
        send_button = st.button("🚀 Send Attendance", key="send_button")

    if send_button:
        attendance = load_attendance()
        attendance[today] = st.session_state.present_students
        save_attendance(attendance)
        anomalies = check_anomalies(attendance)
        send_email(anomalies)
        st.success("✅ Attendance updated successfully!")

with tab2:
    st.header("📅 Attendance Records")
    attendance_data = load_attendance()

    if attendance_data:
        # Convert attendance data to a DataFrame for better display
        df = pd.DataFrame([
            {"Date": date, "Present Students": ", ".join(names)}
            for date, names in attendance_data.items()
        ])

        # Enhance table appearance
        st.table(df.style.set_properties(**{
            'text-align': 'left',
            'background-color': '#f9f9f9',
            'padding': '10px',
            'border': '1px solid #ddd'
        }))
    else:
        st.info("No attendance records available yet.")