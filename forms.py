from flask_wtf import FlaskForm
from wtforms import widgets, StringField, SubmitField, PasswordField, TextAreaField, SelectMultipleField
from wtforms.validators import DataRequired, Email, EqualTo
from flask_mathdown.fields import MathDownField
from constants import *


class NoValidationSelectMultipleField(SelectMultipleField):
    def pre_validate(self, form):
        """pre_validation is disabled"""


class MultiCheckboxField(SelectMultipleField):
    def __init__(self, should_prevalidate, **kwargs):
        super().__init__(**kwargs)
        self.should_prevalidate = should_prevalidate

    def pre_validate(self, form):
        if self.should_prevalidate:
            super().pre_validate(form)
        else:
            pass
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password_check = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])

    submit = SubmitField('Sign Up')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

    submit = SubmitField('Login')


class NewDiscussionForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()], render_kw={'onfocus': "focus_func()"})
    text = MathDownField('Text', validators=[DataRequired()], render_kw={'onfocus': "focus_func()"})
    assigned = NoValidationSelectMultipleField('Assigned', choices=DEFAULT_CHOICES)
    available = NoValidationSelectMultipleField('Available', choices=AVAILABLE_CHOICES)

    submit = SubmitField('Post')


class NewCommentForm(FlaskForm):
    text = MathDownField('Add New Comment', validators=[DataRequired()], render_kw={'onfocus': "focus_func()"})

    submit = SubmitField('Post')


class SearchDiscussionsForm(FlaskForm):
    search_text = StringField('Search')
    tag_filter_choices = MultiCheckboxField(should_prevalidate=False, label='Filter by tag', choices=AVAILABLE_CHOICES)

    submit = SubmitField('Submit')


class ChangePasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    new_password_check = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('new_password')])

    submit = SubmitField('Change Password')
