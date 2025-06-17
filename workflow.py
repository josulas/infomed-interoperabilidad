"""
Módulo para gestionar el flujo de trabajo de creación y obtención de recursos FHIR de pacientes.
"""


from datetime import datetime
import re

from fhir.resources.patient import Patient
from fhir.resources.coverage import Coverage
from fhir.resources.identifier import Identifier

from patient import create_patient_resource
from base import (send_resource_to_hapi_fhir,
                  get_resource_from_hapi_fhir,
                  get_resource_by_identifier,
                  edit_resource_in_hapi_fhir,
                  get_coverage_by_beneficiary,
                  delete_resource_from_hapi_fhir)
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
def create_or_edit_patient() -> None:
    """
    Crea o edita un recurso FHIR de paciente y lo envía al servidor HAPI FHIR.
    :return: El ID del paciente creado o None si hubo un error.
    """
    patient_dni = input_dni()
    # Verificar si el paciente ya existe
    existing_resources = get_resource_by_identifier(patient_dni, Patient.get_resource_type())
    if existing_resources:
        print(f"Ya existe un paciente con DNI {patient_dni}.")
        input_choice = input("¿Desea editar el paciente existente? (s/n): ").strip().lower()
        if input_choice != 's':
            print("Operación cancelada.")
            return
    if existing_resources[0].id is None:
        print(f"El paciente con DNI {patient_dni} no tiene un ID válido. No se puede editar.")
        return
    # Ingresamos los datos del paciente
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
    # Si el paciente ya existe, editamos el recurso
    if existing_resources:
        patient_resource.id = existing_resources[0].id
        print(f"Editando el paciente con DNI {patient_dni}...")
        if not edit_resource_in_hapi_fhir(patient_resource):
            print("Error al editar el paciente")
        else:
            print("Paciente editado exitosamente")
            print("Detalles del paciente:")
            resource = get_resource_from_hapi_fhir(patient_resource.id, Patient.get_resource_type())
            for key, value in resource.items():
                print(f"{key}: {value}")
    else:
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


def input_coverage_status() -> str:
    """
    Solicita al usuario que ingrese el estado de la cobertura.
    :return: El estado de la cobertura ingresado por el usuario.
    """
    options = {
        "1": "active",
        "2": "cancelled",
        "3": "draft",
        "4": "entered-in-error"
    }
    print("\nSeleccione el estado de la cobertura:")
    for key, value in options.items():
        print(f"{key}. {value}")
    while True:
        choice = input("Ingrese su opción (1-4): ").strip()
        if choice in options:
            return options[choice]
        else:
            print("Opción inválida. Debe ser 1, 2, 3 o 4.")


# Punto B
def search_patient_by_dni() -> None:
    """
    Busca un paciente por su DNI en el servidor HAPI FHIR.
    :param dni: El DNI del paciente a buscar.
    """
    search_dni = input_dni()
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
def add_or_edit_patient_coverages() -> None:
    """
    Agrega cobertura a un paciente existente.
    """
    patient_dni = input_dni()
    patient_resources = get_resource_by_identifier(patient_dni, Patient.get_resource_type())
    if not patient_resources:
        print(f"No se encontró el paciente con DNI {patient_dni}.")
        return
    patient_resource = patient_resources[0]
    patient_id = patient_resource.id
    if not patient_id:
        print(f"Error: El paciente con DNI {patient_dni} no tiene un ID válido.")
        return
    # Primero buscamos si hay una cobertura existente para este paciente
    coverage_resources = get_coverage_by_beneficiary(
        beneficiary_resource_type=Patient.get_resource_type(),
        beneficiary_resource_id=patient_id
    )
    edited_coverage_id: str | None = None
    if coverage_resources:
        print(f"El paciente con DNI {patient_dni} ya tiene cobertura(s) existente(s):")
        for coverage in coverage_resources:
            for key, value in coverage.model_dump().items():
                print(f"{key}: {value}")
        options = {
            str(i + 1): coverage.id for i, coverage in enumerate(coverage_resources)
        }
        for key, value in options.items():
            print(f"{key}. ID de cobertura: {value}")
        print("Seleccione una cobertura para editar o presione Enter para agregar una nueva:")
        done = False
        while not done:
            choice = input(f"Ingrese su opción (1-{len(options)}): ").strip()
            if choice in options:
                edited_coverage_id = options[choice]
                print(f"Editando la cobertura con ID {edited_coverage_id}...")
                done = True
            elif choice == "":
                print("Agregando nueva cobertura...")
                done = True
            else:
                print(f"Opción inválida. Debe ser un número entre 1 y {len(options)} o presione Enter.")
    if edited_coverage_id:
        # Editar o eliminar la cobertura existente
        delete_choice = input("¿Desea eliminar la cobertura existente? (s/n): ").strip().lower()
        if delete_choice == 's':
            if delete_resource_from_hapi_fhir(edited_coverage_id, Coverage.get_resource_type()):
                print("Cobertura eliminada exitosamente.")
            else:
                print("Error al eliminar la cobertura.")
            return
    coverage_type, coverage_type_display = input_coverage_type()
    coverage_status = input_coverage_status()
    policy_identifier = input_policy_identifier()
    subscriber_id = input_subscriber_id()
    start_date = input_date("Ingrese la fecha de inicio de la cobertura")
    end_date = input_date("Ingrese la fecha de fin de la cobertura")
    # Crear el recurso de cobertura referenciando al paciente
    coverage_resource = create_coverage_resource(
        beneficiary_resource_type=Patient.get_resource_type(),
        beneficiary_resource_id=patient_id,
        coverage_type=coverage_type,
        status=coverage_status,
        kind="insurance",
        policy_identifier=policy_identifier,
        coverage_type_display=coverage_type_display,
        subscriber_id=subscriber_id,
        start_date=start_date,
        end_date=end_date,
    )
    if edited_coverage_id:
        # Si se está editando una cobertura existente, asignamos el ID
        coverage_resource.id = edited_coverage_id
        print(f"Editando la cobertura con ID {edited_coverage_id}...")
        if not edit_resource_in_hapi_fhir(coverage_resource):
            print("Error al editar la cobertura")
        else:
            print("Cobertura editada exitosamente")
            print("Detalles de la cobertura:")
            resource = get_resource_from_hapi_fhir(coverage_resource.id, Coverage.get_resource_type())
            for key, value in resource.items():
                print(f"{key}: {value}")
    else:
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


def show_patient_coverages() -> None:
    """
    Muestra las coberturas asociadas a un paciente dado su ID.
    :param patient_id: El ID del paciente.
    """
    patient_dni = input_dni()
    patient_resources = get_resource_by_identifier(patient_dni, Patient.get_resource_type())
    if not patient_resources:
        print(f"No se encontró el paciente con DNI {patient_dni}.")
        return
    patient_resource = patient_resources[0]
    patient_id = patient_resource.id
    if not patient_id:
        print(f"Error: El paciente con DNI {patient_dni} no tiene un ID válido.")
        return
    coverage_resources = get_coverage_by_beneficiary(
        beneficiary_resource_type=Patient.get_resource_type(),
        beneficiary_resource_id=patient_id
    )
    if not coverage_resources:
        print(f"No se encontraron coberturas para el paciente con DNI {patient_dni}.")
    else:
        print(f"Coberturas encontradas para el paciente con DNI {patient_dni}:")
        for coverage in coverage_resources:
            for key, value in coverage.model_dump().items():
                print(f"{key}: {value}")


def main():
    """
    Función principal que gestiona el flujo de trabajo de creación y obtención de recursos FHIR.
    """
    print("Bienvenido al sistema de gestión de pacientes FHIR")
    while True:
        print("\nSeleccione una opción:")
        print("1. Crear o editar paciente")
        print("2. Buscar paciente por DNI")
        print("3. Agregar o editar las coberturas de un paciente")
        print("4. Mostrar coberturas de un paciente")
        print("5. Salir")
        choice = input("Ingrese su opción (1-5): ").strip()
        if choice == "1":
            create_or_edit_patient()
        elif choice == "2":
            search_patient_by_dni()
        elif choice == "3":
            add_or_edit_patient_coverages()
        elif choice == "4":
            show_patient_coverages()
        elif choice == "5":
            print("Saliendo del sistema...")
            break
        else:
            print("Opción inválida. Inténtelo de nuevo.")


if __name__ == "__main__":
    main()
