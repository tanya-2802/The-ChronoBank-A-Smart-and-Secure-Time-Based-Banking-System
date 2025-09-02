from flask_wtf import FlaskForm
from wtforms import FloatField, IntegerField, SelectField, HiddenField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class LoanApplicationForm(FlaskForm):
    """Form for applying for a loan."""
    
    account_id = HiddenField('Account ID')
    
    amount = FloatField(
        'Loan Amount (hours)',
        validators=[
            DataRequired(),
            NumberRange(min=1, max=1000, message='Loan amount must be between 1 and 1000 hours')
        ]
    )
    
    term_days = IntegerField(
        'Loan Term (days)',
        validators=[
            DataRequired(),
            NumberRange(min=7, max=365, message='Loan term must be between 7 and 365 days')
        ]
    )
    
    repayment_strategy = SelectField(
        'Repayment Strategy',
        choices=[
            ('FIXED', 'Fixed Rate - Equal payments over the term'),
            ('DYNAMIC', 'Dynamic Rate - Adjusts with market conditions'),
            ('EARLY', 'Early Repayment - Discounts for paying early')
        ],
        validators=[DataRequired()]
    )
    
    submit = SubmitField('Apply for Loan')

class LoanPaymentForm(FlaskForm):
    """Form for making a payment towards a loan."""
    
    account_id = HiddenField('Account ID')
    
    amount = FloatField(
        'Payment Amount (hours)',
        validators=[
            DataRequired(),
            NumberRange(min=0.1, message='Payment amount must be at least 0.1 hours')
        ]
    )
    
    submit = SubmitField('Make Payment')