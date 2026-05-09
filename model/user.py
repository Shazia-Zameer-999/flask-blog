from flask_login import UserMixin
   
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data["_id"])
        self.username = user_data["username"]
        self.provider = user_data["provider"]
        self.provider_id = user_data["provider_id"]
        self.email = user_data["email"]
        self.profile_pic = user_data["profile_pic"]
