from app import app
from config import mysql
from flask import jsonify, flash, request, render_template, redirect
from ValorDolar import valor_dolar

"""
OJO: El nombre de las tablas en las queries va siempre en minúscula
"""


@app.route('/', methods=['GET'])
def home():
    """Esto es sólo para realizar las pruebas"""
    return render_template('form.html')


@app.route('/create/<idCategoria>/<Producto>/<Marca>/<Stock>', methods=['POST'])
def create_producto(idCategoria, Producto, Marca, Stock):
    try:
        conn = mysql.connect
        cursor = conn.cursor()
        sqlQuery = """INSERT INTO producto(idProducto, idCategoria, Producto, Marca, Stock) VALUES(DEFAULT, %s, %s, %s, %s)"""
        bindData = (idCategoria, Producto, Marca, Stock)
        cursor.execute(sqlQuery, bindData)
        conn.commit()
        response = jsonify('Producto agregado exitosamente')
        response.status_code = 200
        cursor.close()
        conn.close()
        return response
    except Exception as e:
        print(e)


@app.route('/listado_productos')
def productos():
    """
    Devuelve en una respond con un JSON con los datos de todos los productos en la DB.
    Cada elemento dentro del json es un diccionario con los siguientes datos de un producto:

        Categoria: string, nombre de la categoría del producto.
        idProducto: int, PK del producto.
        Producto: string, nombre del producto.
        Marca: string, nombre de la marca del producto.
        Stock: int, stock del producto.
        PrecioUSD: float, valor del producto en dólares estadounidenses.
        PrecioCLP: int, valor del producto en pesos chilenos.
    """
    try:
        dolar = valor_dolar()
        conn = mysql.connect
        cursor = conn.cursor()
        cursor.execute(
            "SELECT "
            "cat.Categoria, "
            "pro.idProducto, "
            "pro.Producto, "
            "pro.Marca, "
            "pro.Stock, "
            "MAX(pre.Precio) PrecioUSD "
            "FROM producto pro "
            "JOIN precio pre ON pro.idProducto = pre.idProducto "
            "JOIN categoria cat ON pro.idCategoria = cat.idCategoria "
            "GROUP BY cat.Categoria, pro.idProducto, pro.Producto, pro.Marca, pro.Stock "
            ";"
        )
        emp_rows = cursor.fetchall()
        if len(emp_rows) <= 0:
            return not_found()
        for row in emp_rows:
            row["PrecioUSD"] = float(row["PrecioUSD"])  # Convierte PrecioUSD de Decimal a float
            row["PrecioCLP"] = round(row["PrecioUSD"] * dolar)  # Agrega el precio en CLP a la fila
        cursor.close()
        conn.close()
        response = jsonify(emp_rows)
        response.status_code = 200
        return response
    except Exception as e:
        print(e)


@app.route('/producto_detalle', methods=['GET'])
def producto_detalle(id_producto=None):
    """
    Usa request.args['idProducto'] y devuelve una respond con los datos del producto con PK igual a idProducto en la DB.
    Los datos son enviados en formato json e incluyen:

        Categoria: string, nombre de la categoría del producto.
        Producto: string, nombre del producto.
        Marca: string, nombre de la marca del producto.
        Stock: int, stock del producto
        PrecioUSD: float, valor del producto en dólares estadounidenses.
        PrecioCLP: int, valor del producto en pesos chilenos.
        Fecha_modificacion_precio: datetime.datetime, fecha del último cambio de precio del producto.

    También es usado por modificar_producto() para recuperar la nueva representación del producto.
    """
    try:
        dolar = valor_dolar()  # consulta la tasa de cambio de USD a CLP
        if not id_producto:
            id_producto = request.args['idProducto']
        conn = mysql.connect
        cursor = conn.cursor()
        cursor.execute(
            "SELECT "
            "cat.Categoria, "
            "pro.Producto, "
            "pro.Marca, "
            "pro.Stock, "
            "pre.Precio PrecioUSD, "
            "pre.Fecha_modificacion_precio "
            "FROM producto pro "
            "JOIN categoria cat ON pro.idCategoria = cat.idCategoria "
            "JOIN precio pre ON pro.idProducto = pre.idProducto "
            "WHERE pro.idProducto = %s "
            "ORDER BY pre.Fecha_modificacion_precio DESC LIMIT 1;",
            {id_producto}
        )
        emp_row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not emp_row:
            return not_found()
        emp_row["PrecioUSD"] = float(emp_row["PrecioUSD"])  # Convierte PrecioUSD de Decimal a float
        emp_row["PrecioCLP"] = round(emp_row["PrecioUSD"] * dolar)  # Agrega el precio en CLP a la fila
        if not id_producto:
            response = jsonify(emp_row)
            response.status_code = 200
            return response
        else:
            return emp_row
    except Exception as e:
        error = {"type": str(type(e)), "message": str(e),
                 "ups": "Esto lo usaba para debugear, debía borrarlo pero se me olvidó"}
        response = jsonify(error)
        return response


@app.route('/modificar_producto', methods=['PUT'])
def modificar_producto():
    """
    Extrae los datos desde request.json .form o .args, pero sólo se ha testeado desde .json.
    Modifica los datos de un producto en la DB. Los parámetros son todos opcionales menos idProducto, estos son:

        idProducto: int obligatorio, PK del producto cuyos datos se busca modificar.
        idCategoria: int, PK de la nueva categoría del producto, valores de 1 a 6.
        Producto: string, nuevo nombre del producto.
        Marca: string, nombre de la nueva marca del producto.
        Stock: int, nuevo stock del producto.
        Precio: float, nuevo valor del producto en dólares estadounidenses. Si se ingresa, se llamará a la función
            actualizar_ precio(id_producto=idProducto, nuevo_precio=Precio)

    Retorna un json con 2 items:

        msg: string, un mensaje que confirma que se ha alterado la DB.
        nueva_data: dict, el resultado de producto_detalle(id_producto=idProducto) una vez actualizada la DB.
    """
    if request.is_json:
        rd = request.json
    elif len(request.args) <= 1:
        rd = request.args.to_dict()
    elif len(request.form) <= 1:
        rd = request.form.to_dict()
    else:
        return not_found()
    try:
        if "idProducto" in rd.keys():
            _idProducto = int(rd["idProducto"])
        else:
            return not_found()

        if "idCategoria" in rd.keys():
            _idCategoria = int(rd["idCategoria"])
        else:
            _idCategoria = ""

        if "Producto" in rd.keys():
            _Producto = str(rd["Producto"])
        else:
            _Producto = ""

        if "Marca" in rd.keys():
            _Marca = str(rd["Marca"])
        else:
            _Marca = ""

        if "Stock" in rd.keys():
            _Stock = int(rd["Stock"])
        else:
            _Stock = ""

        if "Precio" in rd.keys():
            _Precio = float(rd["Precio"])
        else:
            _Precio = ""

        cambios = ""

        if _idCategoria:
            cambios += f"idCategoria={_idCategoria}"

        if _Producto:
            if _idCategoria:
                cambios += ", "
            cambios += f"Producto='{_Producto}'"

        if _Marca:
            if _idCategoria or _Producto:
                cambios += ", "
            cambios += f"Marca='{_Marca}'"

        if _Stock:
            if _idCategoria or _Producto or _Marca:
                cambios += ", "
            cambios += f"Stock={_Stock}"
        query = f"UPDATE producto SET {cambios} WHERE idProducto={_idProducto}"
        print(query)
        conn = mysql.connect
        cursor = conn.cursor()
        if _Precio:
            actualizar_precio(_idProducto, _Precio)
        cursor.execute(query)
        conn.commit()
        nueva_data = producto_detalle(_idProducto)
        msg = f"Producto con código {_idProducto} modificado"
        response = jsonify({"nueva_data": nueva_data, "msg": msg})
        response.status_code = 200
        return response
    except Exception as e:
        print(e)


def actualizar_precio(id_producto, nuevo_precio):
    try:
        conn = mysql.connect
        cursor = conn.cursor()
        query = (f"INSERT INTO precio (idPrecio, idProducto, Fecha_modificacion_precio, Precio) "
                 f"VALUES (DEFAULT, {id_producto}, CURRENT_TIMESTAMP(), {nuevo_precio});")
        cursor.execute(query)
        conn.commit()
        cursor.close()
        conn.close()
        return
    except Exception as e:
        raise e


@app.route('/eliminar_producto', methods=['POST'])
def eliminar_producto():
    """
    Toma request.form['idProducto'] y elimina el producto con PK igual a idProducto.
    Responde con un json que contiene un mensaje de confirmación.
    """
    try:
        id_producto = request.form['idProducto']
        conn = mysql.connect
        cursor = conn.cursor()
        cursor.execute("DELETE FROM producto WHERE idProducto =%s", {id_producto})
        conn.commit()
        response = jsonify("Producto de código %s borrado" % id_producto)
        response.status_code = 200
        cursor.close()
        conn.close()
        return response
    except Exception as e:
        print(e)


@app.errorhandler(404)
def not_found(error=None):
    message = {
        'status': 404,
        'message': 'Record not found: ' + request.url,
    }
    respond = jsonify(message)
    respond.status_code = 404
    return respond


if __name__ == "__main__":
    app.run(host='0.0.0.0')
