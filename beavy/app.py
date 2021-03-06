from flask import Flask, session, url_for, redirect
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flask.ext.marshmallow import Marshmallow
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.security import Security, SQLAlchemyUserDatastore, current_user
from flask.ext.security.utils import encrypt_password
from flask_mail import Mail
from flask_limiter import Limiter
from flask_admin import Admin, AdminIndexView

from flask_social_blueprint.core import SocialBlueprint as SocialBp
from flask.ext.babel import Babel

from flask_environments import Environments
from pprint import pprint

from celery import Celery

import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# The app
app = Flask(__name__)


# --------- helpers for setup ----------------------------


def make_env(app):
    # environment-based configuration loading
    env = Environments(app, var_name="BEAVY_ENV")

    env.from_yaml(os.path.join(BASE_DIR, 'config.yml'))
    env.from_yaml(os.path.join(os.getcwd(), 'config.yml'))

    # update social buttons
    _FLBLPRE = "flask_social_blueprint.providers.{}"
    if not "SOCIAL_BLUEPRINT" in app.config:
        app.config["SOCIAL_BLUEPRINT"] = dict([
            ("." in name and name or _FLBLPRE.format(name), values)
            for name, values in app.config.get("SOCIAL_LOGINS").items()])

    return env


def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery


class SocialBlueprint(SocialBp):
    # our own wrapper around the SocialBlueprint
    # to forward for registring
    def login_failed_redirect(self, profile, provider):
        if not app.config.get("SECURITY_REGISTERABLE"):
            return redirect("/")

        session["_social_profile"] = profile.data
        # keep the stuff around, so we can set it up after
        # the user provided us with a nice email address
        return redirect(url_for('security.register',
                        name="{} {}".format(profile.data.get("first_name"),
                                            profile.data.get("last_name"))))


class BeavyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        if not current_user.is_active() or not current_user.is_authenticated():
            return False

        if current_user.has_role('admin'):
            return True

        return False

# --------------------------- Setting stuff up in order ----------


# load the environment and configuration
env = make_env(app)

# initialize the celery task queue
celery = make_celery(app)

# start database
db = SQLAlchemy(app)
# and database migrations
migrate = Migrate(app, db)

# initialize Resource-Based API-System
ma = Marshmallow(app)

# scripts manager
manager = Manager(app)
# add DB+migrations commands
manager.add_command('db', MigrateCommand)

# initialize i18n
babel = Babel(app)

# initialize email support
mail = Mail(app)

# limit access to the app
limiter = Limiter(app)


#  ------ Database setup is done after here ----------
from beavy.models.user import User
from beavy.models.role import Role
from beavy.models.social_connection import SocialConnection

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# add social authentication
SocialBlueprint.init_bp(app, SocialConnection, url_prefix="/_social")

# initialize admin backend
admin = Admin(app,
              '{} Admin'.format(app.config.get("NAME")),
              index_view=BeavyAdminIndexView(),
              # base_template='my_master.html',
              template_mode='bootstrap3',)


from beavy.common.admin_model_view import AdminModelView
# setup admin UI stuff
admin.add_view(AdminModelView(User, db.session,
                              name="Users",
                              menu_icon_type='glyph',
                              menu_icon_value='glyphicon-user'))


#  ----- finally, load all configured modules ---------
from .setup import replaceHomeEndpoint, generate_capability_maps

# and set the home endpoint
replaceHomeEndpoint(app)

from .models.object import Object
generate_capability_maps(Object)

from .models.activity import Activity
generate_capability_maps(Activity)

# ----- some debug features

if app.debug:

    @app.before_first_request
    def ensure_users():
        from datetime import datetime
        admin_role = user_datastore.find_or_create_role('admin')

        if not user_datastore.find_user(email="user@example.org"):
            user_datastore.create_user(email="user@example.org",
                                       confirmed_at=datetime.now(),
                                       active=True,
                                       password=encrypt_password("password"))

        if not user_datastore.find_user(email="admin@example.org"):
            user_datastore.add_role_to_user(
                user_datastore.create_user(email="admin@example.org",
                                           confirmed_at=datetime.now(),
                                           active=True,
                                           password=encrypt_password("password")), admin_role)

        user_datastore.commit()

    @app.before_first_request
    def print_routes():
        pprint(["{} -> {}".format(rule.rule, rule.endpoint)
                for rule in app.url_map.iter_rules()
                if rule.endpoint != 'static'])


