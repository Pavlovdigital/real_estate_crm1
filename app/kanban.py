from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from .models import Deal, db

bp = Blueprint('kanban', __name__, url_prefix='/kanban')

@bp.route('/')
@login_required
def kanban_board():
    deals_new = Deal.query.filter_by(stage="Новая").all()
    deals_work = Deal.query.filter_by(stage="В работе").all()
    deals_done = Deal.query.filter_by(stage="Завершена").all()
    return render_template('kanban.html',
                           deals_new=deals_new,
                           deals_work=deals_work,
                           deals_done=deals_done)

@bp.route('/move/<int:deal_id>/<string:stage>')
@login_required
def move_deal(deal_id, stage):
    deal = Deal.query.get_or_404(deal_id)
    deal.stage = stage
    db.session.commit()
    flash(f"Сделка перемещена в стадию '{stage}'", 'success')
    return redirect(url_for('kanban.kanban_board'))
