import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
bootstrap = Bootstrap()

def create_app():
    app = Flask(__name__, static_folder='static')

    # Конфигурация приложения
    app.config.from_prefixed_env()
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'supersecretkey'),
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///app.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    bootstrap.init_app(app)

    # Регистрация кастомных CLI-команд
    from .commands import create_admin
    app.cli.add_command(create_admin)

    # Регистрация Blueprint'ов
    from . import routes, models, forms, utils, parser, kanban, importer
    app.register_blueprint(routes.bp)
    app.register_blueprint(kanban.bp)
    app.register_blueprint(importer.bp)

    return app
