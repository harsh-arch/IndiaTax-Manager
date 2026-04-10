from flask import Flask, render_template, url_for, flash, redirect, request, Blueprint
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging # Import logging
import uuid

from config import Config # Imports the hardcoded config
from forms import LoginForm, RegistrationForm
import file_handler # Our module for file I/
from forms import LoginForm, RegistrationForm, IncomeForm, ExpenseForm
from forms import LoginForm, RegistrationForm, IncomeForm, ExpenseForm, ProfileForm
from tax_logic import calculate_full_taxes # Import the main calculation function
from decimal import Decimal, InvalidOperation
from datetime import datetime
from flask import send_file # Import send_file
from utils import generate_summary_pdf # Import the PDF generator
from io import BytesIO 
from flask_mail import Mail, Message # Import Mail and Message
from threading import Thread

def format_currency(value):
    """Formats a value as USD currency."""
    if value is None:
        return "N/A" # Handle None values gracefully
    try:
        # Ensure we work with Decimal for consistent formatting
        # Convert potential strings or floats safely
        if not isinstance(value, Decimal):
            dec_value = Decimal(str(value))
        else:
            dec_value = value
        # Format as currency
        return "${:,.2f}".format(dec_value)
    except (TypeError, ValueError, InvalidOperation) as e:
        # Handle cases where conversion fails or input is unexpected type
        logging.warning(f"Could not format value '{value}' as currency: {e}")
        return str(value) # Return original string representation as fallback
    
# Configure logging if not already done elsewhere
logging.basicConfig(level=logging.INFO)

# --- Flask App Setup ---
app = Flask(__name__)
app.config.from_object(Config) # Loads config from the Config class
 
 # --- Register the custom filter with Jinja Environment ---
app.jinja_env.filters['money'] = format_currency # Add the filter here
# --- Flask-Mail Setup ---
mail = Mail(app) # Initialize Flask-Mail

# --- Flask-Login Setup ---
# ...

# --- Helper Function for Asynchronous Email Sending ---
def send_async_email(flask_app, msg):
    # Need app context to send mail outside of a request context (in a thread)
    with flask_app.app_context():
        try:
            mail.send(msg)
            logging.info(f"Debug email theoretically sent to {msg.recipients}")
        except Exception as e:
            # Log error but don't crash the app
            logging.error(f"Error sending debug email: {e}", exc_info=True) # Log full traceback

# --- Main Email Sending Function ---
def send_email(to, subject, template_or_body):
    """Sends an email asynchronously."""
    try:
        sender_email = app.config.get('MAIL_DEFAULT_SENDER', 'default-sender@example.com')
        # Create the message object
        # Assuming template_or_body is HTML content for now
        msg = Message(subject, recipients=[to], html=template_or_body, sender=sender_email)

        # Start the email sending in a background thread
        thread = Thread(target=send_async_email, args=[app, msg])
        thread.start()
        logging.info(f"Email sending thread started for recipient: {to}")
        # Don't join the thread, let the request finish quickly
    except Exception as e:
        logging.error(f"Failed to initiate email sending thread to {to}: {e}", exc_info=True)

# --- Flask-Login Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'


# User class for Flask-Login
class User(UserMixin):
    def __init__(self, username):
        self.id = username

    @staticmethod
    def get(user_id):
        users = file_handler.load_users()
        if user_id in users:
            return User(user_id)
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# --- Blueprints ---
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
data_bp = Blueprint('data', __name__, url_prefix='/data')
results_bp = Blueprint('results', __name__, url_prefix='/results')
# --- Routes ---
@main_bp.route('/')
@main_bp.route('/home')
def home():
    # You might want a dedicated home.html instead of just base.html
    return render_template('base.html', title='Home')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        # Check again just before saving, although form validation should catch it
        users = file_handler.load_users()
        if username in users:
            flash('Username already exists. Please choose another.', 'danger')
            return render_template('auth/register.html', title='Register', form=form)

        hashed_password = generate_password_hash(form.password.data)
        users[username] = hashed_password

        # Attempt to save user credentials and create initial data file
        if file_handler.save_users(users):
            logging.info(f"User credentials saved for {username}.")
            if file_handler.create_initial_user_data(username):
                logging.info(f"Initial data file created for {username}.")
                flash(f'Account created for {username}! You can now log in.', 'success')
                return redirect(url_for('auth.login'))
            else:
                logging.error(f"Failed to create initial data file for {username} AFTER saving credentials.")
                # CRITICAL: Consider how to handle this inconsistency.
                # Maybe try to remove the user credentials? Or notify admin?
                # For now, just inform the user the account might be incomplete.
                flash('Account created, but failed to initialize user data. Please contact support.', 'warning')
                return redirect(url_for('auth.login')) # Or redirect to register?
        else:
            logging.error(f"Failed to save user credentials for {username}.")
            flash('Account creation failed due to a saving error. Please try again.', 'danger')

    # If GET request or validation failed
    return render_template('auth/register.html', title='Register', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember = form.remember.data

        users = file_handler.load_users()
        user_hashed_pw = users.get(username)

        if user_hashed_pw and check_password_hash(user_hashed_pw, password):
            user = User(username)
            login_user(user, remember=remember)
            logging.info(f"User '{username}' logged in successfully.")
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            return redirect(next_page or url_for('auth.dashboard'))
        else:
            logging.warning(f"Failed login attempt for username: '{username}'.")
            flash('Login Unsuccessful. Please check username and password', 'danger')

    return render_template('auth/login.html', title='Login', form=form)

@auth_bp.route("/logout")
@login_required
def logout():
    user_id = current_user.id # Get username before logging out
    logout_user()
    logging.info(f"User '{user_id}' logged out.")
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))

@auth_bp.route("/dashboard")
@login_required
def dashboard():
    user_data = file_handler.load_user_data(current_user.id)
    current_year = datetime.now().year # Get current year
    return render_template('user/dashboard.html', title='Dashboard', user_data=user_data, current_year=current_year) # Pass it

@data_bp.route('/add_income', methods=['GET', 'POST'])
@login_required
def add_income():
    form = IncomeForm()
    if form.validate_on_submit():
        # Data is valid, proceed to save
        username = current_user.id
        year_str = str(form.year.data)
        amount_val = float(form.amount.data) # Convert Decimal to float for JSON storage

        # Generate a unique ID for this entry
        entry_id = str(uuid.uuid4())

        new_income_entry = {
            "id": entry_id,
            "source": form.source.data,
            "amount": amount_val,
            "category": form.category.data
        }

        # Load existing data
        user_data = file_handler.load_user_data(username)

        # Ensure the 'financials' structure exists
        if 'financials' not in user_data:
            user_data['financials'] = {}

        # Ensure the year exists within 'financials'
        if year_str not in user_data['financials']:
            user_data['financials'][year_str] = {'income': [], 'expenses': []} # Initialize structure for the year

        # Ensure the income list exists for the year
        if 'income' not in user_data['financials'][year_str]:
             user_data['financials'][year_str]['income'] = []

        # Append the new entry
        user_data['financials'][year_str]['income'].append(new_income_entry)

        # Save the updated data
        if file_handler.save_user_data(username, user_data):
            flash('Income added successfully!', 'success')
            # Redirect to the same page to allow adding more, or back to dashboard
            return redirect(url_for('data.add_income'))
            # Or: return redirect(url_for('auth.dashboard'))
        else:
            flash('Error saving income data. Please try again.', 'danger')

    # If GET request or validation failed
    return render_template('input/income_entry.html', title='Add Income', form=form)


@data_bp.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    form = ExpenseForm()
    if form.validate_on_submit():
        username = current_user.id
        year_str = str(form.year.data)
        amount_val = float(form.amount.data) # Convert Decimal to float for JSON
        entry_id = str(uuid.uuid4())

        new_expense_entry = {
            "id": entry_id,
            "description": form.description.data,
            "amount": amount_val,
            "category": form.category.data
        }

        user_data = file_handler.load_user_data(username)

        if 'financials' not in user_data:
            user_data['financials'] = {}

        if year_str not in user_data['financials']:
            user_data['financials'][year_str] = {'income': [], 'expenses': []}

        if 'expenses' not in user_data['financials'][year_str]:
             user_data['financials'][year_str]['expenses'] = []

        user_data['financials'][year_str]['expenses'].append(new_expense_entry)

        if file_handler.save_user_data(username, user_data):
            flash('Expense added successfully!', 'success')
            return redirect(url_for('data.add_expense'))
        else:
            flash('Error saving expense data. Please try again.', 'danger')

    return render_template('input/expenses_entry.html', title='Add Expense', form=form)
@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    username = current_user.id
    user_data = file_handler.load_user_data(username)

    if form.validate_on_submit():
        # Update profile data
        selected_status = form.filing_status.data
        if 'profile' not in user_data:
            user_data['profile'] = {} # Ensure profile dict exists
        user_data['profile']['filing_status'] = selected_status

        if file_handler.save_user_data(username, user_data):
            flash('Profile updated successfully!', 'success')
            # return redirect(url_for('auth.profile')) # Redirect back to profile
            return redirect(url_for('auth.dashboard')) # Or redirect to dashboard
        else:
            flash('Error saving profile data. Please try again.', 'danger')

    elif request.method == 'GET':
        # Populate form with existing data on GET request
        if 'profile' in user_data and 'filing_status' in user_data['profile']:
            form.filing_status.data = user_data['profile']['filing_status']
        else:
             form.filing_status.data = '' # Set default if no status saved yet


    return render_template('user/profile.html', title='Profile', form=form)

@results_bp.route('/summary/<int:year>')
@login_required
def tax_summary(year):
    username = current_user.id
    user_data = file_handler.load_user_data(username)
    profile_data = user_data.get("profile", {})
    filing_status = profile_data.get("filing_status")
    financial_data = user_data.get("financials", {})

    if not filing_status:
        flash("Please set your filing status in your profile before calculating taxes.", "warning")
        return redirect(url_for('auth.profile')) # Redirect to profile page

    # Call the calculation logic
    calculation_results = calculate_full_taxes(financial_data, filing_status, year)

    # Check for errors during calculation
    if calculation_results.get("error"):
         flash(f"Error calculating taxes: {calculation_results['error']}", "danger")
         # Redirect to dashboard or show an error page
         return redirect(url_for('auth.dashboard'))

    # Format Decimals to strings for template rendering if needed, or use Jinja filters
    # For simplicity, we'll pass Decimals and format in Jinja

    return render_template('results/tax_summary.html',
                           title=f'Tax Summary {year}',
                           results=calculation_results,
                           year=year)

@results_bp.route('/download_summary/<int:year>')
@login_required
def download_summary(year):
    username = current_user.id
    user_data = file_handler.load_user_data(username)
    profile_data = user_data.get("profile", {})
    filing_status = profile_data.get("filing_status")
    financial_data = user_data.get("financials", {})

    if not filing_status:
        flash("Cannot generate PDF: Filing status not set.", "warning")
        return redirect(url_for('auth.profile'))

    # Calculate the tax data again (or retrieve if stored temporarily)
    calculation_results = calculate_full_taxes(financial_data, filing_status, year)

    if calculation_results.get("error"):
         flash(f"Cannot generate PDF due to calculation error: {calculation_results['error']}", "danger")
         return redirect(url_for('results.tax_summary', year=year)) # Go back to HTML summary

    # Generate PDF using the utility function
    try:
        pdf_buffer = generate_summary_pdf(calculation_results)
        filename = f"tax_summary_{username}_{year}.pdf"

        return send_file(
            pdf_buffer,
            as_attachment=True, # Treat as download
            download_name=filename, # Suggested filename for user
            mimetype='application/pdf'
        )
    except Exception as e:
         logging.error(f"Error generating PDF for user {username}, year {year}: {e}")
         flash("An error occurred while generating the PDF.", "danger")
         return redirect(url_for('results.tax_summary', year=year))
    
@auth_bp.route('/history') # Or put in user_bp if you create one
@login_required
def history():
    username = current_user.id
    user_data = file_handler.load_user_data(username)
    financial_data = user_data.get("financials", {})
    filing_status = user_data.get("profile", {}).get("filing_status")

    history_summary = []
    # Get years sorted, newest first
    sorted_years = sorted(financial_data.keys(), reverse=True)

    for year_str in sorted_years:
        try:
            year = int(year_str)
             # Calculate summary for each year (could be computationally expensive for many years)
             # Alternatively, store key results when calculated, but that adds complexity
            if not filing_status:
                 # Or maybe show data even without calculation?
                 year_summary = {"year": year, "error": "Filing status not set"}
            else:
                calc = calculate_full_taxes(financial_data, filing_status, year)
                # Extract key figures for the history view
                year_summary = {
                    "year": year,
                    "gross_income": calc.get("gross_income"),
                    "taxable_income": calc.get("taxable_income"),
                    "final_tax_liability": calc.get("final_tax_liability"),
                    "error": calc.get("error") # Include any calculation errors
                }
            history_summary.append(year_summary)

        except ValueError:
             logging.warning(f"Skipping non-integer year key '{year_str}' in history for user {username}")
             continue # Skip non-year keys if any
        except Exception as e:
             logging.error(f"Error processing history for year {year_str}, user {username}: {e}")
             history_summary.append({"year": year_str, "error": "Calculation error"})


    return render_template('user/history.html',
                           title='Filing History',
                           history_data=history_summary)

# Register blueprints
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(data_bp) # Register the data blueprint
app.register_blueprint(results_bp)

# --- Placeholder for tax_logic.py import ---
# from tax_logic import ...

# --- Run App ---
if __name__ == '__main__':
    print("--- Tax Assistant Starting ---")
    print(f"SECRET_KEY set: {bool(app.config.get('SECRET_KEY'))}")
    print(f"Users file path: {Config.USERS_FILE}")
    print(f"User data directory: {Config.USER_DATA_DIR}")
    # Ensure data directories one last time before running
    Config.ensure_data_dirs()
    # WARNING: debug=True is insecure for production. Keep it True for development.
    # host='0.0.0.0' makes the server accessible on your network. Use with caution.
    app.run(debug=True, host='127.0.0.1', port=5001)