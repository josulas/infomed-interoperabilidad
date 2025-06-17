"""
Módulo para crear un recurso FHIR de paciente con parámetros opcionales.
"""


from fhir.resources.patient import Patient
from fhir.resources.humanname import HumanName
from fhir.resources.contactpoint import ContactPoint


# Crear el recurso FHIR de paciente con parámetros opcionales
def create_patient_resource(family_name: str| None = None,
                            given_name: str | None = None,
                            birth_date: str | None = None,
                            gender: str | None = None,
                            phone: str | None =None) -> Patient:
    """
    Crea un recurso FHIR de paciente con los parámetros proporcionados.
    :param family_name: Apellido del paciente (opcional).
    :param given_name: Nombre del paciente (opcional).
    :param birth_date: Fecha de nacimiento del paciente (opcional
    :param gender: Género del paciente (opcional).
    :param phone: Número de teléfono del paciente (opcional).
    :return: Un recurso FHIR de tipo Patient.
    """
    patient = Patient()
    # Agregar el nombre del paciente si está disponible
    if family_name or given_name:
        name = HumanName()
        if family_name:
            name.family = family_name
        if given_name:
            name.given = [given_name]
    # Agregar la fecha de nacimiento si está disponible
    if birth_date:
        patient.birthDate = birth_date
    # Agregar el género si está disponible
    if gender:
        patient.gender = gender

    # Agregar información de contacto si está disponible
    if phone:
        contact = ContactPoint()
        contact.system = "phone"
        contact.value = phone
        contact.use = "mobile"
        patient.telecom = [contact]

    return patient
