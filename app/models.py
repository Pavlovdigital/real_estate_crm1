from . import db
from flask_login import UserMixin
from datetime import datetime

# --- Справочники ---
class District(db.Model):
    __tablename__ = 'districts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)

class StatusOption(db.Model):
    __tablename__ = 'status_options'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)

class PlanOption(db.Model):
    __tablename__ = 'plan_options'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)

class MOption(db.Model):
    __tablename__ = 'm_options'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)

class BlknOption(db.Model):
    __tablename__ = 'blkn_options'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)

class POption(db.Model):
    __tablename__ = 'p_options'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)

class ConditionOption(db.Model):
    __tablename__ = 'condition_options'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)

# --- Основные модели ---
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    users = db.relationship('User', backref='role', lazy=True)

class User(UserMixin, db.Model):
    __tablename__ = 'users'  # исправлено: двойное подчеркивание
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(128), unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    
    # Внешний ключ на таблицу roles
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=True)
    
    # Обратная связь с сделками
    deals = db.relationship('Deal', backref='agent', lazy=True)

class Property(db.Model):
    __tablename__ = 'properties'
    id = db.Column(db.Integer, primary_key=True)
    cat = db.Column(db.String(32))
    status = db.Column(db.String(32))
    district = db.Column(db.String(64))
    price = db.Column(db.Float)
    plan = db.Column(db.String(32))
    floor = db.Column(db.Integer)
    total_floors = db.Column(db.Integer)
    area = db.Column(db.Float)
    m = db.Column(db.String(32))
    s = db.Column(db.String(16))
    s_kh = db.Column(db.String(16))
    blkn = db.Column(db.String(16))
    p = db.Column(db.String(16))
    condition = db.Column(db.String(64))
    phone = db.Column(db.String(32))
    street = db.Column(db.String(128))
    d_kv = db.Column(db.String(32))
    year = db.Column(db.String(16))
    description = db.Column(db.Text)
    source = db.Column(db.String(32))
    photos = db.Column(db.Text)  # ссылки через запятую
    link = db.Column(db.String(256))
    external_id = db.Column(db.String(128), unique=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    deals = db.relationship('Deal', backref='property', lazy=True)
    history = db.relationship('PropertyHistory', backref='property', lazy=True)

class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    phone = db.Column(db.String(32))
    email = db.Column(db.String(128))
    notes = db.Column(db.Text)
    deals = db.relationship('Deal', backref='client', lazy=True)
    properties = db.relationship('Property', backref='client_obj', lazy=True)

    # --- Интересы клиента для подбора ---
    price_min = db.Column(db.Float)
    price_max = db.Column(db.Float)
    districts = db.Column(db.Text)  # сохраняется список через запятую
    floor = db.Column(db.Integer)
    condition = db.Column(db.String(64))
    description = db.Column(db.Text)

class Deal(db.Model):
    __tablename__ = 'deals'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'))
    agent_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    stage = db.Column(db.String(32), default="Новая")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PropertyHistory(db.Model):
    __tablename__ = 'property_history'
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    field = db.Column(db.String(64))
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)