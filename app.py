from flask import Flask, request, jsonify
# from flask_sqlalchemy import SQLAlchemy
from hashlib import sha256
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin'
app.config['MYSQL_DB'] = 'rev_pay'

mysql = MySQL(app)


# Route for Registration
@app.route('/register', methods=['POST'])
def register():
    data = request.json

    if 'username' not in data or 'password' not in data or 'company_name' not in data:
        return jsonify({"error": "Company name, Username & passwordare required"}), 400

    company_name = data['company_name']
    username = data['username']
    password = data['password']

    password_hash = sha256(password.encode()).hexdigest()

    cur = mysql.connection.cursor()
    cur.execute("SELECT company_id FROM businesses WHERE username = %s", (username,))
    existing_business = cur.fetchone()
    cur.close()

    if existing_business:
        return jsonify({"error": "Username already exists"}), 409
    
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO businesses (company_name, username, password) VALUES (%s, %s, %s)", (company_name, username, password_hash))
    mysql.connection.commit()
    cur.close()

    return jsonify({"message": "Registration successful"}), 201

# Route to authenticate and login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']

    password_hash = sha256(password.encode()).hexdigest()
    cur = mysql.connection.cursor()
    cur.execute("SELECT company_id FROM Businesses WHERE username = %s AND password = %s", (username, password_hash))
    result = cur.fetchone()
    
    if result:
        return jsonify({"message": "Login successful", "company_id": result[0]})
    else:
        return jsonify({"message": "Invalid credentials"}), 401

# Route to create a bank account
@app.route('/create_account', methods=['POST'])
def create_account():
    data = request.json
    company_id = data['company_id']
    bank_account_number = data['bank_account_number']
    ifsc_code = data['ifsc_code']

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO BankAccounts (company_id, bank_account_number, ifsc_code) VALUES (%s, %s, %s)", (company_id, bank_account_number, ifsc_code))
    mysql.connection.commit()
    cur.close()
    
    return jsonify({"message": "Bank account created successfully"})    


@app.route('/')
def hello():
    return "Welcome to Rev Pay"

if __name__ == '__main__':
    app.run()