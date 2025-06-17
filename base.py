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


def edit_resource_in_hapi_fhir(resource: Resource) -> bool:
    """
    Edita un recurso FHIR existente en el servidor HAPI FHIR.
    :param resource: Un recurso FHIR que hereda de Resource con el ID del recurso a editar.
    :return: True si el recurso fue editado exitosamente, False en caso contrario.
    """
    resource_type = resource.get_resource_type()
    resource_id = resource.id
    url = f"http://hapi.fhir.org/baseR4/{resource_type}/{resource_id}"
    headers = {"Content-Type": "application/fhir+json"}
    resource_json = resource.model_dump_json()
    response = requests.put(url,
                            headers=headers,
                            data=resource_json,
                            timeout=10)
    if response.status_code == 200:
        print("Recurso editado exitosamente")
        return True
    else:
        print(f"Error al editar el recurso: {response.status_code}")
        print(response.json())
        return False


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


def get_coverage_by_beneficiary(beneficiary_resource_type: str,
                                beneficiary_resource_id: str) -> list[Coverage]:
    """
    Busca recursos Coverage por el beneficiario en el servidor HAPI FHIR.
    :param beneficiary_resource_type: El tipo de recurso del beneficiario (ejemplo: 'Patient').
    :param beneficiary_resource_id: El ID del recurso del beneficiario.
    :return: Lista de recursos Coverage encontrados.
    """
    url = f"http://hapi.fhir.org/baseR4/Coverage?beneficiary={beneficiary_resource_type}/{beneficiary_resource_id}&_summary=false&_elements=*"
    response = requests.get(url,
                            headers={"Accept": "application/fhir+json"},
                            timeout=10)
    if response.status_code == 200:
        resources = response.json().get('entry', [])
        if resources:
            resources_list = []
            for entry in resources:
                try:
                    resource = entry['resource']
                    if "kind" not in resource:
                        resource['kind'] = 'insurance'
                    coverage = Coverage.model_validate(entry['resource'])
                    resources_list.append(coverage)
                except Exception as e:
                    continue
            return resources_list
        else:
            print("No se encontraron recursos Coverage para el beneficiario.")
            return []
    else:
        print(f"Error al buscar los recursos Coverage: {response.status_code}")
        print(response.json())
        return []


def delete_resource_from_hapi_fhir(resource_id: str,
                                  resource_type: str) -> bool:
    """
    Elimina un recurso FHIR del servidor HAPI FHIR por su ID.
    :param resource_id: El ID del recurso a eliminar.
    :param resource_type: El tipo de recurso (ejemplo: 'Patient', 'Observation').
    :return: True si el recurso fue eliminado exitosamente, False en caso contrario.
    """
    url = f"http://hapi.fhir.org/baseR4/{resource_type}/{resource_id}"
    response = requests.delete(url, timeout=10)
    if response.status_code == 200:
        print("Recurso eliminado exitosamente")
        return True
    else:
        print(f"Error al eliminar el recurso: {response.status_code}")
        print(response.json())
        return False
