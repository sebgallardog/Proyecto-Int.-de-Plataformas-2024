from app import app
from flask import jsonify, request, redirect, url_for, render_template
from transbank.webpay.webpay_plus.transaction import Transaction

transaction = Transaction()


@app.route('/procesarPago', methods=['GET'])
def procesar_pago():
    amount = request.args["carritoTotal"]
    return redirect(url_for('pagarwebpay', amount=amount))


@app.route('/pagarwebpay', methods=['post'])
def pagarwebpay():
    try:
        host_url = request.host_url
        amount = request.form['amount']
        buy_order = 'order12345'
        session_id = 'session12345'
        return_url = f'{host_url}retorno'
        response = transaction.create(buy_order, session_id, amount, return_url)
        redirect_url = f"{response['url']}?token_ws={response['token']}"
        return redirect(redirect_url)
    except Exception as e:
        return e


@app.route('/retorno', methods=['GET'])
def retorno_webpay():
    try:
        host_url = request.host_url
        token = request.args.get('token_ws')
        response = transaction.commit(token)
        res = jsonify(response).json
        return render_template('resultadopago.html', response=res, host_url=host_url)
    except Exception as e:
        return jsonify({'error': str(e)}), 500



""" 
VISA                4051 8856 0044 6623 CVV 123     cualquier fecha de expiración 	Genera transacciones aprobadas.
AMEX                3700 0000 0002 032  CVV 1234    cualquier fecha de expiración 	Genera transacciones aprobadas.
MASTERCARD 	        5186 0595 5959 0568 CVV 123     cualquier fecha de expiración 	Genera transacciones rechazadas.
Prepago VISA        4051 8860 0005 6590 CVV 123     cualquier fecha de expiración 	Genera transacciones aprobadas.
Prepago MASTERCARD 	5186 1741 1062 9480 CVV 123     cualquier fecha de expiración 	Genera transacciones rechazadas.
Redcompra 	        4051 8842 3993 7763 	        Genera transacciones aprobadas (para operaciones que permiten débito Redcompra)
Redcompra 	        4511 3466 6003 7060 	        Genera transacciones aprobadas (para operaciones que permiten débito Redcompra)
Redcompra 	        5186 0085 4123 3829 	        Genera transacciones rechazadas (para operaciones que permiten débito Redcompra)
"""