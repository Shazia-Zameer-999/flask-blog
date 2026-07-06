from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, data):
        self.id = str(data["_id"])
        self.username = data.get("username", "Reader")
        self.provider = data.get("provider", "local")
        self.provider_id = data.get("provider_id", self.id)
        self.email = data.get("email", "")
        self.profile_pic = data.get("profile_pic", "")
        self.bio = data.get("bio", "")
        self.role = data.get("role", "reader")

    @property
    def is_admin(self):
        return self.role == "admin"
