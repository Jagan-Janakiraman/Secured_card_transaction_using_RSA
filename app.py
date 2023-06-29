from flask import Flask, request, jsonify
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import pymysql
import secrets


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
    encrypted_symmetric_key = db.Column(db.String(512))

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


private_key = None
public_key = None
# Generate a secure random key
symmetric_key = secrets.token_bytes(16)


def generate_rsa_keys():
    global private_key, public_key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()
    return private_key, public_key


@app.route('/generate_keys', methods=['GET'])
def generate_keys():
    generate_rsa_keys()
    print(public_key)
    print(private_key)
    return jsonify(
        message = 'rsa key generated sucessfully'
        ), 200
    
@app.route('/encrypt', methods=['POST'])
def encrypt():
    card_details = request.json.get('card_details')
    
    if not card_details:
        return jsonify({'error': 'Missing card details'}), 400
    
    private_key, public_key = generate_rsa_keys()
    if not public_key:
        return jsonify({'error': 'RSA key not generated'}), 400
    
    cipher = Cipher(algorithms.AES(symmetric_key), modes.ECB(), backend=default_backend())
    encryptor = cipher.encryptor()
    padded_card_details = card_details.encode('utf-8').rjust(32)
    encrypted_card_details = encryptor.update(padded_card_details) + encryptor.finalize()
    encrypted_symmetric_key = public_key.encrypt(
        symmetric_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    card = CardDetails(encrypted_card_details.hex(), encrypted_symmetric_key.hex())
    db.session.add(card)
    db.session.commit()
    
    return jsonify({
        'encrypted_card_details': encrypted_card_details.hex(),
        'encrypted_symmetric_key': encrypted_symmetric_key.hex()
    })


@app.route('/decrypt', methods=['POST'])
def decrypt():
    encrypted_card_details = request.json.get('encrypted_card_details')
    encrypted_symmetric_key = request.json.get('encrypted_symmetric_key')
    
    if not encrypted_card_details or not encrypted_symmetric_key:
        return jsonify({'message':'Missing encrypted card details or symmetric key.'}), 400
    
    if not private_key:
        return jsonify({'message':'RSA key not genereted.'}), 400
        

    decrypted_symmetric_key = private_key.decrypt(
        bytes.fromhex(encrypted_symmetric_key),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    decipher = Cipher(algorithms.AES(decrypted_symmetric_key), modes.ECB(), backend=default_backend())
    decryptor = decipher.decryptor()
    decrypted_card_details = decryptor.update(bytes.fromhex(encrypted_card_details)) + decryptor.finalize()

    # Decode the decrypted binary data using UTF-8 to obtain the original string
    decrypted_card_details = decrypted_card_details.decode('utf-8').strip()

    return jsonify({
        'decrypted_card_details': decrypted_card_details
    })



if __name__ == '__main__':
    app.run(debug=True)