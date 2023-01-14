import io
import os
import requests

from datetime import datetime, timedelta, timezone

from flask import Flask, jsonify, send_file, request, render_template, make_response, redirect, url_for
from flask_migrate import Migrate
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager, get_jwt, \
    set_access_cookies, unset_jwt_cookies

from models import db, User, ICalProfile, FilterWord, OTPCode

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config["STATIC_FOLDER"] = "static"
app.config["TEMPLATES_FOLDER"] = "templates"

app.config["JWT_SECRET_KEY"] = os.environ["JWT_SECRET_KEY"]
app.config["JWT_COOKIE_SECURE"] = os.environ["JWT_COOKIE_SECURE"]
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
            access_token = create_access_token(identity=user_name)
            set_access_cookies(response, access_token)
            return response
    return jsonify({"msg": "Login failed"}), 401


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
            access_token = create_access_token(identity=get_jwt_identity())
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
    user_name = data["username"]
    password = data["password"]
    otp_code = data["otp"]
    db_code = OTPCode.query.filter_by(code_value=otp_code).first()
    if db_code:
        if not db_code.code_used:
            existing_user = User.query.filter_by(user_name=user_name).first()
            if existing_user:
                return jsonify({"msg": "Username exists"}), 401
            new_user = User(user_name=user_name, is_admin=db_code.for_admin)
            new_user.set_password(password)
            db.session.add(new_user)
            db_code.code_used = True
            db.session.commit()
            return make_login(user_name, password)
    return jsonify({"msg": "Invalid OTP"}), 401


@app.route("/api/logout", methods=["POST"])
def api_logout():
    response = make_response(redirect(url_for("login")))
    unset_jwt_cookies(response)
    return response


@app.route("/api/changeProfile", methods=["POST"])
@jwt_required()
def api_change_profile():
    current_user = get_jwt_identity()
    db_user = User.query.filter_by(user_name=current_user).first()

    profile_change_data = request.json
    profile_to_change = ICalProfile.query.filter_by(user_id=db_user.user_id,
                                                    profile_name=profile_change_data["profile_name_original"]).first()
    if "profile_name" in profile_change_data:
        profile_to_change.profile_name = profile_change_data["profile_name"]
    if "i_cal_url" in profile_change_data:
        profile_to_change.i_cal_url = profile_change_data["i_cal_url"]
    if "token" in profile_change_data:
        profile_to_change.token = profile_change_data["token"]
    if "add_filter" in profile_change_data:
        existing_word = FilterWord.query.filter_by(content=profile_change_data["add_filter"],
                                                   profile_id=profile_to_change.profile_id).first()
        if not existing_word:
            new_filter = FilterWord(content=profile_change_data["add_filter"], profile_id=profile_to_change.profile_id)
            db.session.add(new_filter)
        else:
            return jsonify({"msg": "Word exists"}), 401
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
    current_user = get_jwt_identity()
    db_user = User.query.filter_by(user_name=current_user).first()
    new_profile_data = request.json
    existing_profile = ICalProfile.query.filter_by(user_id=db_user.user_id,
                                                   profile_name=new_profile_data["new_profile_name"]).first()
    if existing_profile:
        return jsonify({"msg": "Name exists"}), 401
    existing_token = ICalProfile.query.filter_by(token=new_profile_data["new_token"]).first()
    if existing_token:
        return jsonify({"msg": "Token exists"}), 401
    new_profile_element = ICalProfile(profile_name=new_profile_data["new_profile_name"],
                                      i_cal_url=new_profile_data["new_ical_url"], token=new_profile_data["new_token"],
                                      user_id=db_user.user_id)
    db.session.add(new_profile_element)
    db.session.commit()
    return jsonify({"msg": "Created new profile"}), 200


@app.route("/api/deleteProfile", methods=["POST"])
@jwt_required()
def api_delete_profile():
    current_user = get_jwt_identity()
    db_user = User.query.filter_by(user_name=current_user).first()

    delete_profile_data = request.json
    profile_query = ICalProfile.query.filter_by(user_id=db_user.user_id,
                                                profile_name=delete_profile_data["delete_profile_name"])
    FilterWord.query.filter_by(profile_id=profile_query.first().profile_id).delete(synchronize_session=False)
    profile_query.delete(synchronize_session=False)

    db.session.commit()
    return jsonify({"msg": "Deleted profile"}), 200


@app.route("/api/changeUsername", methods=["POST"])
@jwt_required()
def api_change_username():
    current_user = get_jwt_identity()
    db_user = User.query.filter_by(user_name=current_user).first()

    if db_user:
        new_user_name = request.json["new_user_name"]
        if db_user.user_name == new_user_name:
            return jsonify({"msg": "Already your username"}), 401
        existing_user_name = User.query.filter_by(user_name=new_user_name).first()
        if existing_user_name:
            return jsonify({"msg": "Username exists"}), 401
        db_user.user_name = new_user_name
        db.session.commit()
        return api_logout()
    return jsonify({"msg": "Operation failed"}), 401


@app.route("/api/changePassword", methods=["POST"])
@jwt_required()
def api_change_password():
    current_user = get_jwt_identity()
    db_user_query = User.query.filter_by(user_name=current_user)
    db_user = db_user_query.first()

    if db_user:
        request_data = request.json
        if not db_user.check_password(request_data["old_password"]):
            return jsonify({"msg": "Wrong old password"}), 401
        db_user.set_password(request_data["new_password"])
        db.session.commit()
        return jsonify({"msg": "Change successful"}), 200
    return jsonify({"msg": "Operation failed"}), 401


@app.route("/api/removeCode", methods=["POST"])
@jwt_required()
def api_remove_code():
    current_user = get_jwt_identity()
    db_user = User.query.filter_by(user_name=current_user).first()

    if db_user.is_admin:
        code_to_remove = request.json["remove_code"]
        OTPCode.query.filter_by(code_value=code_to_remove).delete(synchronize_session=False)
        db.session.commit()
        return jsonify({"msg": "Code removed"}), 200
    return jsonify({"msg": "Not authorized"}), 401


@app.route("/api/addCode", methods=["POST"])
@jwt_required()
def api_add_code():
    current_user = get_jwt_identity()
    db_user = User.query.filter_by(user_name=current_user).first()

    if db_user.is_admin:
        request_data = request.json
        existing_code = OTPCode.query.filter_by(code_value=request_data["new_code"]).first()
        if existing_code:
            return jsonify({"msg": "Code exists"}), 401
        new_code = OTPCode(code_value=request_data["new_code"], for_admin=request_data["for_admin"])
        db.session.add(new_code)
        db.session.commit()
        return jsonify({"msg": "Code added"}), 200
    return jsonify({"msg": "Not authorized"}), 401


@app.route("/api/deleteAccount", methods=["POST"])
@jwt_required()
def api_delete_account():
    current_user = get_jwt_identity()
    db_user_query = User.query.filter_by(user_name=current_user)
    db_user = db_user_query.first()

    if db_user:
        profile_query = ICalProfile.query.filter_by(user_id=db_user.user_id)
        all_profile_ids = [profile.profile_id for profile in profile_query.all()]
        FilterWord.query.filter(FilterWord.profile_id.in_(all_profile_ids)).delete(synchronize_session=False)
        profile_query.delete(synchronize_session=False)
        db_user_query.delete(synchronize_session=False)
        db.session.commit()
        return api_logout()
    return jsonify({"msg": "Operation failed"}), 401


@app.route("/filtered/<token>")
def send_filtered_ical(token):
    ical = ICalProfile.query.filter_by(token=token).first()
    personal_filters = [single_filter.content for single_filter in ical.words]
    raw_ical = requests.get(ical.i_cal_url)
    ical_content = raw_ical.content.decode("utf-8")
    delimiter = "BEGIN"
    event_list = [delimiter + e for e in ical_content.split(delimiter) if e]
    filtered_event_list = [e for e in event_list if not any(t in e for t in personal_filters)]
    response = "".join(filtered_event_list)
    return send_file(io.BytesIO(bytes(response, "utf-8")), mimetype="text/calendar", download_name="calendar.ics"), 200


@app.route("/", methods=["GET"])
@jwt_required()
def home():
    current_user = get_jwt_identity()
    db_user = User.query.filter_by(user_name=current_user).first()
    if db_user:
        return render_template("index.html", user_name=db_user.user_name, filter_list=enumerate(db_user.i_cal_profiles),
                               filter_word_list=[profile.words for profile in db_user.i_cal_profiles],
                               need_button="logout")
    return make_response(redirect(url_for("login")))


@app.route("/account", methods=["GET"])
@jwt_required()
def account():
    current_user = get_jwt_identity()
    db_user = User.query.filter_by(user_name=current_user).first()
    if db_user:
        all_codes = OTPCode.query.filter_by(code_used=False).all()
        return render_template("account.html", user_name=db_user.user_name, admin=db_user.is_admin, all_codes=all_codes,
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
