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
    # Generate a new RSA private key with the given public exponent and key size
    private_key = rsa.generate_private_key(
        public_exponent=65537,  # The public exponent used for RSA encryption
        key_size=2048  # The size of the RSA key in bits
    )
    # Extract the corresponding public key from the generated private key
    public_key = private_key.public_key()
    return private_key, public_key

""" 
It generates a new RSA private key with the specified public exponent and key size, 
and then extracts the corresponding public key from the private key. 
The private and public keys are stored in global variables private_key and public_key for later use.
"""

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
    
    # Create an AES cipher object using the symmetric key and ECB mode
    cipher = Cipher(algorithms.AES(symmetric_key), modes.ECB(), backend=default_backend())
    encryptor = cipher.encryptor()
    
    # Pad the card details to a multiple of 16 bytes and encode as UTF-8
    padded_card_details = card_details.encode('utf-8').rjust(32)
    
    # Encrypt the padded card details using the AES cipher
    encrypted_card_details = encryptor.update(padded_card_details) + encryptor.finalize()
    
    # Encrypt the symmetric key with the RSA public key using OAEP padding
    encrypted_symmetric_key = public_key.encrypt(
        symmetric_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    # Create a new CardDetails object with the encrypted card details and symmetric key
    card = CardDetails(encrypted_card_details.hex(), encrypted_symmetric_key.hex())
    
    # Add the card details to the database
    db.session.add(card)
    db.session.commit()
    
    # Return the encrypted card details and encrypted symmetric key as JSON response
    return jsonify({
        'encrypted_card_details': encrypted_card_details.hex(),
        'encrypted_symmetric_key': encrypted_symmetric_key.hex()
    })

    """
        It retrieves the card_details from the request JSON, generates RSA keys, creates an AES cipher object, 
        encrypts the card details using AES, encrypts the symmetric key using RSA, 
        stores the encrypted data in the database, and returns the encrypted card details and symmetric key as a JSON response.
    """


@app.route('/decrypt', methods=['POST'])
def decrypt():
    encrypted_card_details = request.json.get('encrypted_card_details')
    encrypted_symmetric_key = request.json.get('encrypted_symmetric_key')
    
    if not encrypted_card_details or not encrypted_symmetric_key:
        return jsonify({'message':'Missing encrypted card details or symmetric key.'}), 400
    
    if not private_key:
        return jsonify({'message':'RSA key not generated.'}), 400
    
    # Decrypt the symmetric key using the RSA private key and OAEP padding
    decrypted_symmetric_key = private_key.decrypt(
        bytes.fromhex(encrypted_symmetric_key),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Create an AES cipher object using the decrypted symmetric key and ECB mode
    decipher = Cipher(algorithms.AES(decrypted_symmetric_key), modes.ECB(), backend=default_backend())
    decryptor = decipher.decryptor()

    # Decrypt the encrypted card details using the AES cipher
    decrypted_card_details = decryptor.update(bytes.fromhex(encrypted_card_details)) + decryptor.finalize()

    # Decode the decrypted binary data using UTF-8 to obtain the original string
    decrypted_card_details = decrypted_card_details.decode('utf-8').strip()

    # Return the decrypted card details as a JSON response
    return jsonify({
        'decrypted_card_details': decrypted_card_details
    })

    """
    It retrieves the encrypted_card_details and encrypted_symmetric_key from the request JSON, checks if they are present, 
    checks if the RSA private key is generated, decrypts the symmetric key using RSA and OAEP padding, creates an AES cipher object using the decrypted symmetric key, 
    decrypts the encrypted card details using AES, decodes the decrypted data, and returns the decrypted card details as a JSON response.
    """


if __name__ == '__main__':
    app.run(debug=True)