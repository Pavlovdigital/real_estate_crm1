from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, make_response, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from . import db, login_manager
from .models import User, Role, Property, Client, Deal, PropertyHistory
from .forms import LoginForm, PropertyForm, ClientForm, DealForm, RegisterForm
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pandas as pd
from io import BytesIO
import os
from sqlalchemy import or_
import pdfkit

import threading
from app.parser import parse_krisha, parse_olx

bp = Blueprint('routes', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Регистрация администратора (разово через форму) ---
@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Пользователь с таким email уже существует', 'danger')
            return redirect(url_for('routes.register'))
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password, role='admin')
        db.session.add(user)
        db.session.commit()
        flash('Администратор зарегистрирован! Теперь войдите в систему.', 'success')
        return redirect(url_for('routes.login'))
    return render_template('register.html', form=form)

# --- Авторизация: "/" и "/login" обрабатываются одинаково ---
@bp.route('/', methods=['GET', 'POST'])
@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            return redirect(url_for('routes.dashboard'))
        flash('Неверный email или пароль', 'danger')
    return render_template('login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.login'))

@bp.route('/dashboard')
@login_required
def dashboard():
    props_count = Property.query.count()
    deals_count = Deal.query.count()
    clients_count = Client.query.count()
    return render_template('dashboard.html', props_count=props_count, deals_count=deals_count, clients_count=clients_count)

@bp.route('/properties')
@login_required
def properties():
    q = Property.query
    filter_fields = ["district", "cat", "status", "plan", "m", "blkn", "p", "condition"]
    for field in filter_fields:
        vals = request.args.getlist(field)
        if vals:
            q = q.filter(getattr(Property, field).in_(vals))
    price_min = request.args.get('price_min')
    price_max = request.args.get('price_max')
    if price_min: q = q.filter(Property.price >= float(price_min))
    if price_max: q = q.filter(Property.price <= float(price_max))
    for f in ['street', 'phone', 'description']:
        val = request.args.get(f)
        if val:
            q = q.filter(getattr(Property, f).ilike(f"%{val}%"))
    props = q.order_by(Property.updated_at.desc()).all()
    from app.utils import get_json_options
    context = {
        'props': props,
        'district_options': get_json_options('district'),
        'cat_options': get_json_options('cat'),
        'status_options': get_json_options('status'),
        'plan_options': get_json_options('plan'),
        'm_options': get_json_options('m'),
        'blkn_options': get_json_options('blkn'),
        'p_options': get_json_options('p'),
        'condition_options': get_json_options('condition'),
    }
    return render_template('properties.html', **context)

@bp.route('/property/<int:property_id>')
@login_required
def property_detail(property_id):
    prop = Property.query.get_or_404(property_id)
    history = PropertyHistory.query.filter_by(property_id=property_id).order_by(PropertyHistory.changed_at.desc()).all()
    return render_template('object_detail.html', prop=prop, history=history)

@bp.route('/property/add', methods=['GET', 'POST'])
@login_required
def property_add():
    form = PropertyForm()
    from app.utils import inject_json_choices
    inject_json_choices(form)
    if form.validate_on_submit():
        prop = Property(
            cat=form.cat.data,
            status=form.status.data,
            district=form.district.data,
            price=form.price.data,
            plan=form.plan.data,
            floor=form.floor.data,
            total_floors=form.total_floors.data,
            area=form.area.data,
            m=form.m.data,
            s=form.s.data,
            s_kh=form.s_kh.data,
            blkn=form.blkn.data,
            p=form.p.data,
            condition=form.condition.data,
            phone=form.phone.data,
            street=form.street.data,
            d_kv=form.d_kv.data,
            year=form.year.data,
            description=form.description.data,
        )
        db.session.add(prop)
        db.session.commit()
        flash('Объект добавлен!', 'success')
        return redirect(url_for('routes.properties'))
    return render_template('property_form.html', form=form)

@bp.route('/property/edit/<int:property_id>', methods=['GET', 'POST'])
@login_required
def property_edit(property_id):
    prop = Property.query.get_or_404(property_id)
    form = PropertyForm(obj=prop)
    from app.utils import inject_json_choices
    inject_json_choices(form)
    if form.validate_on_submit():
        for field in ['cat','status','district','price','plan','floor','total_floors','area','m','s','s_kh','blkn','p','condition','phone','street','d_kv','year','description']:
            setattr(prop, field, getattr(form, field).data)
        db.session.commit()
        flash('Объект обновлён!', 'success')
        return redirect(url_for('routes.properties'))
    return render_template('property_form.html', form=form, edit=True)

@bp.route('/properties/import', methods=['GET', 'POST'])
@login_required
def import_properties():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            flash('Файл не выбран', 'danger')
            return redirect(request.url)
        try:
            df = pd.read_excel(file)
            count_new = 0
            for _, row in df.iterrows():
                ext_id = str(row.get('ID', ''))
                duplicate = Property.query.filter(
                    (Property.external_id == ext_id) |
                    ((Property.phone == row.get('Телефон')) &
                     (Property.floor == row.get('Эт')) &
                     (Property.total_floors == row.get('Эть')) &
                     (Property.rooms == row.get('Комнат')))
                ).first()
                if duplicate:
                    continue
                prop = Property(
                    cat=row.get('КАТ'),
                    status=row.get('Статус'),
                    district=row.get('Район'),
                    price=row.get('Цена'),
                    plan=row.get('План'),
                    floor=row.get('Эт'),
                    total_floors=row.get('Эть'),
                    area=row.get('М'),
                    m=row.get('М'),
                    s=row.get('S'),
                    s_kh=row.get('S кх'),
                    blkn=row.get('Блкн'),
                    p=row.get('П'),
                    condition=row.get('Состояние'),
                    phone=row.get('Телефон'),
                    street=row.get('Улица'),
                    d_kv=row.get('Д-кв'),
                    year=row.get('Год'),
                    description=row.get('Описание'),
                    source=row.get('Источник'),
                    photos=row.get('Фото'),
                    external_id=ext_id
                )
                db.session.add(prop)
                count_new += 1
            db.session.commit()
            flash(f'Импорт завершён! Новых объектов: {count_new}', 'success')
            return redirect(url_for('routes.properties'))
        except Exception as e:
            flash(f'Ошибка при импорте: {str(e)}', 'danger')
            return redirect(request.url)
    return render_template('import_form.html')

@bp.route('/properties/export/pdf')
@login_required
def export_properties_pdf():
    props = Property.query.all()
    rendered = render_template('pdf_properties.html', props=props)
    pdf = pdfkit.from_string(rendered, False)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=properties.pdf'
    return response

@bp.route('/global_search', methods=['GET'])
@login_required
def global_search():
    q = request.args.get('q', '')
    props = []
    if q:
        like = f"%{q}%"
        props = Property.query.filter(
            or_(
                Property.title.ilike(like),
                Property.description.ilike(like),
                Property.address.ilike(like),
                Property.district.ilike(like),
                Property.price.cast(db.String).ilike(like),
                Property.area.cast(db.String).ilike(like),
                Property.floor.cast(db.String).ilike(like),
                Property.total_floors.cast(db.String).ilike(like),
                Property.rooms.cast(db.String).ilike(like),
                Property.property_type.ilike(like),
                Property.status.ilike(like),
                Property.phone.ilike(like),
                Property.external_id.ilike(like),
                Property.link.ilike(like)
            )
        ).all()
    return render_template('global_search.html', props=props, query=q)

PARSER_STATUS = {"step": "Готов к запуску", "percent": 0, "log": []}

@bp.route('/parser/run', methods=['POST'])
@login_required
def run_parser():
    if not current_user.role or current_user.role.name != 'admin':
        return jsonify({'error': 'Нет доступа!'}), 403
    def do_parse():
        PARSER_STATUS.update({"step": "Krisha", "percent": 0, "log": []})
        parse_krisha(PARSER_STATUS)
        PARSER_STATUS.update({"step": "OLX", "percent": 50})
        parse_olx(PARSER_STATUS)
        PARSER_STATUS.update({"step": "Готово", "percent": 100})
    threading.Thread(target=do_parse).start()
    return jsonify({"ok": True})

@bp.route('/parser/status')
@login_required
def parser_status():
    return jsonify(PARSER_STATUS)

@bp.route('/clients')
@login_required
def clients():
    clients = Client.query.all()
    return render_template('clients.html', clients=clients)

@bp.route('/deals')
@login_required
def deals():
    deals = Deal.query.all()
    return render_template('deals.html', deals=deals)

@bp.route('/property/<int:property_id>/history')
@login_required
def property_history(property_id):
    prop = Property.query.get_or_404(property_id)
    history = PropertyHistory.query.filter_by(property_id=property_id).order_by(PropertyHistory.changed_at.desc()).all()
    return render_template('history.html', prop=prop, history=history)

@bp.route('/admin')
@login_required
def admin_panel():
    if not current_user.role or current_user.role.name != "admin":
        flash('Нет доступа!', 'danger')
        return redirect(url_for('routes.dashboard'))
    users = User.query.all()
    roles = Role.query.all()
    return render_template('admin.html', users=users, roles=roles)

@bp.route('/kanban')
@login_required
def kanban_board():
    deals_new = Deal.query.filter_by(stage="Новая").all()
    deals_work = Deal.query.filter_by(stage="В работе").all()
    deals_done = Deal.query.filter_by(stage="Завершена").all()
    return render_template('kanban.html', deals_new=deals_new, deals_work=deals_work, deals_done=deals_done)

@bp.route('/kanban/move/<int:deal_id>/<string:stage>')
@login_required
def move_deal(deal_id, stage):
    deal = Deal.query.get_or_404(deal_id)
    deal.stage = stage
    db.session.commit()
    flash(f"Сделка перемещена в стадию '{stage}'", 'success')
    return redirect(url_for('routes.kanban_board'))