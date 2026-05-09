from authlib.integrations.flask_client import OAuth
from flask_bootstrap import Bootstrap5
from flask_wtf import CSRFProtect
from flask_login import LoginManager

csrf = CSRFProtect()
loginManager = LoginManager()
oauth = OAuth()
bootstrap = Bootstrap5()
