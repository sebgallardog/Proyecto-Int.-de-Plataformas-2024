# import pymysql
from MySQLdb.cursors import DictCursor, Cursor

from app import app
from config import mysql
from flask import jsonify, flash, request, render_template, redirect

"""
OJO: El nombre de las tablas en las queries va siempre en minúscula
"""


@app.route('/', methods=['GET'])
def home():
    return render_template('form.html')


@app.route('/create/<idTipoHerramienta>/<Producto_nom>/<Producto_marca>/<Producto_stock>', methods=['POST'])
def create_producto(idTipoHerramienta, Producto_nom, Producto_marca, Producto_stock):
    try:
        conn = mysql.connect
        cursor = conn.cursor()
        sqlQuery = """INSERT INTO producto(idProducto, idTipoHerramienta, Producto_nom, Producto_marca, Producto_stock) VALUES(DEFAULT, %s, %s, %s, %s)"""
        bindData = (idTipoHerramienta, Producto_nom, Producto_marca, Producto_stock)
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
def producto():
    try:
        conn = mysql.connect
        cursor = conn.cursor()
        cursor.execute(
            "SELECT "
            "th.idTipoHerramienta idCategoría, "
            "th.TipoHerramienta_nom Categoría, "
            "pro.idProducto, "
            "pro.Producto_nom Producto, "
            "pro.Producto_marca Marca, "
            "pre.Precio_valor Precio "
            "FROM producto pro "
            "JOIN precio pre ON pro.idProducto = pre.idProducto "
            "JOIN tipoherramienta th ON pro.idTipoHerramienta = th.idTipoHerramienta "
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
            "th.TipoHerramienta_nom Categoría, "
            "pro.Producto_nom Producto, "
            "pro.Producto_marca Marca, "
            "pre.Precio_valor Precio, "
            "pre.Precio_fecha Última_modificación_precio "
            "FROM producto pro "
            "JOIN tipoherramienta th ON pro.idTipoHerramienta = th.idTipoHerramienta "
            "JOIN precio pre ON pro.idProducto = pre.idProducto "
            "WHERE pro.idProducto = %s "
            "ORDER BY pre.Precio_fecha DESC LIMIT 1;",
            {id_producto}
        )
        empRow = cursor.fetchone()
        if not empRow:
            return not_found()
        response = jsonify(empRow)
        # response.status_code = 200
        cursor.close()
        conn.close()
        # return render_template('form.html', producto_detalle=response.json)
        return response
    except Exception as e:
        print(e)


@app.route('/modificar_producto', methods=['PUT'])
def modificar_producto():
    # No se pueden modificar filas cuya PK sea FK en otra tabla en el motor InnoDB
    try:
        _json = request.json
        _idProducto = _json["idProducto"]
        _idTipoHerramienta = _json["idTipoHerramienta"]
        _Producto_nom = _json["Producto_nom"]
        _Producto_marca = _json["Producto_marca"]
        _Producto_stock = _json["Producto_stock"]
        if _idProducto and _idTipoHerramienta and _Producto_nom and _Producto_marca and _Producto_stock and request.method == 'PUT':
            sqlQuery = "UPDATE producto SET idTipoHerramienta=%s, Producto_nom=%s, Producto_marca=%s, Producto_stock=%s WHERE idProducto=%s"
            bindData = (_idTipoHerramienta, _Producto_nom, _Producto_marca, _Producto_stock, _idProducto,)
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


@app.route('/eliminar_producto', methods=['POST'])
def actualizar_precio():
    try:
        cod_producto = request.args['idProducto']
        nuevo_precio = request.args['nuevo_precio']
        conn = mysql.connect
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO precio (idPrecio, idProducto, Precio_fecha, Precio_valor) "
            "VALUES (DEFAULT, %s, CURRENT_TIMESTAMP(), %s);",
            {cod_producto, nuevo_precio}
        )
        conn.commit()
        response = jsonify(f'Precio del producto de código {cod_producto} actualizado a {nuevo_precio}')
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
