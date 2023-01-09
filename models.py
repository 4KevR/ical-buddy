from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "USER"

    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String)
    admin_role = db.Column(db.Boolean)

    i_cal_profiles = relationship("ICalProfile")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class ICalProfile(db.Model):
    __tablename__ = "I_CAL_PROFILE"

    profile_id = db.Column(db.Integer, primary_key=True)
    profile_name = db.Column(db.String)
    i_cal_url = db.Column(db.String)
    token = db.Column(db.String, unique=True)

    user_id = db.Column(db.Integer, db.ForeignKey("USER.user_id"))

    words = relationship("FilterWord")


class FilterWord(db.Model):
    __tablename__ = "FILTER_WORD"

    word_id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String)

    profile_id = db.Column(db.Integer, db.ForeignKey("I_CAL_PROFILE.profile_id"))


class OTPCode(db.Model):
    __tablename__ = "OTP_CODE"

    code_id = db.Column(db.Integer, primary_key=True)
    code_value = db.Column(db.Integer, unique=True)
    code_used = db.Column(db.Boolean)
