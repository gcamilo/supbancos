import os
from datetime import datetime

from dateutil.relativedelta import relativedelta
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://apis.sb.gob.do/estadisticas/v2"
RATE_XML_URL = "https://cdn.bancentral.gov.do/documents/nsdp/documents/INR_DR.xml"


class SBAPIError(Exception):
    """Exception for errors returned by the Superintendencia API."""
    pass


def get_eif_for_period(periodo, registros=1000, entidades=None, tipo_entidades=None):
    """
    Fetch the Estado de Situación EIF for a given YYYY-MM period.

    Returns a list of records or raises SBAPIError on failure.
    """
    key = os.getenv("SB_API_KEY")
    if not key:
        raise SBAPIError("SB_API_KEY environment variable is not set")
    url = f"{BASE_URL}/estados/situacion/eif"
    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "User-Agent": "Mozilla/5.0"
    }
    params = {
        "periodoInicial": periodo,
        "periodoFinal": periodo,
        "registros": registros,
    }
    if entidades:
        params["entidad"] = entidades
    if tipo_entidades:
        params["tipoEntidad"] = tipo_entidades
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code != 200:
        raise SBAPIError(f"Error fetching data: {resp.status_code} {resp.text}")
    return resp.json()


def find_latest_period(max_months_back=12, start_date=None):
    """
    Identify and fetch the most recent available period.

    Attempts up to max_months_back from start_date (defaults to now).
    Returns a tuple (periodo, data_list).
    """
    start_date = start_date or datetime.now()
    # Determine tipoEntidad filter: override via SB_TIPO_ENTIDADES or auto-discover
    env_tipos = os.getenv("SB_TIPO_ENTIDADES")
    if env_tipos:
        tipo_list = [t.strip() for t in env_tipos.split(",") if t.strip()]
    else:
        # Auto-discover all tipoEntidad values for the starting period
        periodo0 = start_date.strftime("%Y-%m")
        tipo_list = get_tipo_entidades_for_period(periodo0)

    for i in range(max_months_back):
        periodo = (start_date - relativedelta(months=i)).strftime("%Y-%m")
        data = get_eif_for_period(periodo, tipo_entidades=tipo_list)
        if data:
            return periodo, data
    raise SBAPIError(f"No data found in the last {max_months_back} months")


def get_entities_for_period(periodo, registros=1000):
    """
    Fetch the Detalle de Entidades (access details) for a given YYYY-MM period.

    Returns a sorted list of unique entity short names, or raises SBAPIError.
    """
    # Allow override of entities via environment variable (comma-separated)
    env_list = os.getenv("SB_ENTIDADES")
    if env_list:
        return sorted([e.strip() for e in env_list.split(",") if e.strip()])
    key = os.getenv("SB_API_KEY")
    if not key:
        raise SBAPIError("SB_API_KEY environment variable is not set")
    url = f"{BASE_URL}/detalle-entidades/acceso"
    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "User-Agent": "Mozilla/5.0"
    }
    params = {
        "periodoInicial": periodo,
        "periodoFinal": periodo,
        "registros": registros,
    }
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code != 200:
        raise SBAPIError(f"Error fetching entities: {resp.status_code} {resp.text}")
    data = resp.json()
    entities = sorted({item.get("entidad") for item in data if "entidad" in item})
    return entities

def get_tipo_entidades_for_period(periodo, registros=1000):
    """
    Fetch distinct tipoEntidad values for a given YYYY-MM period.

    Returns a sorted list of unique tipoEntidad strings or raises SBAPIError.
    """
    key = os.getenv("SB_API_KEY")
    if not key:
        raise SBAPIError("SB_API_KEY environment variable is not set")
    url = f"{BASE_URL}/detalle-entidades/acceso"
    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "User-Agent": "Mozilla/5.0"
    }
    params = {
        "periodoInicial": periodo,
        "periodoFinal": periodo,
        "registros": registros,
    }
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code != 200:
        raise SBAPIError(f"Error fetching tipoEntidad list: {resp.status_code} {resp.text}")
    data = resp.json()
    tipos = sorted({item.get("tipoEntidad") for item in data if item.get("tipoEntidad")})
    return tipos


def find_latest_period_for_all_entities(max_months_back=12, start_date=None):
    """
    Identify the most recent YYYY-MM period for which all entities have
    reported Estado de Situación EIF data. Returns a tuple of
    (periodo, entities_list, data_list).
    """
    start_date = start_date or datetime.now()
    for i in range(max_months_back):
        periodo = (start_date - relativedelta(months=i)).strftime("%Y-%m")
        entities = get_entities_for_period(periodo)
        if not entities:
            continue
        data = get_eif_for_period(periodo, registros=1000, entidades=entities)
        reported = {item.get("entidad") for item in data if "entidad" in item}
        if set(entities) <= reported:
            return periodo, entities, data
    raise SBAPIError(f"No common data found in the last {max_months_back} months")


def get_principales(periodo_inicial, periodo_final=None, registros=100):
    """
    Fetch principal system indicators (incl. tasaActiva, tasaPasiva) for a range of periods.

    Returns a list of records (one per periodo) or raises SBAPIError on failure.
    """
    key = os.getenv("SB_API_KEY")
    if not key:
        raise SBAPIError("SB_API_KEY environment variable is not set")
    url = f"{BASE_URL}/indicadores/principales"
    headers = {"Ocp-Apim-Subscription-Key": key, "User-Agent": "Mozilla/5.0"}
    params = {"periodoInicial": periodo_inicial, "registros": registros}
    if periodo_final:
        params["periodoFinal"] = periodo_final
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code != 200:
        raise SBAPIError(f"Error fetching principal indicators: {resp.status_code} {resp.text}")
    return resp.json()


def get_rate_series_xml(indicator: str) -> dict[str, float]:
    """
    Fetch and parse the INR_DR.xml from the Central Bank,
    extracting the time series for the given INDICATOR code.
    Returns a dict mapping YYYY-MM to rate values (floats).
    """
    resp = requests.get(RATE_XML_URL)
    if resp.status_code != 200:
        raise SBAPIError(f"Error fetching rate XML: {resp.status_code}")
    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as e:
        raise SBAPIError(f"Error parsing rate XML: {e}")
    series_elem = None
    for elem in root.findall(".//{*}Series"):
        if elem.attrib.get("INDICATOR") == indicator:
            series_elem = elem
            break
    if series_elem is None:
        raise SBAPIError(f"No series found for indicator {indicator}")
    rates = {}
    for obs in series_elem.findall(".//{*}Obs"):
        periodo = obs.attrib.get("TIME_PERIOD")
        val = obs.attrib.get("OBS_VALUE")
        try:
            rates[periodo] = float(val)
        except (TypeError, ValueError):
            continue
    return rates