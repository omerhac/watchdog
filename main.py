import gradio as gr
import json
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import pandas as pd
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os

assert 'MONGO_USERNAME' in os.environ, "MONGO_USERNAME environment variable is not set"
assert 'MONGO_PASS' in os.environ, "MONGO_PASS environment variable is not set"
MONGO_USERNAME = os.environ.get('MONGO_USERNAME')
MONGO_PASS = os.environ.get('MONGO_PASS')
MONGO_URI = f'mongodb+srv://{MONGO_USERNAME}:{MONGO_PASS}@pixel-brain.vzvdnha.mongodb.net/?retryWrites=true&w=majority&appName=Pixel-Brain'
COLLECTION_NAME = os.environ.get('COLLECTION_NAME', 'tichon')
client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
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

def register_attendance(selected_students):
    today = datetime.now().strftime('%Y-%m-%d')
    attendance_record = {
        'date': today,
        'present': selected_students
    }
    save_attendance(attendance_record)
    attendance = load_attendance()
    # anomalies = check_anomalies(attendance)
    # send_email(anomalies)
    return "✅ הנוכחות עודכנה בהצלחה!"

def view_attendance():
    attendance_data = load_attendance()
    if attendance_data:
        df = pd.DataFrame([
            {"תאריך": record['date'], "תלמידים נוכחים": ", ".join(record['present'])}
            for record in attendance_data
        ])
        return df.to_html(index=False)
    else:
        return "אין כרגע רשומות נוכחות."

def create_app():
    with gr.Blocks(theme=gr.themes.Default()) as app:
        gr.Markdown("# אפליקציית נוכחות צרעה 📚")
        
        with gr.Tab("✅ רישום נוכחות"):
            gr.Markdown(f"## תאריך: {datetime.now().strftime('%Y-%m-%d')}")
            gr.Markdown("### בחר תלמידים נוכחים:")
            checkboxes = [gr.Checkbox(label=student) for student in STUDENTS]
            submit_btn = gr.Button("🚀 שלח נוכחות")
            result = gr.Markdown()
            
            submit_btn.click(
                fn=lambda *args: register_attendance([STUDENTS[i] for i, arg in enumerate(args) if arg]),
                inputs=checkboxes,
                outputs=result
            )
        
        with gr.Tab("📊 צפייה בנוכחות"):
            gr.Markdown("## 📅 רשומות נוכחות")
            attendance_table = gr.HTML()
            refresh_btn = gr.Button("רענן נתונים")
            
            refresh_btn.click(fn=view_attendance, outputs=attendance_table)
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.launch()