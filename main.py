import streamlit as st
import json
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import pandas as pd  # For handling dataframes
from streamlit.components.v1 import html
from pymongo import MongoClient
import os

# MongoDB Atlas connection
assert 'MONGO_URI' in os.environ, "MONGO_URI environment variable is not set"
MONGO_URI = os.environ.get('MONGO_URI')
COLLECTION_NAME = os.environ.get('COLLECTION_NAME', 'tichon')
client = MongoClient(MONGO_URI)
db = client['watchdog']
collection = db[COLLECTION_NAME]

# Read students from file
def load_students():
    with open('students.txt', 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

STUDENTS = load_students()
ADMIN_EMAILS = ["admin@example.com"]

def load_attendance():
    return list(collection.find({}, {'_id': 0}))

def save_attendance(data):
    existing_record = collection.find_one({'date': data['date']})
    if existing_record:
        collection.update_one({'date': data['date']}, {'$set': {'present': data['present']}})
    else:
        collection.insert_one(data)

def check_anomalies(data):
    anomalies = []
    one_week_ago = datetime.now() - timedelta(weeks=1)
    for student in STUDENTS:
        absences = sum(
            1 for record in data
            if student not in record['present'] and datetime.strptime(record['date'], '%Y-%m-%d') >= one_week_ago
        )
        if absences >= 5:
            anomalies.append(f"{student} חסר/חסרה {absences} שיעורים השבוע.")
    return anomalies

def send_email(anomalies):
    if not anomalies:
        return
    msg = MIMEText("\n".join(anomalies), 'plain', 'utf-8')
    msg['Subject'] = 'נמצאו חריגות בנוכחות'
    msg['From'] = 'noreply@example.com'
    msg['To'] = ", ".join(ADMIN_EMAILS)

    with smtplib.SMTP('smtp.example.com', 587) as server:
        server.starttls()
        server.login('your_email@example.com', 'password')
        server.send_message(msg)

# Set the page direction to Right-to-Left (RTL) for Hebrew
st.markdown(
    """
    <style>
    /* Set the entire app to RTL */
    [data-testid="stAppViewContainer"] {
        direction: rtl;
        text-align: right;
    }
    /* Align text in tables to the right */
    table {
        direction: rtl;
        text-align: right;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("אפליקציית נוכחות צרעה 📚")

# Define 'today' before it's used
today = datetime.now().strftime('%Y-%m-%d')

# Create tabs for different functionalities
tab1, tab2 = st.tabs(["✅ רישום נוכחות", "📊 צפייה בנוכחות"])

with tab1:
    st.header(f"תאריך: {today}")

    # Initialize present_students in session state
    if 'present_students' not in st.session_state:
        st.session_state.present_students = []

    st.subheader("בחר תלמידים נוכחים:")

    # Display student buttons in a grid layout
    cols = st.columns(3)  # Adjust the number of columns as needed
    for idx, student in enumerate(STUDENTS):
        col = cols[idx % 3]
        if col.button(student, key=f"button_{student}"):
            if student not in st.session_state.present_students:
                st.session_state.present_students.append(student)
            else:
                st.session_state.present_students.remove(student)

    st.markdown("### תלמידים נוכחים:")
    for student in st.session_state.present_students:
        st.markdown(f"✅ **{student} נוכח/ת**")

    st.markdown("---")

    # Layout the Send button to stand out
    send_col1, send_col2, send_col3 = st.columns([1, 2, 1])  # Center the button
    with send_col2:
        send_button = st.button("🚀 שלח נוכחות", key="send_button")

    if send_button:
        attendance_record = {
            'date': today,
            'present': st.session_state.present_students
        }
        save_attendance(attendance_record)
        attendance = load_attendance()
        # anomalies = check_anomalies(attendance)
        # send_email(anomalies)
        st.success("✅ הנוכחות עודכנה בהצלחה!")

with tab2:
    st.header("📅 רשומות נוכחות")
    attendance_data = load_attendance()

    if attendance_data:
        # Convert attendance data to a DataFrame for better display
        df = pd.DataFrame([
            {"תאריך": record['date'], "תלמידים נוכחים": ", ".join(record['present'])}
            for record in attendance_data
        ])

        # Get the primary color from Streamlit's theme
        primary_color = st.get_option("theme.primaryColor")

        # Style the DataFrame
        styled_df = df.style.set_properties(**{
            'text-align': 'right',
            'background-color': '#f9f9f9',
            'padding': '10px',
            'border': '1px solid #ddd'
        }).set_table_styles([
            {'selector': 'th', 'props': [
                ('background-color', primary_color),
                ('color', 'white'),
                ('font-weight', 'bold'),
                ('text-align', 'right'),
                ('padding', '10px')
            ]}
        ])

        # Convert styled DataFrame to HTML
        table_html = styled_df.to_html(index=False)

        # Wrap the table in a div with RTL direction
        rtl_table_html = f'<div dir="rtl">{table_html}</div>'

        # Display the styled table
        html(rtl_table_html, height=400, scrolling=True)
    else:
        st.info("אין כרגע רשומות נוכחות.")