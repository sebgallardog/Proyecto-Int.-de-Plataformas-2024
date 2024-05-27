import json
import requests
from datetime import date, datetime


class ValorDolar:
    """
    Se requiere un archivo .json en la misma carpeta nombrado como 'secrets.json' que contenga un correo
    y contraseña válidos para usar la API del banco central.
    {
        "USER": "correo",
        "PASSWORD": "contraseña"
    }
    """

    # Ahora usuario y contraseña no se guardan como atributos dentro del objeto para mayor seguridad
    def __init__(self):
        self.__dia = '2001-01-01'
        self.__valor = self.valor

    def __SerieRequest(self):
        with open("secrets.json", "r", encoding="utf-8") as credentials:
            data = json.load(credentials)
            user = data["USER"]
            password = data["PASSWORD"]
        url = f'https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx?user={user}&pass={password}&firstdate={self.__dia}&timeseries=F073.TCO.PRE.Z.D&function=GetSeries'
        response = requests.get(url)
        data = json.loads(response.text.encode("utf-8"))
        self.__valor = float(data['Series']['Obs'][-1]['value'])

    @property
    def valor(self):
        if date.today() != datetime.strptime(self.__dia, '%Y-%m-%d').date():
            self.__dia = str(date.today())
            self.__SerieRequest()
        return self.__valor


if __name__ == '__main__':
    dolar = ValorDolar()
    print(dolar.valor)
