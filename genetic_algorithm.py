# genetic_algorithm.py

import random



class Doctor:
    def __init__(self, name, specialty):
        self.name = name
        self.specialty = specialty


class Patient:
    def __init__(self, number, specialty, doctor = None, day = None, time = None, duration = None, date = None, is_scheduled=False):
        self.number = number
        self.specialty = specialty
        self.is_scheduled = is_scheduled
        if doctor and date and day and time and duration:
            self.date = date
            self.doctor = doctor
            self.day = day
            self.time = time
            self.duration = duration

    def get_day(self):
        return self.day
    def set_day(self, day):
        self.day = day

    def get_time(self):
        return self.time
    def set_time(self, time):
        self.time = time
    def get_duration(self):
        return self.duration
    def set_duration(self, duration):
        self.duration = duration

    def get_number(self):
        return self.number
    def get_doctor(self):
        return self.doctor
    def set_doctor(self, doctor):
        self.doctor = doctor
    def get_specialty(self):
        return self.specialty

    def get_is_scheduled(self):
        return self.is_scheduled

    def set_is_scheduled(self, is_scheduled):
        self.is_scheduled = is_scheduled

    def get_date(self):
        return self.date
    def set_date(self, date):
        self.date = date


#DYNAMIC
DOCTORS = ["Dr. Smith", "Dr. Johnson", "Dr. Lee"]
PATIENTS = []
TIME_SLOTS = [540, 600, 660, 780, 840, 900]  # Representing 9:00 AM, 10:00 AM, etc., as minutes
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
DOCTOR_PREFERENCES = {
    "Dr. Smith": ["9AM", "10AM"],
    "Dr. Johnson": ["1PM", "2PM"],
    "Dr. Lee": ["11AM", "3PM"]
}

DOCTOR_AVAILABILITY = {
    "Dr. Smith": {
        "Monday": [540, 600],
        "Tuesday": [540, 600],
        "Wednesday": [540, 600],
        "Thursday": [540, 600],
        "Friday": [540, 600]
    },
    "Dr. Johnson": {
        "Monday": [780, 840],  # 1:00 PM is 780, 2:00 PM is 840
        "Tuesday": [780, 840],
        "Wednesday": [780, 840],
        "Thursday": [780, 840],
        "Friday": [780, 840]
    },
    "Dr. Lee": {
        "Monday": [660, 900],  # 11:00 AM is 660, 3:00 PM is 900
        "Tuesday": [660, 900],
        "Wednesday": [660, 900],
        "Thursday": [660, 900],
        "Friday": [660, 900]
    }
}

APPOINTMENT_DURATION = {
    "Dr. Smith": 30,
    "Dr. Johnson": 45,
    "Dr. Lee": 30
}
DOCTOR_SPECIALTIES = {
    "Dr. Smith": "General Medicine",
    "Dr. Johnson": "Cardiology",
    "Dr. Lee": "OBGYN"
}



# Genetic Algorithm Parameters
POPULATION_SIZE = 20
MUTATION_RATE = 0.1
GENERATIONS = 100000

def check_conflict(schedule, doctor, day, time):
    # Loop through all existing appointments to check for time conflicts
    for patient, (assigned_doctor, assigned_day, assigned_time, _) in schedule.items():
        if assigned_doctor == doctor and assigned_day == day and assigned_time == time:
            return True  # Conflict found (double-booking)
    return False  # No conflict

def generate_schedule():
    schedule = {}
    for patient in PATIENTS:
        required_specialty = patient.get_specialty()
        available_doctors = [doctor for doctor, specialty in DOCTOR_SPECIALTIES.items() if
                             specialty == required_specialty]

        doctor = random.choice(available_doctors)
        day = random.choice(DAYS_OF_WEEK)


        available_slots = DOCTOR_AVAILABILITY[doctor][day]
        time_slot = random.choice(available_slots)  # Select a time in integer (e.g., 540)
        duration = APPOINTMENT_DURATION[doctor]
        if check_conflict(schedule, doctor, day, time_slot):
            continue

        schedule[patient] = (doctor, day, time_slot, duration)

    return schedule

def initialize_population():
    return [generate_schedule() for _ in range(POPULATION_SIZE)]

def evaluate_fitness(schedule: dict):
    score = 0
    doctor_schedule = {doc: {day: [] for day in DAYS_OF_WEEK} for doc in DOCTORS}

    for patient, (doctor, day, time, duration) in schedule.items():
        # Penalty for double-booking a doctor at the same time

        if time in doctor_schedule[doctor][day]:
            score -= 5  # A strong penalty for double-booking
        else:
            doctor_schedule[doctor][day].append(time)
            # Reward for preferences (if time is preferred for the doctor)
            if time in DOCTOR_AVAILABILITY[doctor][day]:
                score += 1
            # Reward for unique time slots
            score += 1

    return score

def select_parents(population):
    sorted_population = sorted(population, key=evaluate_fitness, reverse=True)
    return sorted_population[:2]

def crossover(parent1, parent2):
    child = {}
    doctor_schedule = {doc: {day: [] for day in DAYS_OF_WEEK} for doc in DOCTORS}

    for patient in PATIENTS:
        if patient in parent1 and patient in parent2:
            # If the patient exists in both parents, choose randomly
            if random.random() > 0.5:
                doctor, day, time, duration = parent1[patient]
            else:
                doctor, day, time, duration = parent2[patient]
        elif patient in parent1:
            # If the patient only exists in parent1, use their data
            doctor, day, time, duration = parent1[patient]
        else:
            # If the patient only exists in parent2, use their data
            doctor, day, time, duration = parent2[patient]

        if check_conflict(child, doctor, day, time):
            available_slots = DOCTOR_AVAILABILITY[doctor][day]
            time_slot = random.choice(available_slots)
            child[patient] = (doctor, day, time_slot, duration)
        else:
            child[patient] = (doctor, day, time, duration)
            doctor_schedule[doctor][day].append(time)

    return child


def mutate(schedule):
    if random.random() < MUTATION_RATE:
        patient = random.choice(PATIENTS)
        required_specialty = patient.get_specialty
        available_doctors = [doctor for doctor, specialty in DOCTOR_SPECIALTIES.items() if
                             specialty == required_specialty]

        if not available_doctors:
            return schedule  # No available doctors for mutation

        doctor = random.choice(available_doctors)
        day = random.choice(DAYS_OF_WEEK)
        if day in ["Saturday", "Sunday"]:
            return schedule
        available_slots = DOCTOR_AVAILABILITY[doctor][day]
        time_slot = random.choice(available_slots)
        duration = APPOINTMENT_DURATION[doctor]

        schedule[patient] = (doctor, day, time_slot, duration)

        doctor_schedule = {doc: {day: [] for day in DAYS_OF_WEEK} for doc in DOCTORS}
        for patient, (doctor, day, time, _) in schedule.items():
            if time in doctor_schedule[doctor][day]:
                schedule[patient] = (doctor, day, random.choice(available_slots), duration)

    return schedule


def elitism(population):
    sorted_population = sorted(population, key=evaluate_fitness, reverse=True)
    top_5_percent = sorted_population[:int(0.05 * len(sorted_population))]
    return top_5_percent

def convert_time(minutes):
    hours = minutes // 60
    minutes = minutes % 60
    am_pm = "AM" if hours < 12 else "PM"
    if hours > 12:
        hours -= 12  # Convert to 12-hour format
    elif hours == 0:
        hours = 12  # Midnight is 12:00 AM
    return f"{hours}:{str(minutes).zfill(2)} {am_pm}"
