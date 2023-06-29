# Secured_card_transaction_using_RSA

 This Flask application provides a secure card transactions system using RSA encryption and a MySQL database to store the encrypted card details. The application includes separate APIs for RSA key generation, encryption, and decryption.

# To run Requirements.txt file is this command

    pip install -r requirements.txt

Steps:

1. Importing Required Libraries:
   - The necessary libraries and modules are imported, including Flask, SQLAlchemy, cryptography, pymysql, and secrets.

2. Flask App Configuration:
   - The Flask app is initialized, and the SQLAlchemy and Flask-Migrate extensions are configured to work with the app.
   - The SQLAlchemy database URI is set to connect to a MySQL database named "card_details_db" with the username "root" and password "password".

3. Database Configuration:
   - The `create_connection()` function is defined to establish a connection to the MySQL database based on the provided configuration.
   - A `CardDetails` class is created as a model representing the table structure in the database. It contains columns for `id`, `encrypted_card_details`, and `encrypted_symmetric_key`.

4. Checking Database Connection:
   - The `/check_db_connection` route is defined to verify the database connection.
   - Inside the route, the `create_connection()` function is called to attempt a connection to the database.
   - If the connection is successful, it retrieves the table names and returns a JSON response with the status, connected database name, and table names. Otherwise, it returns an error message.

5. Generating RSA Keys:
   - The `generate_rsa_keys()` function generates RSA key pair (private key and public key) using the `rsa` module from the `cryptography` library.
   - The private key is stored in the `private_key` variable, and the public key is stored in the `public_key` variable.

6. Generating Symmetric Key:
   - A symmetric key is generated using the `secrets.token_bytes()` function from the `secrets` module.
   - The symmetric key is stored in the `symmetric_key` variable.

7. Generating RSA Keys (API Endpoint):
   - The `/generate_keys` route is defined to generate the RSA key pair and print the public key and private key for testing purposes.
   - Inside the route, the `generate_rsa_keys()` function is called to generate the RSA keys.
   - The public key and private key are printed and returned as a JSON response.

8. Encryption (API Endpoint):
   - The `/encrypt` route is defined to encrypt the card details.
   - Inside the route, the `card_details` are obtained from the request JSON.
   - If the `card_details` is missing, an error response is returned.
   - The `generate_rsa_keys()` function is called to generate the RSA keys.
   - The symmetric key is used to create a cipher object for AES encryption in ECB mode.
   - The `card_details` are padded using PKCS7 padding.
   - The padded card details are encrypted using the symmetric key.
   - The symmetric key is encrypted using the public key and OAEP padding.
   - The encrypted card details and encrypted symmetric key are stored in the database using the `CardDetails` model.
   - The encrypted card details and encrypted symmetric key are returned as a JSON response.

9. Decryption (API Endpoint):
   - The `/decrypt` route is defined to decrypt the encrypted card details.
   - Inside the route, the `encrypted_card_details` and `encrypted_symmetric_key` are obtained from the request JSON.
   - If any of the required parameters are missing, an error response is returned.
   - The private key is used to decrypt the symmetric key using OAEP padding.
   - A cipher object is created using the decrypted symmetric key for AES decryption in ECB mode.
   - The encrypted card details are decrypted using the cipher object.
   - The decrypted card details are decoded to obtain the original string.
   - The decrypted card details are returned as a JSON response.

10. Running

 the Flask App:
    - The `app.run()` method is called to run the Flask application in debug mode.

That's the explanation of the provided code. It sets up a Flask app with endpoints for generating RSA keys, encrypting card details, and decrypting card details using RSA and AES encryption. The encrypted data is stored in a MySQL database using SQLAlchemy.