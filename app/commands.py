import click
from flask import current_app
from flask.cli import with_appcontext
from app import db
from app.models import User, Role # Added Role import
from werkzeug.security import generate_password_hash

@click.command('create-admin')
@with_appcontext
def create_admin():
    existing_user = User.query.filter_by(email="vadimexpert95@gmail.com").first()
    if existing_user:
        click.echo("⚠ Администратор уже существует.")
        return

    user = User(
        username="Вадим Павлов",
        email="vadimexpert95@gmail.com",
        password_hash=generate_password_hash("Vadim2015"),
        role="admin"
    )
    db.session.add(user)
    db.session.commit()
    click.echo("✅ Администратор создан: vadimexpert95@gmail.com")