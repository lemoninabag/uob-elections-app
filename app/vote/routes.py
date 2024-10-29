import csv
from app.session_manager import active_sessions
from flask import Blueprint, render_template, request, session, redirect, url_for, flash

vote_bp = Blueprint('vote', __name__)

positions = ['President', 'Vice President', 'Secretary', 'Treasurer', 'Events & Cultural Coordinator', 
            'Media Coordinator', 'Pearson Representative', 'Bolton Representative', 
            'Northwood Representative', 'ATHE Representative', 'Career Services Coordinator', 
            'Sports Coordinator']

@vote_bp.route('/', methods = ['GET', 'POST'])
def vote():
    if 'user' not in session or session.get('session_id') != active_sessions.get(session['user']):
        return redirect(url_for('auth.login'))
    
    username = session['user']
    student_name = session.get('student_name')
    has_voted = False

    with open('voters.csv', 'r') as voters_file:
        reader = csv.DictReader(voters_file)
        for row in reader:
            if row['username'] == username:
                is_verified = row.get('is_verified') == 'True'
                has_voted = row.get('is_voted') == 'True'
                break
    if not is_verified:
        return redirect(url_for('auth.authenticate'))


    with open('voters.csv', 'r') as voters_file:
        reader = csv.DictReader(voters_file)
        for row in reader:
            if row['username'] == username and row.get('is_voted') == 'True':
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

        return redirect(url_for('vote.confirmation'))

    return render_template('vote.html', positions = positions, candidates = candidates, student_name = student_name)


@vote_bp.route('/confirmation', methods = ['GET', 'POST'])
def confirmation():
    if 'user' not in session or session.get('session_id') != active_sessions.get(session['user']):
        session.clear()
        flash("Session invalid or expired. Please log in again.", "error")
        return redirect(url_for('auth.login'))

    votes = session.get('votes', {})

    if len(votes) != len(positions):
        return f"You must vote for all positions before submitting. (Voted for {votes} out of {len(positions)})"

    if request.method == 'POST':
        update_nominee_votes(votes)
        update_isVoted(session['user'])
        session.pop('votes', None)
        session.pop('user', None)

        return "Vote successfully submitted!"
    
    return render_template('confirmation.html', votes = votes)

@vote_bp.route('/results')
def results():
    nominees_by_position = {}

    with open('nominees.csv', mode = 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            position = row['position']
            name = row['nominee']
            votes = int(row['votes'])

            if position not in nominees_by_position:
                nominees_by_position[position] = []

            nominees_by_position[position].append({'name': name, 'votes': votes})

    winners = {}
    for position, nominees in nominees_by_position.items():
        sorted_nominees = sorted(nominees, key = lambda x: x['votes'], reverse = True)
        winners[position] = sorted_nominees[0]  

    return render_template('results.html', winners = winners, nominees_by_position = nominees_by_position)

def update_nominee_votes(votes):
    nominees = []
    with open('nominees.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            nominee_name = row['nominee']
            if nominee_name in votes.values():
                row['votes'] = int(row.get('votes', 0)) + 1 
            nominees.append(row)

    with open('nominees.csv', 'w', newline = '') as file:
        fieldnames = ['position', 'nominee', 'votes']
        writer = csv.DictWriter(file, fieldnames = fieldnames)
        writer.writeheader()
        writer.writerows(nominees)

def update_isVoted(username):
    users = []
    with open('voters.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['username'] == username:
                row['is_voted'] = 'True'
            users.append(row)

    with open('voters.csv', 'w', newline = '') as file:
        fieldnames = ['username', 'email', 'password', 'is_verified', 'is_voted']
        writer = csv.DictWriter(file, fieldnames = fieldnames)
        writer.writeheader()
        writer.writerows(users)