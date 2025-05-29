from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from .models import Property, db
import pandas as pd
import os

bp = Blueprint('importer', __name__, url_prefix='/importer')

@bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_excel():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            flash('Файл не выбран', 'danger')
            return redirect(request.url)
        try:
            df = pd.read_excel(file)
            for _, row in df.iterrows():
                # Здесь настрой сопоставление столбцов под свою Excel-структуру!
                prop = Property(
                    title=row.get('Заголовок', ''),
                    description=row.get('Описание', ''),
                    address=row.get('Адрес', ''),
                    district=row.get('Район', ''),
                    price=row.get('Цена'),
                    area=row.get('Площадь'),
                    floor=row.get('Этаж'),
                    total_floors=row.get('Этажность'),
                    rooms=row.get('Комнат'),
                    property_type=row.get('Тип', 'Квартира'),
                    status="Активен",
                    external_id=str(row.get('ID', '')),
                    phone=row.get('Телефон', ''),
                    link=row.get('Ссылка', '')
                )
                db.session.add(prop)
            db.session.commit()
            flash('Импорт завершён!', 'success')
            return redirect(url_for('routes.properties'))
        except Exception as e:
            flash(f'Ошибка при импорте: {str(e)}', 'danger')
            return redirect(request.url)
    return render_template('import_form.html')
