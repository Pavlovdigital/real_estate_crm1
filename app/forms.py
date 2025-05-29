from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, FloatField, IntegerField, TextAreaField,
    SelectField, SelectMultipleField, FileField, SubmitField
)
from wtforms.validators import DataRequired, Length, Email, Optional, EqualTo

# --- Авторизация ---
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

# --- Объекты недвижимости ---
class PropertyForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired(), Length(max=128)])
    description = TextAreaField('Описание', validators=[Optional()])
    address = StringField('Адрес', validators=[Optional(), Length(max=256)])
    district = SelectMultipleField('Район', choices=[], coerce=str, validators=[Optional()])
    price = FloatField('Цена', validators=[Optional()])
    area = FloatField('Площадь', validators=[Optional()])
    floor = IntegerField('Этаж', validators=[Optional()])
    total_floors = IntegerField('Этажей в доме', validators=[Optional()])
    rooms = IntegerField('Комнат', validators=[Optional()])
    property_type = SelectField(
        'Тип',
        choices=[('Квартира', 'Квартира'), ('Дом', 'Дом'), ('Коммерция', 'Коммерция')],
        validators=[Optional()]
    )
    status = SelectField('Статус', choices=[('Активен', 'Активен'), ('Архив', 'Архив')], validators=[Optional()])
    photos = FileField('Фото', validators=[Optional()])
    submit = SubmitField('Сохранить')

# --- Клиенты с фильтрацией интересов ---
class ClientForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired(), Length(max=128)])
    phone = StringField('Телефон', validators=[Optional(), Length(max=32)])
    email = StringField('Email', validators=[Optional(), Email()])
    notes = TextAreaField('Заметки', validators=[Optional()])

    # --- Пожелания клиента (автоподбор) ---
    preferred_price_min = FloatField('Мин. цена', validators=[Optional()])
    preferred_price_max = FloatField('Макс. цена', validators=[Optional()])
    preferred_districts = SelectMultipleField('Предпочтительные районы', choices=[], coerce=str, validators=[Optional()])
    preferred_floor = IntegerField('Желаемый этаж', validators=[Optional()])
    preferred_condition = StringField('Состояние / Ремонт', validators=[Optional()])
    preferred_description = StringField('Ключевые слова в описании', validators=[Optional()])

    submit = SubmitField('Сохранить')

# --- Сделки ---
class DealForm(FlaskForm):
    client_id = SelectField('Клиент', coerce=int, validators=[DataRequired()], choices=[])
    property_id = SelectField('Объект', coerce=int, validators=[DataRequired()], choices=[])
    agent_id = SelectField('Агент', coerce=int, validators=[Optional()], choices=[])
    stage = SelectField('Стадия', choices=[
        ('Новая', 'Новая'),
        ('В работе', 'В работе'),
        ('Завершена', 'Завершена')
    ])
    submit = SubmitField('Сохранить')

# --- Админская форма создания пользователей ---
class RegisterForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    role_id = SelectField('Роль', coerce=int, validators=[DataRequired()], choices=[])
    submit = SubmitField('Создать')

# --- Разовая регистрация администратора через форму ---
class RegistrationForm(FlaskForm):
    username = StringField('Имя', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрировать')