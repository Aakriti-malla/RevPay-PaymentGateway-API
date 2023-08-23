from flask import Flask, request, jsonify
# from flask_sqlalchemy import SQLAlchemy
# from passlib.hash import sha256_crypt
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin'
app.config['MYSQL_DB'] = 'rev_pay'

mysql = MySQL(app)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if 'username' not in data or 'password' not in data:
        return jsonify({"error": "Username and password are required"}), 400
    
    username = data['username']
    password = data['password']

    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM businesses WHERE username = %s", (username,))
    existing_business = cur.fetchone()
    cur.close()

    if existing_business:
        return jsonify({"error": "Username already exists"}), 409
    
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO businesses (username, password) VALUES (%s, %s)", (username, password))
    mysql.connection.commit()
    cur.close()

    return jsonify({"message": "Registration successful"}), 201


@app.route('/')
def hello():
    return "Welcome to Rev Pay"

if __name__ == '__main__':
    app.run()