"""
Módulo para enviar y obtener recursos FHIR desde un servidor HAPI FHIR.
"""

import requests

from fhir.resources.resource import Resource
from fhir.resources.patient import Patient
from fhir.resources.coverage import Coverage


RESOURCE_CLASSES = {
    Patient.get_resource_type(): Patient,
    Coverage.get_resource_type(): Coverage,
}


# Enviar el recurso FHIR al servidor HAPI FHIR
def send_resource_to_hapi_fhir(resource: Resource) -> str | None:
    """
    Envía un recurso FHIR al servidor HAPI FHIR.
    :param resource: Un recurso FHIR que hereda de Resource.
    :return: El ID del recurso creado en el servidor HAPI FHIR o None si hubo un error.
    """
    resource_type = resource.get_resource_type()
    url = f"http://hapi.fhir.org/baseR4/{resource_type}"
    headers = {"Content-Type": "application/fhir+json"}
    resource_json = resource.model_dump_json()
    response = requests.post(url,
                             headers=headers,
                             data=resource_json,
                             timeout=10)
    if response.status_code == 201:
        print("Recurso creado exitosamente")
        # Devolver el ID del recurso creado
        return response.json()['id']
    else:
        print(f"Error al crear el recurso: {response.status_code}")
        print(response.json())
        return None


# Buscar el recurso por ID
def get_resource_from_hapi_fhir(resource_id: str,
                                resource_type: str) -> dict:
    """
    Obtiene un recurso FHIR del servidor HAPI FHIR por su ID.
    :param resource_id: El ID del recurso a buscar.
    :param resource_type: El tipo de recurso (ejemplo: 'Patient', 'Observation').
    :return: True si el recurso fue encontrado y obtenido exitosamente, False en caso contrario.
    """
    url = f"http://hapi.fhir.org/baseR4/{resource_type}/{resource_id}"
    response = requests.get(url,
                            headers={"Accept": "application/fhir+json"},
                            timeout=10)
    # Verificar si la solicitud fue exitosa
    if response.status_code == 200:
        resource = response.json()
        return resource
    else:
        return {}


def get_resource_by_identifier(identifier: str,
                               resource_type: str) -> list[Resource]:
    """
    Busca un recurso FHIR por su identificador en el servidor HAPI FHIR.
    :param identifier: El identificador del recurso a buscar.
    :param resource_type: El tipo de recurso (ejemplo: 'Patient', 'Observation').
    :return: Lista de recursos encontrados.
    """
    resource_class = RESOURCE_CLASSES.get(resource_type, None)
    if not resource_class:
        print(f"Tipo de recurso no soportado: {resource_type}")
        return []
    url = f"http://hapi.fhir.org/baseR4/{resource_type}?identifier={identifier}"
    response = requests.get(url,
                            headers={"Accept": "application/fhir+json"},
                            timeout=10)
    if response.status_code == 200:
        resources = response.json().get('entry', [])
        if resources:
            return [resource_class.model_validate(entry['resource']) for entry in resources]
        else:
            print("No se encontraron recursos con ese identificador.")
            return []
    else:
        print(f"Error al buscar el recurso: {response.status_code}")
        print(response.json())
        return []
