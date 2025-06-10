import os
from datetime import datetime

from dateutil.relativedelta import relativedelta
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://apis.sb.gob.do/estadisticas/v2"


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
    # Allow override of tipoEntidad via environment variable (comma-separated)
    tipo_list = None
    env_tipos = os.getenv("SB_TIPO_ENTIDADES")
    if env_tipos:
        tipo_list = [t.strip() for t in env_tipos.split(",") if t.strip()]
    for i in range(max_months_back):
        periodo = (start_date - relativedelta(months=i)).strftime("%Y-%m")
        if tipo_list:
            data = get_eif_for_period(periodo, tipo_entidades=tipo_list)
        else:
            data = get_eif_for_period(periodo)
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