import io
import os
import requests
import re

from datetime import datetime, timedelta, timezone
from icalendar import Calendar

from flask import Flask, jsonify, send_file, request, render_template, make_response, redirect, url_for
from flask_migrate import Migrate
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager, get_jwt, \
    set_access_cookies, unset_jwt_cookies, current_user

from models import db, User, ICalProfile, FilterWord, OTPCode

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config["STATIC_FOLDER"] = "static"
app.config["TEMPLATES_FOLDER"] = "templates"

app.config["JWT_SECRET_KEY"] = os.environ["JWT_SECRET_KEY"]
app.config["JWT_COOKIE_SECURE"] = True if os.environ["JWT_COOKIE_SECURE"] == "True" else False
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db)

jwt = JWTManager(app)


def make_login(user_name, password):
    db_user = User.query.filter_by(user_name=user_name).first()
    if db_user:
        if db_user.check_password(password):
            response = make_response(redirect(url_for("home")))
            access_token = create_access_token(identity=db_user)
            set_access_cookies(response, access_token)
            return response
    return jsonify({"msg": "Login failed"}), 401


def validate_url(url):
    try:
        requests.get(url)
        return True
    except Exception:
        return False


def validate_token(token):
    if re.search("^[a-zA-Z0-9-._~]+$", token):
        return True
    return False


@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.user_id


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.filter_by(user_id=identity).first()


@jwt.expired_token_loader
@jwt.unauthorized_loader
def redirect_on_invalid_jwt(*args):
    return make_response(redirect(url_for("login")))


@app.after_request
def refresh_expiring_jwt(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=current_user)
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        return response


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json
    user_name = data["username"]
    password = data["password"]
    return make_login(user_name, password)


@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.json
    db_code = OTPCode.query.filter_by(code_value=data["otp"]).first()
    if getattr(db_code, 'code_used', True):
        return jsonify({"msg": "Invalid OTP"}), 406
    existing_user = User.query.filter_by(user_name=data["username"]).first()
    if existing_user:
        return jsonify({"msg": "Username exists"}), 406
    new_user = User(user_name=data["username"], is_admin=db_code.for_admin)
    new_user.set_password(data["password"])
    db.session.add(new_user)
    db_code.code_used = True
    db.session.commit()
    return make_login(data["username"], data["password"])


@app.route("/api/logout", methods=["POST"])
def api_logout():
    response = make_response(redirect(url_for("login")))
    unset_jwt_cookies(response)
    return response


@app.route("/api/changeProfile", methods=["POST"])
@jwt_required()
def api_change_profile():
    if not current_user:
        return jsonify({"msg": "Not authorized"}), 401
    profile_change_data = request.json
    profile_to_change = ICalProfile.query.filter_by(user_id=current_user.user_id,
                                                    profile_name=profile_change_data["profile_name_original"]).first()
    if not profile_to_change:
        return jsonify({"msg": "Invalid profile data"}), 406
    if "profile_name" in profile_change_data:
        profile_to_change.profile_name = profile_change_data["profile_name"]
    if "i_cal_url" in profile_change_data:
        if not validate_url(profile_change_data["i_cal_url"]):
            return jsonify({"msg": "Invalid url"}), 406
        profile_to_change.i_cal_url = profile_change_data["i_cal_url"]
    if "token" in profile_change_data:
        if not validate_token(profile_change_data["token"]):
            return jsonify({"msg": "Invalid token"}), 406
        profile_to_change.token = profile_change_data["token"]
    if "add_filter" in profile_change_data:
        existing_word = FilterWord.query.filter_by(content=profile_change_data["add_filter"],
                                                   profile_id=profile_to_change.profile_id).first()
        if not existing_word:
            new_filter = FilterWord(content=profile_change_data["add_filter"], profile_id=profile_to_change.profile_id)
            db.session.add(new_filter)
        else:
            return jsonify({"msg": "Word exists"}), 406
    if "remove_filter" in profile_change_data:
        requested_word = profile_change_data["remove_filter"]
        element_to_delete = [elem for elem in profile_to_change.words if elem.content == requested_word]
        if len(element_to_delete) >= 1:
            FilterWord.query.filter_by(word_id=element_to_delete[0].word_id).delete(synchronize_session=False)
    db.session.commit()
    return jsonify({"msg": "Change successful"}), 200


@app.route("/api/newProfile", methods=["POST"])
@jwt_required()
def api_new_profile():
    if not current_user:
        return jsonify({"msg": "Not authorized"}), 401
    new_profile_data = request.json
    if not new_profile_data.keys() >= {"new_profile_name", "new_token", "new_ical_url"}:
        return jsonify({"msg": "Invalid profile data"}), 406
    existing_profile = ICalProfile.query.filter_by(user_id=current_user.user_id,
                                                   profile_name=new_profile_data["new_profile_name"].strip()).first()
    if existing_profile:
        return jsonify({"msg": "Name exists"}), 406
    existing_token = ICalProfile.query.filter_by(token=new_profile_data["new_token"]).first()
    if existing_token:
        return jsonify({"msg": "Token exists"}), 406
    if not validate_url(new_profile_data["new_ical_url"]):
        return jsonify({"msg": "Invalid url"}), 406
    if not validate_token(new_profile_data["new_token"]):
        return jsonify({"msg": "Invalid token"}), 406
    new_profile_element = ICalProfile(profile_name=new_profile_data["new_profile_name"].strip(),
                                      i_cal_url=new_profile_data["new_ical_url"], token=new_profile_data["new_token"],
                                      user_id=current_user.user_id)
    db.session.add(new_profile_element)
    db.session.commit()
    return jsonify({"msg": "Created new profile"}), 200


@app.route("/api/deleteProfile", methods=["POST"])
@jwt_required()
def api_delete_profile():
    if not current_user:
        return jsonify({"msg": "Not authorized"}), 401
    delete_profile_data = request.json
    if not "delete_profile_name" in delete_profile_data:
        return jsonify({"msg": "Invalid profile data"}), 406
    profile_query = ICalProfile.query.filter_by(user_id=current_user.user_id,
                                                profile_name=delete_profile_data["delete_profile_name"])
    profile = profile_query.first()
    if not profile:
        return jsonify({"msg": "Invalid profile data"}), 406
    FilterWord.query.filter_by(profile_id=profile.profile_id).delete(synchronize_session=False)
    profile_query.delete(synchronize_session=False)
    db.session.commit()
    return jsonify({"msg": "Deleted profile"}), 200


@app.route("/api/changeUsername", methods=["POST"])
@jwt_required()
def api_change_username():
    if not current_user:
        return jsonify({"msg": "Not authorized"}), 401
    username_data = request.json
    if not "new_user_name" in username_data:
        return jsonify({"msg": "Invalid user data"}), 406
    new_user_name = username_data["new_user_name"]
    if current_user.user_name == new_user_name:
        return jsonify({"msg": "Already your username"}), 406
    existing_user_name = User.query.filter_by(user_name=new_user_name).first()
    if existing_user_name:
        return jsonify({"msg": "Username exists"}), 406
    current_user.user_name = new_user_name
    db.session.commit()
    return api_logout()


@app.route("/api/changePassword", methods=["POST"])
@jwt_required()
def api_change_password():
    if not current_user:
        return jsonify({"msg": "Not authorized"}), 401
    password_change_data = request.json
    if not password_change_data.keys() >= {"old_password", "new_password"}:
        return jsonify({"msg": "Invalid user password data"}), 406
    if not current_user.check_password(password_change_data["old_password"]):
        return jsonify({"msg": "Wrong old password"}), 401
    current_user.set_password(password_change_data["new_password"])
    db.session.commit()
    return jsonify({"msg": "Change successful"}), 200


@app.route("/api/removeCode", methods=["POST"])
@jwt_required()
def api_remove_code():
    if not getattr(current_user, 'is_admin', False):
        return jsonify({"msg": "Not authorized"}), 401
    code_to_remove_data = request.json
    if not "remove_code" in code_to_remove_data:
        return jsonify({"msg": "Invalid code removal data"}), 406
    code_to_remove = code_to_remove_data["remove_code"]
    OTPCode.query.filter_by(code_value=code_to_remove).delete(synchronize_session=False)
    db.session.commit()
    return jsonify({"msg": "Code removed"}), 200


@app.route("/api/addCode", methods=["POST"])
@jwt_required()
def api_add_code():
    if not getattr(current_user, 'is_admin', False):
        return jsonify({"msg": "Not authorized"}), 401
    code_to_add_data = request.json
    if not code_to_add_data.keys() >= {"new_code", "for_admin"}:
        return jsonify({"msg": "Invalid code data"}), 406
    existing_code = OTPCode.query.filter_by(code_value=code_to_add_data["new_code"]).first()
    if existing_code:
        return jsonify({"msg": "Code exists"}), 401
    new_code = OTPCode(code_value=code_to_add_data["new_code"], for_admin=code_to_add_data["for_admin"])
    db.session.add(new_code)
    db.session.commit()
    return jsonify({"msg": "Code added"}), 200


@app.route("/api/deleteAccount", methods=["POST"])
@jwt_required()
def api_delete_account():
    if not current_user:
        return jsonify({"msg": "Not authorized"}), 401
    profile_query = ICalProfile.query.filter_by(user_id=current_user.user_id)
    all_profile_ids = [profile.profile_id for profile in profile_query.all()]
    FilterWord.query.filter(FilterWord.profile_id.in_(all_profile_ids)).delete(synchronize_session=False)
    profile_query.delete(synchronize_session=False)
    User.query.filter_by(user_id=current_user.user_id).delete(synchronize_session=False)
    db.session.commit()
    return api_logout()


@app.route("/filtered/<token>")
def send_filtered_ical(token):
    ical = ICalProfile.query.filter_by(token=token).first()
    if not ical:
        return jsonify({"msg": "Invalid token"}), 406
    personal_filters = [single_filter.content for single_filter in ical.words]
    try:
        raw_ical = requests.get(ical.i_cal_url)
        ical_content = raw_ical.content.decode("utf-8")
        parsed_ical = Calendar.from_ical(ical_content)
        composed_ical = Calendar()
        for component in parsed_ical.walk():
            if component.name == "VEVENT":
                if any(filter_string in component.get("SUMMARY") for filter_string in personal_filters):
                    continue
            composed_ical.add_component(component)
        response = composed_ical.to_ical()
        return send_file(io.BytesIO(response), mimetype="text/calendar", download_name="calendar.ics"), 200
    except Exception:
        return jsonify({"msg": "Could not fetch iCal data"}), 400


@app.route("/", methods=["GET"])
@jwt_required()
def home():
    if current_user:
        return render_template("index.html", user_name=current_user.user_name, filter_list=enumerate(current_user.i_cal_profiles),
                               filter_word_list=[profile.words for profile in current_user.i_cal_profiles],
                               need_button="logout")
    return make_response(redirect(url_for("login")))


@app.route("/account", methods=["GET"])
@jwt_required()
def account():
    if current_user:
        all_codes = OTPCode.query.filter_by(code_used=False).all()
        return render_template("account.html", user_name=current_user.user_name, admin=current_user.is_admin, all_codes=all_codes,
                               need_button="logout")
    return make_response(redirect(url_for("login")))


@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html", register=False, need_button="register")


@app.route("/register", methods=["GET"])
def register():
    return render_template("login.html", register=True, need_button="login")


if __name__ == "__main__":
    app.run(host="ical-buddy", port=5000)
    with app.app_context():
        app.add_url_rule('/favicon.ico', redirect_to=url_for('static', filename='favicon.ico'))
