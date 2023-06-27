from flask import Flask, request, jsonify
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import pymysql


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost/card_details_db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Database configuration
db_config = {
    'host': 'localhost',
    'database': 'card_details_db',
    'user': 'root',
    'password': 'password'
}

# to create a database connection
def create_connection():
    connection = None
    try:
        connection = pymysql.connect(**db_config)
        # print("Connected to MySQL database")
        return connection
    except pymysql.Error as e:
        print(f"Error while connecting to MySQL database: {e}")
    return connection

# database for card details
class CardDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    encrypted_card_details = db.Column(db.String(256))
    encrypted_symmetric_key = db.Column(db.String(256))

    def __init__(self, encrypted_card_details, encrypted_symmetric_key):
        self.encrypted_card_details = encrypted_card_details
        self.encrypted_symmetric_key = encrypted_symmetric_key


# to check the database connection
@app.route('/check_db_connection', methods=['GET'])
def check_db_connection():
    try:
        connection = create_connection()
        if connection is None:
            return jsonify(status="Error", message="Failed to connect to the database")

        connected_database = db_config['database']  # Retrieve the database name from the db_config dictionary
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        table_names = [table[0] for table in cursor.fetchall()] #LIST COMPRENSION TO DISPLAY THE TABLES IN THAT DATABASE
        cursor.close()
        connection.close()
        return jsonify(status="Connected", database=connected_database, tables=table_names)
    except pymysql.Error as e:
        return jsonify(status="Error", message=str(e))
    
##################################################################
private_key = None
public_key = None
symmetric_key = b'SuperSecretKey123'  # Replace with a securely generated key
   
def generate_rsa_keys():
    global private_key, public_key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key
    
@app.route('/generate_keys', methods=['GET'])
def generate_keys():
    generate_rsa_keys()
    print(public_key)
    print(private_key)
    return jsonify(
        message = 'rsa key generated sucessfully'
        ), 200
   
   
   
   
   
   
    
if __name__ == '__main__':
    app.run(debug=True)