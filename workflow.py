"""
Módulo para gestionar el flujo de trabajo de creación y obtención de recursos FHIR de pacientes.
"""


from datetime import datetime
import re

from fhir.resources.patient import Patient
from fhir.resources.coverage import Coverage
from fhir.resources.identifier import Identifier

from patient import create_patient_resource
from base import send_resource_to_hapi_fhir, get_resource_from_hapi_fhir, get_resource_by_identifier
from coverage import create_coverage_resource


def input_dni() -> str:
    """
    Solicita al usuario que ingrese un DNI y lo devuelve.
    :return: El DNI ingresado por el usuario.
    """
    while True:
        dni_input = input("Ingrese el DNI del paciente: ")
        if 7 <= len(dni_input) <= 8 and dni_input.isdigit():
            return dni_input
        else:
            print("DNI inválido. Debe tener 7 u 8 dígitos.")


def input_date(msg: str) -> str | None:
    """
    Solicita al usuario que ingrese una fecha de nacimiento en formato YYYY-MM-DD.
    :param msg: Mensaje a mostrar al usuario para solicitar la fecha.
    :return: La fecha de nacimiento ingresada o None si no se proporciona.
    """
    while True:
        date_input = input(msg + " (YYYY-MM-DD) o presione Enter para omitir: ").strip()
        if not date_input:
            return None
        try:
            datetime.strptime(date_input, "%Y-%m-%d")
            return date_input
        except ValueError:
            print("Fecha inválida. Debe estar en formato YYYY-MM-DD.")


def input_gender() -> str | None:
    """
    Solicita al usuario que ingrese el género del paciente.
    :return: El género ingresado o None si no se proporciona.
    """
    while True:
        gender_input = input("Ingrese el género del paciente (M/F) o" \
        " presione Enter para omitir: ").strip().upper()
        if gender_input in ["M", "F", ""]:
            # Convert to FHIR AdministrativeGender codes
            if gender_input == "M":
                return "male"
            elif gender_input == "F":
                return "female"
            else:
                return None
        print("Género inválido. Debe ser 'M' o 'F'.")


def input_policy_identifier() -> str | None:
    """
    Solicita al usuario que ingrese un número de póliza.
    :return: El número de póliza ingresado o None si no se proporciona.
    """
    policy_input = input("Ingrese el número de póliza (opcional): ").strip()
    return policy_input if policy_input else None


def input_coverage_type() -> tuple[str, str]:
    """
    Solicita al usuario que seleccione el tipo de cobertura.
    :return: Tupla con (código del tipo, descripción del tipo).
    """
    coverage_types = {
        "1": ("EHCPOL", "Extended healthcare policy"),
        "2": ("PUBLICPOL", "Public healthcare policy"),
        "3": ("DENTPRG", "Dental program")
    }
    print("\nSeleccione el tipo de cobertura:")
    print("1. Póliza de salud extendida (EHCPOL)")
    print("2. Seguro médico (PUBLICPOL)")
    print("3. Seguro dental (DENTPRG)")
    while True:
        choice = input("Ingrese su opción (1-3): ").strip()
        if choice in coverage_types:
            return coverage_types[choice]
        else:
            print("Opción inválida. Debe ser 1, 2 o 3.")


def input_phone() -> str | None:
    """
    Solicita al usuario que ingrese un número de teléfono.
    :return: El número de teléfono ingresado o None si no se proporciona.
    """
    phone_input = input("Ingrese el número de teléfono del paciente (opcional): ").strip()
    expression = r"^\+?[1-9]\d{1,14}$"
    if not phone_input or re.match(expression, phone_input):
        return phone_input if phone_input else None
    else:
        print("Número de teléfono inválido. Debe ser un número válido (u omitir).")
        return None


def input_subscriber_id() -> str | None:
    """
    Solicita al usuario que ingrese el ID del suscriptor.
    :return: El ID del suscriptor ingresado o None si no se proporciona.
    """
    subscriber_input = input("Ingrese el ID del suscriptor (opcional): ").strip()
    return subscriber_input if subscriber_input else None


def input_non_void(msg: str) -> str:
    """
    Solicita al usuario que ingrese una string no vacía.
    :param msg: Mensaje a mostrar al usuario.
    :return: La string ingresada por el usuario.
    """
    while True:
        value = input(msg).strip()
        if value:
            return value
        else:
            print("El valor no puede estar vacío. Inténtelo de nuevo.")

# Punto A
def create_patient() -> None:
    """
    Crea un recurso FHIR de paciente y lo envía al servidor HAPI FHIR.
    :return: El ID del paciente creado o None si hubo un error.
    """
    patient_dni = input_dni()
    family_name = input_non_void("Ingrese el apellido del paciente: ")
    given_name = input_non_void("Ingrese el nombre del paciente: ")
    gender = input_gender()
    birth_date = input_date("Ingrese la fecha de nacimiento del paciente")
    phone = input_phone()
    # Crear el recurso de paciente
    patient_resource = create_patient_resource(
        family_name=family_name,
        given_name=given_name,
        birth_date=birth_date,
        gender=gender,
        phone=phone
    )
    dni_identifier = Identifier()
    dni_identifier.system = "http://www.renaper.gob.ar/dni"
    dni_identifier.value = patient_dni
    patient_resource.identifier = [dni_identifier]
    # Enviamos el recurso de paciente al servidor HAPI FHIR
    created_id = send_resource_to_hapi_fhir(patient_resource)
    if not created_id:
        print("Error al crear el paciente")
    else:
        print("Paciente creado exitosamente")
        print("Detalles del paciente:")
        resource = get_resource_from_hapi_fhir(created_id, Patient.get_resource_type())
        for key, value in resource.items():
            print(f"{key}: {value}")


# Punto B
def search_patient_by_dni() -> None:
    """
    Busca un paciente por su DNI en el servidor HAPI FHIR.
    :param dni: El DNI del paciente a buscar.
    """
    search_dni = input_non_void("Ingrese el DNI del paciente a buscar: ")
    resources = get_resource_by_identifier(search_dni, Patient.get_resource_type())
    if not resources:
        print(f"No se encontró el paciente con DNI {search_dni}.")
    elif len(resources) > 1:
        print(f"Se encontraron múltiples pacientes con DNI {search_dni}.")
    else:
        print(f"Paciente encontrado con DNI {search_dni}:")
    for resource in resources:
        for field_name, field_value in resource.model_dump().items():
            print(f"{field_name}: {field_value}")


# Punto C
def add_patient_coverage():
    """
    Agrega cobertura a un paciente existente.
    """
    patient_dni = input_non_void("Ingrese el DNI del paciente para agregar cobertura: ")
    patient_resources = get_resource_by_identifier(patient_dni, Patient.get_resource_type())
    if not patient_resources:
        print(f"No se encontró el paciente con DNI {patient_dni}.")
        return
    patient_resource = patient_resources[0]
    patient_id = patient_resource.id
    if not patient_id:
        print(f"Error: El paciente con DNI {patient_dni} no tiene un ID válido.")
        return
    print(f"Paciente con DNI {patient_dni} encontrado. Puede proceder a agregar cobertura.")
    coverage_type, coverage_type_display = input_coverage_type()
    policy_identifier = input_policy_identifier()
    subscriber_id = input_subscriber_id()
    start_date = input_date("Ingrese la fecha de inicio de la cobertura")
    end_date = input_date("Ingrese la fecha de fin de la cobertura")
    # Crear el recurso de cobertura referenciando al paciente
    coverage_resource = create_coverage_resource(
        beneficiary_resource_type="Patient",
        beneficiary_resource_id=patient_id,
        coverage_type=coverage_type,
        status="active",
        policy_identifier=policy_identifier,
        coverage_type_display=coverage_type_display,
        subscriber_id=subscriber_id,
        start_date=start_date,
        end_date=end_date,
    )
    # Enviamos el recurso de cobertura al servidor HAPI FHIR
    created_id = send_resource_to_hapi_fhir(coverage_resource)
    # Leemos el recurso de cobertura del servidor HAPI FHIR
    if not created_id:
        print("Error al crear la cobertura")
    else:
        print("Cobertura creada exitosamente")
        print("Detalles de la cobertura:")
        resource = get_resource_from_hapi_fhir(created_id, Coverage.get_resource_type())
        for key, value in resource.items():
            print(f"{key}: {value}")


def main():
    """
    Función principal que gestiona el flujo de trabajo de creación y obtención de recursos FHIR.
    """
    print("Bienvenido al sistema de gestión de pacientes FHIR")
    while True:
        print("\nSeleccione una opción:")
        print("1. Crear paciente")
        print("2. Buscar paciente por DNI")
        print("3. Agregar cobertura a un paciente")
        print("4. Salir")
        choice = input("Ingrese su opción (1-4): ").strip()
        if choice == "1":
            create_patient()
        elif choice == "2":
            search_patient_by_dni()
        elif choice == "3":
            add_patient_coverage()
        elif choice == "4":
            print("Saliendo del sistema...")
            break
        else:
            print("Opción inválida. Inténtelo de nuevo.")


if __name__ == "__main__":
    main()
