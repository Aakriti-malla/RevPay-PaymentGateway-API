from flask import Flask, request, jsonify
from hashlib import sha256
from flask_mysqldb import MySQL
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import secrets

app = Flask(__name__)

secret_key = secrets.token_hex(32)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin'
app.config['MYSQL_DB'] = 'rev_pay'
app.config['JWT_SECRET_KEY'] = secret_key

mysql = MySQL(app)
jwt = JWTManager(app)


# Route for Registration
@app.route('/register', methods=['POST'])
def register():
    data = request.json

    required_fields = ['username','password', 'company_name']

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Company name, username, and password are required"}), 400

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
    cur.execute("SELECT company_id FROM businesses WHERE username = %s AND password = %s", (username, password_hash))
    result = cur.fetchone()
    
    if result:
        access_token = create_access_token(identity=result[0])
        return jsonify({"message": "Login successful", "access_token": access_token})
    else:
        return jsonify({"message": "Invalid credentials"}), 401

# Route to create a bank account
@app.route('/add_account', methods=['POST'])
@jwt_required()
def add_account():
    current_user = get_jwt_identity()
    data = request.json
    required_fields = ['bank_account_number', 'ifsc_code']

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Bank account number and IFSC Code are required"}), 400
    
    bank_account_number = data['bank_account_number']
    ifsc_code = data['ifsc_code']
    
    if 'transaction_type' in data:
        transaction_type = data['transaction_type']
        allowed_transaction_types = ['CREDIT', 'DEBIT', 'BOTH']
        
        if transaction_type not in allowed_transaction_types:
            return jsonify({"error": "Invalid 'transaction_type'. Allowed values are 'CREDIT', 'DEBIT' or 'BOTH"}), 400

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO bankaccounts (company_id, bank_account_number, ifsc_code, transaction_type) VALUES (%s, %s, %s, %s)", (current_user, bank_account_number, ifsc_code, transaction_type))
    mysql.connection.commit()
    cur.close()
    
    return jsonify({"message": "Bank account created successfully"})    


# Route for transactions 
@app.route('/transactions', methods=["POST"])
@jwt_required()
def create_transactions():
    data = request.json
    sender_account_id = get_jwt_identity()
    receiver_account_id = data['receiver_account_id']  
    transaction_type = data['transaction_type']  
    amount = data['amount']

    cur = mysql.connection.cursor()
    cur.execute("SELECT transaction_type FROM bankaccounts WHERE account_id = %s", (sender_account_id,))
    sender_transaction_type = cur.fetchone()[0]
    cur.close()

    if sender_transaction_type == 'BOTH' or sender_transaction_type == transaction_type:
        cur = mysql.connection.cursor()
        cur.execute("UPDATE bankaccounts SET balance = balance - %s WHERE account_id = %s", (amount, sender_account_id))
        cur.execute("UPDATE bankaccounts SET balance = balance + %s WHERE account_id = %s", (amount, receiver_account_id))
        mysql.connection.commit()
        cur.close()

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Transactions (account_id, beneficiary_account_number, transaction_type, amount) VALUES (%s, %s, %s, %s)", (sender_account_id, receiver_account_id, transaction_type, amount))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Transaction recorded successfully"})
    else:
        return jsonify({"error": f"Transaction type '{transaction_type}' not allowed for this account"}), 400


if __name__ == '__main__':
    app.run()