from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import random
from genetic_algorithm import select_parents, generate_schedule, initialize_population, evaluate_fitness, crossover, mutate, elitism, DAYS_OF_WEEK, DOCTOR_SPECIALTIES, convert_time
from genetic_algorithm import PATIENTS
from functools import wraps
import calendar
from datetime import datetime, timedelta
from config import config

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random string for production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Use SQLite for simplicity
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
best_schedule = {}
@app.template_filter('timestamp_to_time')
def timestamp_to_time(timestamp):
    hours = timestamp // 60
    minutes = timestamp % 60
    ampm = 'AM' if hours < 12 else 'PM'
    hours = hours % 12
    if hours == 0:
        hours = 12  # Handle midnight and noon
    return f"{hours}:{minutes:02d} {ampm}"

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)

# Role-based access control decorator
def role_required(role):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('You need to log in first.', 'danger')
                return redirect(url_for('login'))
            user = User.query.get(session['user_id'])
            if user.role != role:
                flash('Access denied!', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

# Home route (protected)
@app.route('/')
def home():
    if 'user_id' in session:
        return render_template('home.html')
    return redirect(url_for('login'))

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        new_user = User(username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        Flask('Registration successful! Please log in.', '/success')
        return redirect(url_for('login'))
    return render_template('register.html')


# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and (user.password == password):
            session['user_id'] = user.id
            session['role'] = user.role
            if user.role == 'admin':
                return redirect(url_for('dashboard_admin'))
            elif user.role == 'doctor':
                return redirect(url_for('dashboard_doctor'))

        return 'Invalid credentials. Please try again.'

    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)


    return redirect(url_for('login'))

def convert_time(minutes):
    if type(minutes) == str:
        minutes = int(minutes)

    hours, mins = divmod(minutes, 60)  # Convert minutes to hours and remaining minutes
    time_obj = datetime.strptime(f"{hours:02}:{mins:02}", "%H:%M")
    return time_obj.strftime("%I:%M %p")

def check_queue(PATIENTS):
    for patient in PATIENTS:
        if not patient.get_is_scheduled():  # If any patient is not scheduled, return False
            return False
    return True

@app.route('/admin')
@role_required('admin')
def dashboard_admin():
    config("best_schedule.txt")

    now = datetime.now()
    year = now.year
    month = now.month
    current_day = now.day  # Get the current day
    calendar.setfirstweekday(calendar.SUNDAY)
    # Generate the calendar for the current month
    cal = calendar.monthcalendar(year, month)

    total_days = calendar.monthrange(year, month)[1]

    schedule = {}
    days_until_monday = (7 - now.weekday()) % 7  # Get days until next Monday
    next_monday = now + timedelta(days=days_until_monday)

    # Pass data to the HTML template
    return render_template('dashboard_admin.html', cal=cal, year=year, month=month, current_day=current_day,
                           PATIENTS=PATIENTS,DAYS_OF_WEEK=DAYS_OF_WEEK,schedule=schedule, convert_time=convert_time,
                           total_days=total_days, next_monday=next_monday.day, DOCTOR_SPECIALTIES=DOCTOR_SPECIALTIES,
                           calculate_next_week = calculate_next_week, check_queue=check_queue)


@app.route('/doctor')
@role_required('doctor')
def dashboard_doctor():
    config("best_schedule.txt")

    now = datetime.now()
    year = now.year
    month = now.month
    current_day = now.day  # Get the current day
    calendar.setfirstweekday(calendar.SUNDAY)

    # Generate the calendar for the current month
    cal = calendar.monthcalendar(year, month)

    total_days = calendar.monthrange(year, month)[1]

    schedule = {}

    days_until_monday = (7 - now.weekday()) % 7  # Get days until next Monday
    next_monday = now + timedelta(days=days_until_monday)

    # Pass data to the HTML template
    return render_template('dashboard_doctor.html', cal=cal, year=year, month=month, current_day=current_day,
                           PATIENTS=PATIENTS,DAYS_OF_WEEK=DAYS_OF_WEEK,schedule=schedule, convert_time=convert_time,
                           total_days=total_days, next_monday=next_monday.day, DOCTOR_SPECIALTIES=DOCTOR_SPECIALTIES,
                           calculate_next_week = calculate_next_week, check_queue=check_queue)

def calculate_next_week(next_monday, date):
    test = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    return next_monday + test.index(date)

@app.route('/run_algorithm', methods=['POST'])
def run_algorithm():

    population = initialize_population()
    for generation in range(genetic_algorithm.GENERATIONS):  # Run for 100 generations
        parents = select_parents(population)
        if len(parents) != 2:
            continue
        child = crossover(parents[0], parents[1])
        child = mutate(child)
        population.append(child)

        # Apply elitism to keep the best solutions
        population = elitism(population)

    # After the algorithm runs, return the best schedule
    best_schedule = max(population, key=evaluate_fitness)
    #This returns a dictionary of patients with a tuple value of (Doctor, Day, Time, and Duration)


    now = datetime.now()
    year = now.year
    month = now.month
    current_day = now.day  # Get the current day

    # Set Monday as the first day of the week
    calendar.setfirstweekday(calendar.SUNDAY)

    # Generate the calendar for the current month
    cal = calendar.monthcalendar(year, month)
    current_date = datetime.now()
    days_until_monday = (7 - current_date.weekday()) % 7  # Get days until next Monday
    next_monday = current_date + timedelta(days=days_until_monday)


    sorted_schedule = sorted(best_schedule.items(), key=lambda item: item[1][2])
    print(best_schedule)
    for patient in PATIENTS:
        print(patient.get_is_scheduled())

    dates = []
    test = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    for patient, (doctor, day, time, duration) in best_schedule.items():
        dates.append(str(month) + "/" + str(test.index(day) + next_monday.day) + "/" + str(year))

    #"ADD SPECIALTY "
    for patient in PATIENTS:
        if not patient.get_is_scheduled():
            # Simulate scheduling the patient
            patient.set_is_scheduled(True)
            print(f"Scheduled patient {patient.get_number()} - {patient.get_specialty()}")

    counter = 0
    with open("best_schedule.txt", "w") as file:
        for patient, (doctor, day, time, duration) in best_schedule.items():
            if patient.get_is_scheduled():
                file.write(f"{patient.get_number()}\t{patient.get_specialty()}\t{doctor}\t{day}\t{time}\t{duration}\t{dates[counter]}\n")
                counter += 1




    # Pass data to the HTML template
    return render_template('dashboard_admin.html', cal=cal, year=year, month=month, current_day=current_day,
                           DOCTOR_SPECIALTIES=DOCTOR_SPECIALTIES, DAYS_OF_WEEK=DAYS_OF_WEEK, convert_time=convert_time, schedule=sorted_schedule, next_monday=next_monday.day,
                           calculate_next_week=calculate_next_week,
                           PATIENTS=PATIENTS,check_queue=check_queue)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create local database if it doesn't exist
    app.run(debug=True)


