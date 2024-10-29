import os
import csv
import random
import smtplib
import bcrypt
from flask import Flask, render_template, request, redirect, session, url_for, flash
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import re
from dotenv import load_dotenv
import bcrypt

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with your actual secret key


load_dotenv()


app = Flask(__name__)
app.secret_key = 'secret_key'

def send_email(recipient_email, confirmation_code):
    sender_address = "warishaisl2003@gmail.com"
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


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']

        if not email.endswith("@bolton.ac.uk"):
            flash("Email must end with '@bolton.ac.uk'")
            return redirect(url_for('register'))
    
        with open('voters.csv', mode='r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                if row['username'] == username:
                    flash("Username already registered. Please log in.")
                    return redirect(url_for('register'))
                if row['email'] == email:
                    flash("Email already registered. Please log in.")
                    return redirect(url_for('register'))

        # Verify student data and get student name from student_data.csv
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

        # Hash the password
        password = request.form['password'].encode('utf-8')
        hashed_pass = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

        # Generate a confirmation code and store in the session with an expiration time
        confirmation_code = random.randint(1000, 9999)
        session['confirmation_code'] = confirmation_code
        session['confirmation_expiration'] = (datetime.now() + timedelta(hours=1)).isoformat()
        session['resend_time'] = (datetime.now() + timedelta(minutes=2)).isoformat()

        # Store data in voters.csv
        with open('voters.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([username, email, hashed_pass, False, False])  # Assuming is_verified = False initially
            session['user'] = username
            session['email'] = email

            send_email(email, confirmation_code)
            return redirect(url_for('authenticate'))
    
    return render_template('register.html')


@app.route('/authenticate', methods=['GET', 'POST'])
def authenticate():
    if request.method == 'POST':
        code_input = request.form['confirmation_code']

        # Ensure the expiration time is retrieved correctly
        expiration = session.get('confirmation_expiration')
        if expiration:
            expiration = datetime.fromisoformat(expiration)
        else:
            flash("Confirmation code expired. Please request a new one.")
            return redirect(url_for('authenticate'))

        # Check if confirmation code expired
        if datetime.now() > expiration:
            flash("Confirmation code has expired. Please request a new one.")
            return redirect(url_for('authenticate'))

        # Compare the input code with the stored confirmation code
        if int(code_input) == session.get('confirmation_code'):
            session['verified'] = True
            update_verification_status(session['user'])
            return redirect(url_for('login'))

        flash("Incorrect code. Please try again.")
        return redirect(url_for('authenticate'))

    # Show the page if GET request
    return render_template('authenticate.html')


@app.route('/resend_code', methods=['POST'])
def resend_code():
    # Retrieve the next possible resend time and check for validity
    next_resend_time = session.get('resend_time')
    if next_resend_time:
        next_resend_time = datetime.fromisoformat(next_resend_time)

    # Ensure enough time has passed since last resend
    if next_resend_time and datetime.now() < next_resend_time:
        flash("You must wait 2 minutes before resending the code.")
        return redirect(url_for('authenticate'))

    # Generate a new confirmation code and update expiration and resend times
    confirmation_code = random.randint(1000, 9999)
    session['confirmation_code'] = confirmation_code
    session['confirmation_expiration'] = (datetime.now() + timedelta(hours=1)).isoformat()
    session['resend_time'] = (datetime.now() + timedelta(minutes=2)).isoformat()

    # Send the new code
    send_email(session['email'], confirmation_code)
    flash("A new confirmation code has been sent to your email.")

    return redirect(url_for('authenticate'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')

        with open('voters.csv', mode='r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                if row['username'] == username:
                    stored_password = row['password']
                    
                    # Check if the stored password matches the entered password
                    if bcrypt.checkpw(password, stored_password.encode('utf-8')):
                        # Check if the user is verified
                        if row.get('is_verified') != 'True':
                            return "Your account is not verified. Please verify your account to proceed."

                        session['user'] = username
                        session['verified'] = True
                        
                        # Check if the user has already voted
                        if row.get('is_voted') == 'True':
                            return "You have already voted."

                        return redirect(url_for('vote'))

        # If no matching username or password was found
        return "Invalid username or password."

    return render_template('login.html')



@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        
        with open('voters.csv', 'r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                if row['username'] == username:
                    email = row['email']
                    
                    recovery_code = str(random.randint(100000, 999999))
                    session['recovery_code'] = recovery_code
                    session['username'] = username 

                    masked_email = re.sub(r'(?<=.{1}).(?=.*@)', '*', email)
                    session['masked_email'] = masked_email
                    send_email(email, recovery_code)
                    
                    return redirect(url_for('verify_email'))
                    
        flash("Username not found. Please try again.")
        return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form['new_password'].encode('utf-8')
        hashed_password = bcrypt.hashpw(new_password, bcrypt.gensalt()).decode('utf-8')
        
        updated_rows = []
        with open('voters.csv', 'r') as file:
            csv_reader = csv.DictReader(file)
            fieldnames = csv_reader.fieldnames
            for row in csv_reader:
                if row['username'] == session['username']:
                    row['password'] = hashed_password
                updated_rows.append(row)

        with open('voters.csv', 'w', newline='') as file:
            csv_writer = csv.DictWriter(file, fieldnames=fieldnames)
            csv_writer.writeheader()
            csv_writer.writerows(updated_rows)

        session.pop('recovery_code', None)
        session.pop('username', None)


        return redirect(url_for('login'))

    return render_template('reset_password.html')



positions = ['President', 'Vice President', 'Secretary', 'Treasurer', 'Events & Cultural Coordinator', 'Media Coordinator', 
            'Pearson Representative', 'Bolton Representative', 'Northwood Representative', 'ATHE Representative', 
            'Career Services Coordinator', 'Sports Coordinator']


@app.route('/vote', methods=['GET', 'POST'])
def vote():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    student_name = session.get('student_name')

    has_voted = False
    with open('voters.csv', 'r') as voters_file:
        reader = csv.DictReader(voters_file)
        for row in reader:
            if row.get('is_voted') == 'True':
                has_voted = True
                break
    
    if has_voted:
        return "You have already voted. Thank you!"
    

    candidates = {}
    for position in positions:
        candidates[position] = []
        with open('nominees.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['position'] == position:
                    candidates[position].append(row['nominee'])

    if request.method == 'POST':
        votes = {}
        for position in positions:
            selected_candidate = request.form.get(position)
            votes[position] = selected_candidate
            print(f"Vote for {position} saved as {selected_candidate}.")

        session['votes'] = votes
        print(f"Votes submitted: {session['votes']}")

        return redirect(url_for('confirmation'))
    

    return render_template('vote.html', positions=positions, candidates=candidates, student_name=student_name)


@app.route('/confirmation', methods=['GET', 'POST'])
def confirmation():
    if 'user' not in session:
        return redirect(url_for('login'))

    votes = session.get('votes', {})

    if len(votes) != len(positions):
        return f"You must vote for all positions before submitting! (Voted for {votes} out of {len(positions)})"

    if request.method == 'POST':
        update_nominee_votes(votes)
        update_user_voting_status(session['user'])
        session.pop('votes', None)
        session.pop('user', None)

        return "Vote successfully submitted!"
    

    return render_template('confirmation.html', votes=votes)

@app.route('/verify_email', methods=['GET', 'POST'])
def verify_email():
    if request.method == 'POST':
        entered_code = request.form['recovery_code']

        if 'recovery_code' in session and entered_code == session['recovery_code']:
            # Code is correct, proceed to reset password
            return redirect(url_for('reset_password'))

        return "Invalid recovery code."

    return render_template('verify_email.html')

@app.route('/results')
def results():
    nominees_by_position = {}

    # Read nominees from CSV file
    with open('nominees.csv', mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            position = row['position']
            name = row['nominee']
            votes = int(row['votes'])

            # Initialize position entry if not already done
            if position not in nominees_by_position:
                nominees_by_position[position] = []

            # Add nominee data to the respective position list
            nominees_by_position[position].append({'name': name, 'votes': votes})

    # Determine the winner for each position
    winners = {}
    for position, nominees in nominees_by_position.items():
        # Sort nominees by votes in descending order
        sorted_nominees = sorted(nominees, key=lambda x: x['votes'], reverse=True)
        winners[position] = sorted_nominees[0]  # Winner is the nominee with the highest votes

    # Pass winners and full sorted data to the template
    return render_template('results.html', winners=winners, nominees_by_position=nominees_by_position)



def update_nominee_votes(votes):
    nominees = []
    with open('nominees.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            nominee_name = row['nominee']
            if nominee_name in votes.values():
                row['votes'] = int(row.get('votes', 0)) + 1 
            nominees.append(row)

    with open('nominees.csv', 'w', newline='') as file:
        fieldnames = ['position', 'nominee', 'votes']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(nominees)

def update_verification_status(username):
    users = []
    with open('voters.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['username'] == username:
                row['is_verified'] = 'True'  # Set is_verified to True
            users.append(row)

    with open('voters.csv', 'w', newline='') as file:
        fieldnames = ['username', 'email', 'password', 'is_verified', 'is_voted']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(users)



def update_user_voting_status(username):
    users = []
    with open('voters.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['username'] == username:
                row['is_voted'] = 'True'
            users.append(row)

    with open('voters.csv', 'w', newline='') as file:
        fieldnames = ['username', 'email', 'password', 'is_verified', 'is_voted']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(users)


if __name__ == '__main__':
    app.run(debug=True)