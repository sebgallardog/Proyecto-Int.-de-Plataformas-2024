from app import app
from config import mysql
from flask import jsonify, flash, request, render_template, redirect
import ValorDolar
"""
OJO: El nombre de las tablas en las queries va siempre en minúscula
"""


@app.route('/', methods=['GET'])
def home():
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
    try:
        conn = mysql.connect
        cursor = conn.cursor()
        cursor.execute(
            "SELECT "
            "cat.idCategoria, "
            "cat.Categoria, "
            "pro.idProducto, "
            "pro.Producto, "
            "pro.Marca, "
            "pre.Precio "
            "FROM producto pro "
            "JOIN precio pre ON pro.idProducto = pre.idProducto "
            "JOIN categoria cat ON pro.idCategoria = cat.idCategoria "
            ";"
        )
        empRows = cursor.fetchall()
        response = jsonify(empRows)
        response.status_code = 200
        cursor.close()
        conn.close()
        return response
    except Exception as e:
        print(e)


@app.route('/producto_detalle', methods=['GET'])
def producto_detalle():
    try:
        id_producto = request.args['idProducto']
        conn = mysql.connect
        cursor = conn.cursor()
        cursor.execute(
            "SELECT "
            "cat.Categoria, "
            "pro.Producto, "
            "pro.Marca, "
            "pre.Precio, "
            "pre.Fecha_modificacion_precio "
            "FROM producto pro "
            "JOIN categoria cat ON pro.idCategoria = cat.idCategoria "
            "JOIN precio pre ON pro.idProducto = pre.idProducto "
            "WHERE pro.idProducto = %s "
            "ORDER BY pre.Fecha_modificacion_precio DESC LIMIT 1;",
            {id_producto}
        )
        empRow = cursor.fetchone()
        if not empRow:
            return not_found()
        # dolar = ValorDolar()
        # empRow["Precio"] *= dolar.valor
        response = jsonify(empRow)
        response.status_code = 200
        cursor.close()
        conn.close()
        return response
    except Exception as e:
        print(e)


@app.route('/modificar_producto', methods=['PUT'])
def modificar_producto():
    # No se pueden modificar filas cuya PK sea FK en otra tabla en el motor InnoDB
    try:
        _json = request.json
        _idProducto = _json["idProducto"]
        _idCategoria = _json["idCategoria"]
        _Producto = _json["Producto"]
        _Marca = _json["Marca"]
        _Stock = _json["Stock"]
        cambios = ""
        query = f"UPDATE producto SET {cambios} WHERE idProducto={_idProducto}"
        if not _idProducto:
            return not_found
        else:
            if _idCategoria:
                cambios += f"idCategoria={_idCategoria}"

            if _Producto:
                if _idCategoria:
                    cambios += ", "
                cambios += f"Producto={_Producto}"

            if _Marca:
                if _idCategoria or _Producto:
                    cambios += ", "
                cambios += f"Marca={_Marca}"
                
            if _Stock:
                if _idCategoria or _Producto or _Marca:
                    cambios += ", "
                cambios += f"Stock={_Stock}"


        if _idProducto and _idCategoria and _Producto and _Marca and _Stock and request.method == 'PUT':
            sqlQuery = "UPDATE producto SET idCategoria=%s, Producto=%s, Marca=%s, Stock=%s WHERE idProducto=%s"
            bindData = (_idCategoria, _Producto, _Marca, _Stock, _idProducto,)
            conn = mysql.connect
            cursor = conn.cursor()
            cursor.execute(sqlQuery, bindData)
            conn.commit()
            response = jsonify("Producto con código {idProducto} modificado".format(idProducto=_idProducto))
            response.status_code = 200
            return response
        else:
            return not_found()
    except Exception as e:
        print(e)  


@app.route('/actualizar_precio', methods=['PUT'])
def actualizar_precio():
    try:
        Id_producto = request.args['idProducto']
        nuevo_precio = request.args['Nuevo_Precio']
        conn = mysql.connect
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO precio (idPrecio, idProducto, Precio_fecha, Precio_valor) "
            "VALUES (DEFAULT, %s, CURRENT_TIMESTAMP(), %s);",
            {Id_producto, nuevo_precio}
        )
        conn.commit()
        response = jsonify(f'Precio del producto de código {Id_producto} actualizado a {nuevo_precio}')
        response.status_code = 200
        cursor.close()
        conn.close()
        return response
    except Exception as e:
        print(e)


@app.route('/eliminar_producto', methods=['POST'])
def eliminar_producto():
    # No se pueden eliminar filas cuya PK sea FK en otra tabla en el motor InnoDB
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
    respone = jsonify(message)
    respone.status_code = 404
    return respone


if __name__ == "__main__":
    app.run(host='0.0.0.0')
