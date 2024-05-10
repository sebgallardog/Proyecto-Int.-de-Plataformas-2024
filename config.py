from app import app
from flask import Flask
from flask_mysqldb import MySQL

app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'ferremas'
app.config['MYSQL_HOST'] = 'localhost'
mysql = MySQL(app)
