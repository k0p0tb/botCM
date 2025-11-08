# data.py
from typing import Dict, List, Any

# Хранилище данных в памяти
users = {}
patients_queue = []
active_consultations = {}  # {patient_id: doctor_id}
patient_data = {}  # {patient_id: {messages: [], ...}}

class UserRole:
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"

def add_user(user_id: int, role: str, data: Dict[str, Any]):
    users[user_id] = {"role": role, "data": data}

def get_user(user_id: int):
    return users.get(user_id)

def add_to_queue(patient_id: int):
    if patient_id not in patients_queue:
        patients_queue.append(patient_id)

def get_next_patient():
    if patients_queue:
        return patients_queue.pop(0)
    return None

def start_consultation(patient_id: int, doctor_id: int):
    active_consultations[patient_id] = doctor_id

def end_consultation(patient_id: int):
    if patient_id in active_consultations:
        del active_consultations[patient_id]

def is_in_consultation(user_id: int):
    return user_id in active_consultations or user_id in active_consultations.values()

def get_consultation_partner(user_id: int):
    if user_id in active_consultations:
        return active_consultations[user_id]  # Для пациента возвращает врача
    for patient_id, doctor_id in active_consultations.items():
        if doctor_id == user_id:
            return patient_id  # Для врача возвращает пациента
    return None