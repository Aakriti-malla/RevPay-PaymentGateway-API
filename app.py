from flask import Flask, request, jsonify
from hashlib import sha256
from flask_mysqldb import MySQL
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import secrets
import datetime

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
        return jsonify({"error": "Bank account number and IFSC Code are required"}), 401
    
    bank_account_number = data['bank_account_number']
    ifsc_code = data['ifsc_code']
    
    if 'transaction_type' in data:
        transaction_type = data['transaction_type']
        allowed_transaction_types = ['CREDIT', 'DEBIT', 'BOTH']
        
        if transaction_type not in allowed_transaction_types:
            return jsonify({"error": " Invalid 'transaction_type'. Allowed values are 'CREDIT', 'DEBIT' or 'BOTH' "}), 401

    # Check if bank account number is already used
    cur = mysql.connection.cursor()
    cur.execute("SELECT account_id FROM bankaccounts WHERE bank_account_number = %s", (bank_account_number,))
    existing_account = cur.fetchone()
    cur.close()

    if existing_account:
        return jsonify({"error": "Bank account already exists!"}), 401

    # Insert into db in case of new account data 
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
    sender_account_id = data['sender_account_id']
    receiver_account_number = data['receiver_account_number']
    transaction_type = data['transaction_type']
    amount = data['amount']

    cur = mysql.connection.cursor()

    # Check for negative amount
    if amount < 0:
        return jsonify({"error": "Amount cannot be negative"}), 400

    # Get sender's activation status and transaction type
    cur.execute("SELECT activation_status, transaction_type FROM bankaccounts WHERE account_id = %s", (sender_account_id,))
    sender_info = cur.fetchone()

    if not sender_info:
        return jsonify({"error": "Sender's account not found!"}), 400

    sender_activation_status = sender_info[0]
    sender_transaction_type = sender_info[1]

    # Check if sender's account is active
    if sender_activation_status != 'ACTIVE':
        return jsonify({"error": "Sender's account is INACTIVE. Transaction rejected!"}), 400

    # Check if the transaction type is valid for sender
    if transaction_type == 'DEPOSIT' and sender_transaction_type not in ['DEBIT', 'BOTH']:
        return jsonify({"error": "Transaction type 'DEPOSIT' not allowed for this sender account"}), 400
    elif transaction_type == 'WITHDRAWAL' and sender_transaction_type not in ['CREDIT', 'BOTH']:
        return jsonify({"error": "Transaction type 'WITHDRAWAL' not allowed for this sender account"}), 400

    # Get receiver's activation status and transaction type
    cur.execute("SELECT activation_status, transaction_type FROM bankaccounts WHERE bank_account_number = %s", (receiver_account_number,))
    receiver_info = cur.fetchone()

    if not receiver_info:
        return jsonify({"error": "Receiver's account not found"}), 400

    receiver_activation_status = receiver_info[0]
    receiver_transaction_type = receiver_info[1]

    # Check if receiver's account is active
    if receiver_activation_status != 'ACTIVE':
        return jsonify({"error": "Receiver's account is INACTIVE. Transaction rejected!"}), 400

    # Check if the transaction type is valid for receiver
    if transaction_type == 'DEPOSIT' and receiver_transaction_type not in ['CREDIT', 'BOTH']:
        return jsonify({"error": "Transaction type 'DEPOSIT' not allowed for this receiver account"}), 400
    elif transaction_type == 'WITHDRAWAL' and receiver_transaction_type not in ['DEBIT', 'BOTH']:
        return jsonify({"error": "Transaction type 'WITHDRAWAL' not allowed for this receiver account"}), 400

    # Check sender's balance for WITHDRAWAL
    if transaction_type == 'WITHDRAWAL':
        cur.execute("SELECT balance FROM bankaccounts WHERE account_id = %s", (sender_account_id,))
        sender_balance = cur.fetchone()[0]

        if sender_balance < amount:
            return jsonify({"error": "Insufficient balance in the sender account"}), 400
        
        # Withdrwal limit validation
        today = datetime.datetime.now().date()
        cur.execute("SELECT SUM(amount) FROM transactions WHERE account_id = %s AND transaction_type = 'WITHDRAWAL' AND DATE(transaction_date) = %s", (sender_account_id, today))
        total_withdrawn_today = cur.fetchone()[0]

        if total_withdrawn_today is None:
            total_withdrawn_today = 0

        if total_withdrawn_today + amount > 20000:
            return jsonify({"error": "Withdrawal amount exceeds the daily limit of Rs. 20,000"}), 400

    # Update sender's and receiver's balances
    if transaction_type == 'DEPOSIT':
        cur.execute("UPDATE bankaccounts SET balance = balance - %s WHERE account_id = %s", (amount, sender_account_id))
        cur.execute("UPDATE bankaccounts SET balance = balance + %s WHERE bank_account_number = %s", (amount, receiver_account_number))
    elif transaction_type == 'WITHDRAWAL':
        cur.execute("UPDATE bankaccounts SET balance = balance - %s WHERE account_id = %s", (amount, sender_account_id))
        cur.execute("UPDATE bankaccounts SET balance = balance + %s WHERE bank_account_number = %s", (amount, receiver_account_number))

    # Insert transaction record
    cur.execute("INSERT INTO transactions (account_id, beneficiary_account_number, transaction_type, amount) VALUES (%s, %s, %s, %s)", (sender_account_id, receiver_account_number, transaction_type, amount))
    mysql.connection.commit()
    cur.close()

    return jsonify({"message": "Transaction recorded successfully"}), 200

# Route for fetching balance of an account
@app.route("/balance/<int:account_id>", methods=["GET"])
@jwt_required()
def get_balance(account_id):
    current_user = get_jwt_identity()
    cur = mysql.connection.cursor()

    # Check if account exists and belongs to the same company as the authenticated user
    cur.execute("SELECT * FROM bankaccounts WHERE account_id = %s AND company_id = %s", (account_id, current_user))
    account = cur.fetchone()

    if account is None:
        cur.close()
        return jsonify({"error": "Account not found"}), 404

    cur.close()
    
    return jsonify({"balance": account[5]}), 200


if __name__ == '__main__':
    app.run()