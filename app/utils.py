import os
import json
from flask import flash
from .models import PropertyHistory, db # Assuming db is initialized in app/__init__.py
from flask_login import current_user # Assuming current_user is available for log_property_change
from datetime import datetime

# --- Directory Setup for Options JSON files ---
_CURRENT_UTILS_DIR = os.path.abspath(os.path.dirname(__file__))
# Assumes utils.py is in 'app/' and options is 'app/options/'
_OPTIONS_DIR = os.path.join(_CURRENT_UTILS_DIR, 'options')

# --- Mapping from English keys (used in routes/forms) to Cyrillic filenames ---
OPTIONS_FILENAME_MAP = {
    'district': 'Район-options.json',
    'status': 'Статус-options.json',
    'cat': 'КАТ-options.json',
    'plan': 'План-options.json',
    'm': 'М-options.json',
    'blkn': 'Блкн-options.json',
    'p': 'П-options.json',
    'condition': 'Состояние-options.json',
}

def get_json_options(option_name_key):
    """
    Loads JSON options for a given key.
    The key is mapped to a specific JSON filename.
    Returns a list of (value, label) tuples for form choices.
    """
    filename = OPTIONS_FILENAME_MAP.get(option_name_key)
    if not filename:
        print(f"Error: No filename mapping found for option key: {option_name_key}")
        return []

    file_path = os.path.join(_OPTIONS_DIR, filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                choices = []
                for item in data:
                    if isinstance(item, dict) and 'name' in item:
                        choices.append((item['name'], item['name'])) # (value, label)
                    elif isinstance(item, str):
                        choices.append((item, item)) # (value, label)
                    else:
                        print(f"Warning: Unexpected item format in {filename}: {item}")
                return choices
            else:
                print(f"Warning: JSON data in {filename} is not a list.")
                return []
    except FileNotFoundError:
        # This is a common case if a particular options file doesn't exist, return empty list.
        # print(f"Info: JSON options file not found at {file_path} (called with key: {option_name_key})")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path} (called with key: {option_name_key})")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while loading {file_path}: {e}")
        return []

def inject_json_choices(form):
    """
    Injects choices from JSON files into relevant form fields.
    Uses hasattr to check if the form has the field before attempting to set choices.
    """
    field_to_option_key_map = {
        'district': 'district',
        'status': 'status',
        'cat': 'cat',
        'plan': 'plan',
        'm': 'm',
        'blkn': 'blkn',
        'p': 'p',
        'condition': 'condition',
        'preferred_districts': 'district', # For ClientForm
        # Add other form fields that need dynamic choices
    }

    for field_name, option_key in field_to_option_key_map.items():
        if hasattr(form, field_name):
            field = getattr(form, field_name)
            if hasattr(field, 'choices'):
                current_choices = get_json_options(option_key)
                if current_choices: # Only update if new choices were successfully loaded
                    field.choices = current_choices
                # else:
                #    print(f"Info: No choices found or loaded for {field_name} using key {option_key}.")


def log_property_change(property_obj, field, old_value, new_value):
    """ Logs changes to a property's fields. """
    # This function requires current_user and db to be available and configured.
    if old_value != new_value:
        entry = PropertyHistory(
            property_id=property_obj.id,
            user_id=current_user.id if current_user else None, # Added a check for current_user
            field=field,
            old_value=str(old_value),
            new_value=str(new_value),
            changed_at=datetime.utcnow()
        )
        db.session.add(entry)
        db.session.commit()
        flash(f'Изменено поле {field}: {old_value} → {new_value}', 'info')
