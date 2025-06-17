"""
Módulo para crear un recurso FHIR Coverage.
"""


from typing import Optional

from fhir.resources.coverage import Coverage
from fhir.resources.reference import Reference
from fhir.resources.identifier import Identifier
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.period import Period


def create_coverage_resource(
    coverage_type: str,
    beneficiary_resource_type: str,
    beneficiary_resource_id: str,
    status: str = "active",
    kind: str = "insurance",
    policy_identifier: Optional[str] = None,
    coverage_type_display: Optional[str] = None,
    subscriber_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Coverage:
    """
    Crea un recurso FHIR Coverage con los parámetros proporcionados.
    :param coverage_type: Tipo de cobertura (ejemplo: 'health', 'dental').
    :param beneficiary_resource_type: Tipo de recurso del beneficiario (ejemplo: 'Patient').
    :param beneficiary_resource_id: ID del recurso del beneficiario.
    :param status: Estado de la cobertura (ejemplo: 'active', 'inactive').
    :param kind: Tipo de cobertura (ejemplo: 'insurance', 'self-paid').
    :param policy_identifier: Identificador de la póliza de seguro.
    :param coverage_type_display: Descripción del tipo de cobertura.
    :param subscriber_id: ID del suscriptor de la póliza.
    :param start_date: Fecha de inicio de la cobertura (formato ISO 8601).
    :param end_date: Fecha de finalización de la cobertura (formato ISO 8601).
    :return: Un recurso FHIR de tipo Coverage.
    """
    type_concept = CodeableConcept()
    coding = Coding()
    coding.system = "http://terminology.hl7.org/CodeSystem/v3-ActCode"
    coding.code = coverage_type
    if coverage_type_display:
        coding.display = coverage_type_display
    type_concept.coding = [coding]
    beneficiary_ref = Reference()
    beneficiary_ref.reference = f"{beneficiary_resource_type}/{beneficiary_resource_id}"
    coverage = Coverage(
        status=status,
        kind=kind,
        type=type_concept,
        beneficiary=beneficiary_ref
        )
    # Agregar identificador de póliza si está disponible
    if policy_identifier:
        identifier = Identifier()
        identifier.system = "http://example.org/policy-numbers"
        identifier.value = policy_identifier
        coverage.identifier = [identifier]
    # Agregar ID del suscriptor si está disponible
    if subscriber_id:
        coverage.subscriberId = [subscriber_id]
    # Agregar período de validez si las fechas están disponibles
    if start_date or end_date:
        period = Period()
        if start_date:
            period.start = start_date
        if end_date:
            period.end = end_date
        coverage.period = period
    return coverage
