from app import app
from config import mysql
from flask import jsonify, request, render_template
from ValorDolar import valor_dolar
from transbankapi import pagarwebpay, retorno_webpay

"""
OJO: El nombre de las tablas en las queries va siempre en minúscula
"""


@app.route('/', methods=['GET'])
def home():
    """Esto es sólo para realizar las pruebas"""
    response = productos()
    prod = response.json
    return render_template('form.html', productos=prod)


@app.route('/create', methods=['POST'])
def create_producto():
    """
    Crea un nuevo producto en la DB. Requiere los siguientes campos:

        idCategoria: int, PK de la categoría del producto, valores de 1 a 6.
        Producto: string, nombre del producto.
        Marca: string, nombre de la marca del producto.
        Stock: int, stock del producto.
        Precio: float, valor del producto en dólares estadounidenses.

    De ser exitosa la transacción, se llama a producto_detalle() con la PK autogenerada del nuevo producto y
    retorna un json con 2 objetos:

        msg: string, un mensaje que confirma que se ha creado un nuevo objeto.
        data: dict, el resultado de producto_detalle().
    """
    if request.is_json:
        rd = request.json
    elif len(request.args) >= 1:
        rd = request.args.to_dict()
    elif len(request.form) >= 1:
        rd = request.form.to_dict()
    else:
        return not_found()
    try:
        id_categoria = int(rd["idCategoria"])
        producto = str(rd["Producto"])
        marca = str(rd["Marca"])
        stock = int(rd["Stock"])
        precio = float(rd["Precio"])
        conn = mysql.connect
        cursor = conn.cursor()
        query_producto = ("INSERT INTO producto(idProducto, idCategoria, Producto, Marca, Stock) "
                          "VALUES(DEFAULT, %s, %s, %s, %s)")
        data_producto = (id_categoria, producto, marca, stock)
        cursor.execute(query_producto, data_producto)
        id_producto = cursor.lastrowid
        actualizar_precio(id_producto, precio, conn=conn, cursor=cursor)
        cursor.close()
        conn.commit()
        conn.close()

        nuevo_producto = producto_detalle(id_producto)
        msg = 'Producto agregado exitosamente'
        response = jsonify({"data": nuevo_producto, "msg": msg})
        response.status_code = 200
        return response
    except Exception as e:
        print(e)


@app.route('/listado_productos')
def productos():
    """
    Devuelve en una respond con un JSON con los datos de todos los productos en la DB.
    Cada elemento dentro del json es un dict que representa a un producto y contiene los siguientes datos de este:

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
            "P.idProducto, "
            "P.Producto, "
            "P.Marca, "
            "P.Stock, "
            "C.Categoria, "
            "PR.Precio PrecioUSD "
            "FROM Producto P "
            "INNER JOIN Categoria C ON P.idCategoria = C.idCategoria "
            "INNER JOIN Precio PR ON P.idProducto = PR.idProducto "
            "INNER JOIN ("
                "SELECT idProducto, MAX(Fecha_modificacion_precio) AS MaxFecha "
                "FROM Precio GROUP BY idProducto"
            ") MaxPrecio ON PR.idProducto = MaxPrecio.idProducto AND PR.Fecha_modificacion_precio = MaxPrecio.MaxFecha;"
        )
        emp_rows = cursor.fetchall()
        cursor.close()
        conn.close()
        if len(emp_rows) <= 0:
            return not_found()
        for row in emp_rows:
            row["PrecioUSD"] = float(row["PrecioUSD"])  # Convierte PrecioUSD de Decimal a float
            row["PrecioCLP"] = round(row["PrecioUSD"] * dolar)  # Agrega el precio en CLP a la fila
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
        idProducto: int, PK del producto.
        Producto: string, nombre del producto.
        Marca: string, nombre de la marca del producto.
        Stock: int, stock del producto
        PrecioUSD: float, valor del producto en dólares estadounidenses.
        PrecioCLP: int, valor del producto en pesos chilenos.
        Fecha_modificacion_precio: datetime.datetime, fecha del último cambio de precio del producto.

    También es llamado por modificar_producto() y create_producto().
    """
    try:
        notid = False
        dolar = valor_dolar()  # consulta la tasa de cambio de USD a CLP
        if not id_producto:
            id_producto = request.args['idProducto']
            notid = True
        conn = mysql.connect
        cursor = conn.cursor()
        cursor.execute(
            "SELECT "
            "cat.Categoria, "
            "pro.idProducto, "
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
        if notid:
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


@app.route('/modificar_producto', methods=['POST'])
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

    De ser exitosa la operación, retorna un json con 2 items:

        msg: string, un mensaje que confirma que se ha alterado la DB.
        nueva_data: dict, el resultado de producto_detalle(id_producto=idProducto) una vez actualizada la DB.
    """
    if request.is_json:
        rd = request.json
        print(rd)
    elif len(request.args) >= 1:
        rd = request.args.to_dict()
        print(rd)
    elif len(request.form) >= 1:
        rd = request.form.to_dict()
        print(rd)
    else:
        return not_found()
    try:
        cambios = ""
        if rd["idProducto"]:
            _idProducto = int(float(rd["idProducto"]))
        else:
            return not_found()

        if rd["idCategoria"]:
            cambios += f"idCategoria={rd['idCategoria']}"

        if rd["Producto"]:
            if rd["idCategoria"]:
                cambios += ", "
            cambios += f"Producto='{rd['Producto']}'"

        if rd["Marca"]:
            if rd["idCategoria"] or rd["Producto"]:
                cambios += ", "
            cambios += f"Marca='{rd['Marca']}'"

        if rd["Stock"]:
            if rd["idCategoria"] or rd['Producto'] or rd['Marca']:
                cambios += ", "
            cambios += f"Stock={rd['Stock']}"

        print(cambios)

        if rd["Precio"]:
            _Precio = float(rd["Precio"])
        else:
            _Precio = ""

        conn = mysql.connect
        cursor = conn.cursor()

        if cambios:
            query = f"UPDATE producto SET {cambios} WHERE idProducto={_idProducto}"
            print(query)
            cursor.execute(query)

        if rd["Precio"]:
            actualizar_precio(_idProducto, float(rd["Precio"]), conn, cursor)

        conn.commit()
        cursor.close()
        conn.close()

        if cambios or rd["Precio"]:
            nueva_data = producto_detalle(_idProducto)
            msg = f"Producto con código {_idProducto} modificado"
            response = jsonify({"nueva_data": nueva_data, "msg": msg})
        else:
            response = jsonify("No se ingresaron datos para modificar el producto")

        response.status_code = 200
        return response
    except Exception as e:
        print(e)


def actualizar_precio(id_producto, nuevo_precio, conn=None, cursor=None):
    try:
        notconn = False
        notcursor = False

        if not conn:
            conn = mysql.connect
            notconn = True

        if not cursor:
            cursor = conn.cursor()
            notcursor = True

        query = (f"INSERT INTO precio (idPrecio, idProducto, Fecha_modificacion_precio, Precio) "
                 f"VALUES (DEFAULT, {id_producto}, CURRENT_TIMESTAMP(), {nuevo_precio});")
        print(query)
        cursor.execute(query)

        if notcursor:
            cursor.close()

        if notconn:
            conn.commit()
            conn.close()

        return
    except Exception as e:
        raise e


@app.route('/eliminar_producto', methods=['POST'])
def eliminar_producto():
    """
    Toma request.form['idProducto'] y elimina el producto con PK igual a idProducto.
    Responde con un json que contiene un mensaje de confirmación.
    Retorna un json con un mensaje que confirma o no si el producto fué eliminado.
    """
    try:
        id_producto = request.form['idProducto']
        conn = mysql.connect
        cursor = conn.cursor()
        cursor.execute("DELETE FROM producto WHERE idProducto =%s", {id_producto})
        if cursor.rowcount == 1:
            msg = "Producto de código %s borrado" % id_producto
            conn.commit()
        else:
            msg = "Producto de código %s No encontrado" % id_producto
        response = jsonify(msg)
        response.status_code = 200
        cursor.close()
        conn.close()
        return response
    except Exception as e:
        print(e)


@app.route('/update_stock', methods=['POST'])
def update_stock():
    e="D"
    print(e)
    try:
        form = request.json['carrito']
        print(form)
        conn = mysql.connect
        cursor = conn.cursor()
        for item in form:
            id_producto = item["idProducto"]
            cantidad = int(item["cantidad"])
            query = f"SELECT Stock FROM producto WHERE idProducto={id_producto}"
            cursor.execute(query)
            emp_row = cursor.fetchone()
            stock = int(emp_row["Stock"]) - cantidad
            query = f"UPDATE producto SET Stock={stock} WHERE idProducto={id_producto}"
            cursor.execute(query)
        conn.commit()
        cursor.close()
        conn.close()
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
    app.run(host='0.0.0.0', debug=True)
