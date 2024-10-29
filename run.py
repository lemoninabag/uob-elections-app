from app import create_app
from flask import session
from app.session_manager import active_sessions

app = create_app()

active_sessions.clear()

if __name__ == '__main__':
    app.run(debug=True)