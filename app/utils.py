from flask import flash
from .models import PropertyHistory, db
from flask_login import current_user
from datetime import datetime

def log_property_change(property_obj, field, old_value, new_value):
    if old_value != new_value:
        entry = PropertyHistory(
            property_id=property_obj.id,
            user_id=current_user.id if current_user.is_authenticated else None,
            field=field,
            old_value=str(old_value),
            new_value=str(new_value),
            changed_at=datetime.utcnow()
        )
        db.session.add(entry)
        db.session.commit()
        flash(f'Изменено поле {field}: {old_value} → {new_value}', 'info')
