from flask_wtf import FlaskForm
from wtforms import FloatField, IntegerField, HiddenField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class InvestmentForm(FlaskForm):
    """Form for creating an investment."""
    account_id = HiddenField('Account ID')
    amount = FloatField('Amount (hours)', validators=[
        DataRequired(),
        NumberRange(min=0.1, message='Amount must be at least 0.1 hours')
    ])
    term_days = IntegerField('Term (days)', validators=[
        DataRequired(),
        NumberRange(min=1, max=365, message='Term must be between 1 and 365 days')
    ])
    submit = SubmitField('Invest')