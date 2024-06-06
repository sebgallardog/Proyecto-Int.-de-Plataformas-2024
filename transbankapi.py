from app import app
from flask import jsonify, request, redirect, url_for, render_template
from transbank.webpay.webpay_plus.transaction import Transaction

transaction = Transaction()


@app.route('/procesarPago', methods=['GET'])
def procesar_pago():
    amount = request.args["carritoTotal"]
    return redirect(url_for('pagarwebpay', amount=amount))


@app.route('/pagarwebpay', methods=['GET'])
def pagarwebpay():
    try:
        amount = request.args['amount']
        buy_order = 'order12345'
        session_id = 'session12345'
        return_url = 'http://localhost:5000/retorno'
        response = transaction.create(buy_order, session_id, amount, return_url)
        redirect_url = f"{response['url']}?token_ws={response['token']}"
        return redirect(redirect_url)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/retorno', methods=['GET'])
def retorno_webpay():
    try:
        token = request.args.get('token_ws')
        response = transaction.commit(token)
        return render_template('resultadopago.html', response=response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
