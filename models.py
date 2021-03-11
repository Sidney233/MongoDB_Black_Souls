import pymongo
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import login, app, mongo


class User(UserMixin):
    id = ""
    username = ""
    email = ""
    password_hash = ""

    def __init__(self, id, username, email, password_hash):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @login.user_loader
    def load_user(id):
        find_user = mongo.db.users.find_one({"_id": id})
        if find_user is None:
            return None
        user = User(id=find_user["_id"], username=find_user["username"], email=find_user["email"],
                    password_hash=find_user["password_hash"])
        return user
