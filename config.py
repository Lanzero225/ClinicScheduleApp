from genetic_algorithm import PATIENTS, Patient
def config(file_info):
    with open(file_info, "r") as file:
        for line in file:
            # Split each line into components
            parts = line.strip().split("\t")

            # Extract patient, doctor, day, time, duration, and date from each line
            patient_number = int(parts[0])
            specialty = parts[1]
            doctor = parts[2]
            day = parts[3]
            time = int(parts[4])
            duration = int(parts[5])
            date = parts[6]

            if any(patient.get_number() == patient_number for patient in PATIENTS):
                continue

            PATIENTS.append(Patient(patient_number, specialty, doctor, day, time, duration, date, True))
            # Assuming you want to store the data in a dictionary like structure
