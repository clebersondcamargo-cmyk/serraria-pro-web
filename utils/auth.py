from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def verify_password(self, pwd):
        return bcrypt.check_password_hash(self.password, pwd)

def create_user(username, email, password):
    hashed = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(username=username, email=email, password=hashed)
    db.session.add(user)
    db.session.commit()
    return user

def find_user(username):
    return User.query.filter_by(username=username).first()
