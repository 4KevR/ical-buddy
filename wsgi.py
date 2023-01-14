from flask import url_for

from app import app

if __name__ == "__main__":
    app.run(host="ical-buddy", port=5000)
    with app.app_context():
        app.add_url_rule('/favicon.ico', redirect_to=url_for('static', filename='favicon.ico'))