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


def get_eif_for_period(periodo, registros=1000):
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
    for i in range(max_months_back):
        periodo = (start_date - relativedelta(months=i)).strftime("%Y-%m")
        data = get_eif_for_period(periodo)
        if data:
            return periodo, data
    raise SBAPIError(f"No data found in the last {max_months_back} months")