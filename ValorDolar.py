import json
import bcchapi
from datetime import date


def valor_dolar():
    try:
        with open("secrets.json", "r", encoding="utf-8") as credentials:
            data = json.load(credentials)
            user = data["USER"]
            password = data["PASSWORD"]
        siete = bcchapi.Siete(user, password)
        response = siete.get('F073.TCO.PRE.Z.D', first_date=str(date.today()))
        tipo_cambio = float(response.Series['Obs'][-1]['value'])
        return tipo_cambio
    except Exception as e:
        raise e
