import os
import csv
import random
import bcrypt
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from app.session_manager import active_sessions
from flask import Blueprint, request, render_template, redirect, url_for, flash, session

def send_email(recipient_email, confirmation_code):
    sender_address = "warishaisl2003@gmail.com" #change this to relevant email
    password = os.getenv("GMAIL_PASSWORD")
    message = f"Your confirmation code is: {confirmation_code}"
    msg = MIMEText(message)
    msg["Subject"] = "UoB Student Council Elections - Confirm Your Email"
    msg["From"] = sender_address
    msg["To"] = recipient_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_address, password)
            server.sendmail(sender_address, recipient_email, msg.as_string())
    except Exception as e:
        print("Error sending email:", e)


register_bp = Blueprint('register', __name__)

@register_bp.route('/', methods=['GET', 'POST'])
def register():
    #if 'user' in session and session.get('session_id') == active_sessions.get(session['user']):
    #    return redirect(url_for('vote.vote'))
    
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']

        # if not email.endswith("@bolton.ac.uk"):
        #     flash("Email must end with '@bolton.ac.uk'")
        #     return redirect(url_for('register.register'))
    
        with open('voters.csv', mode='r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                if row['username'] == username:
                    flash("Username already registered. Please log in.")
                    return redirect(url_for('register.register'))
                if row['email'] == email:
                    flash("Email already registered. Please log in.")
                    return redirect(url_for('register.register'))

        student_name = None
        with open('student_data.csv', mode='r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                if row['username'] == username:
                    student_name = row['name']
                    break

        if not student_name:
            return "Username not found in student records."
        
        session['student_name'] = student_name 

        password = request.form['password'].encode('utf-8')
        hashed_pass = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

        confirmation_code = random.randint(1000, 9999)
        session['confirmation_code'] = confirmation_code
        session['confirmation_expiration'] = (datetime.now() + timedelta(hours=1)).isoformat()
        session['resend_time'] = (datetime.now() + timedelta(minutes=2)).isoformat()

        with open('voters.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([username, email, hashed_pass, False, False])  
            session['user'] = username
            session['email'] = email

            send_email(email, confirmation_code)
            return redirect(url_for('auth.authenticate'))
    
    return render_template('register.html')
