from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
import file_handler # Import our file handler to check if user exists
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, DecimalField, SelectField # Add IntegerField, DecimalField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, NumberRange # Add NumberRange
import file_handler
from datetime import datetime # To get the current year
from wtforms import SelectField 

class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        """Checks if the username already exists in users.json."""
        # Add robust error handling in case file is missing/corrupt
        try:
            users = file_handler.load_users()
            if username.data in users:
                raise ValidationError('That username is already taken. Please choose a different one.')
        except Exception as e:
            # Log the error, maybe raise a different validation error
            print(f"Error during username validation: {e}") # Replace with proper logging
            raise ValidationError('Could not validate username due to a server error.')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')
# Get current year for default value
current_year = datetime.now().year

# Define some basic categories (you can expand this significantly)
INCOME_CATEGORIES = [
    ('SalaryW2', 'Salary (W-2)'),
    ('SelfEmployment', 'Self-Employment/Freelance (1099)'),
    ('Investment', 'Investment Income (Dividends, Interest)'),
    ('Rental', 'Rental Income'),
    ('Other', 'Other Income')
]

EXPENSE_CATEGORIES = [
    ('Medical', 'Medical Expenses'),
    ('MortgageInterest', 'Mortgage Interest'),
    ('StudentLoanInterest', 'Student Loan Interest'),
    ('Education', 'Education/Tuition Fees'),
    ('Charitable', 'Charitable Contributions'),
    ('Business', 'Business Expense (Self-Employed)'),
    ('Other', 'Other Deductible Expense')
]


class IncomeForm(FlaskForm):
    year = IntegerField('Tax Year', default=current_year, validators=[DataRequired(), NumberRange(min=2000, max=current_year + 1)])
    source = StringField('Income Source Description', validators=[DataRequired(), Length(min=2, max=100)])
    amount = DecimalField('Amount', places=2, validators=[DataRequired(), NumberRange(min=0)])
    category = SelectField('Category', choices=INCOME_CATEGORIES, validators=[DataRequired()])
    submit = SubmitField('Add Income')

class ExpenseForm(FlaskForm):
    year = IntegerField('Tax Year', default=current_year, validators=[DataRequired(), NumberRange(min=2000, max=current_year + 1)])
    description = StringField('Expense Description', validators=[DataRequired(), Length(min=2, max=100)])
    amount = DecimalField('Amount', places=2, validators=[DataRequired(), NumberRange(min=0)])
    category = SelectField('Category', choices=EXPENSE_CATEGORIES, validators=[DataRequired()])
    submit = SubmitField('Add Expense')

FILING_STATUSES = [
    ('', '-- Select --'), # Default empty choice
    ('Single', 'Single'),
    ('MFJ', 'Married Filing Jointly'),
    ('MFS', 'Married Filing Separately'),
    ('HOH', 'Head of Household'),
    ('QW', 'Qualifying Widow(er)') # Optional, less common
]

class ProfileForm(FlaskForm):
    filing_status = SelectField('Filing Status', choices=FILING_STATUSES, validators=[DataRequired(message="Please select a filing status.")])
    submit = SubmitField('Update Profile')