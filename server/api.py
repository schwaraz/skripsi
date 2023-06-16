from flask import Flask, request, render_template, jsonify
import mysql.connector
from Crypto.Cipher import AES
import base64
import datetime
import jwt
from jwt.exceptions import ExpiredSignatureError
import dbsql

import os

import logging
from logging.handlers import TimedRotatingFileHandler

# Inisialisasi logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Get the path to the log folder
log_folder = os.path.join(os.getcwd(), "log")

# Create the log folder if it doesn't exist
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

current_date = datetime.date.today()
# Convert the current_date object to a string representation
formatted_date = current_date.strftime("%Y-%m-%d")
# Specify the log file path
log_filename = os.path.join(log_folder, "api_" + formatted_date + ".log")

file_handler = TimedRotatingFileHandler(log_filename, when="midnight", interval=1, backupCount=7)

# Menentukan format log
log_format = "%(asctime)s - %(levelname)s - %(message)s"
formatter = logging.Formatter(log_format)
file_handler.setFormatter(formatter)

# Menambahkan handler ke logger
logger.addHandler(file_handler)
logger.info("starting api")

app = Flask(__name__)
# Connect to the MySQL database
db = mysql.connector.connect(
    host=dbsql.host, user=dbsql.user, password=dbsql.password, database=dbsql.database
)

SECRET_KEY = b"this_is_secretka"  # Replace with your own secret key
INIT_VECTOR = b"y19mg85vk8tn1oih"  # Replace with your own initialization vector
TOKEN_EXPIRATION_TIME = 24  # Token expiration time in hours


def encrypt(plaintext):
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, INIT_VECTOR)
    padded_plaintext = plaintext + (
        AES.block_size - len(plaintext) % AES.block_size
    ) * chr(AES.block_size - len(plaintext) % AES.block_size)
    ciphertext = cipher.encrypt(padded_plaintext.encode())
    return base64.b64encode(ciphertext).decode()


def generate_token(email):
    payload = {
        "email": email,
        "exp": datetime.datetime.utcnow()
         + datetime.timedelta(days=TOKEN_EXPIRATION_TIME),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token





def is_token_valid(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        cursor = db.cursor()
        sql = 'SELECT * FROM `user_token` WHERE `token` = %s'
        cursor.execute(sql, (token,))
        result = cursor.fetchone()
        cursor.close()
        if result is None:
            return False
        else:
            return True
    except jwt.ExpiredSignatureError:
        return False  # Token has expired
    except jwt.InvalidTokenError:
        return False  # Invalid token


def decrypt(ciphertext):
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, INIT_VECTOR)
    decrypted = cipher.decrypt(base64.b64decode(ciphertext)).rstrip(b"\0").decode()
    return decrypted


@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.json
        email = data["email"]
        password = decrypt(data["password"])
        # Perform your login verification
        # Get Data from MySQL
        print(email)
        cursor = db.cursor()
        sql = "SELECT * FROM user WHERE email = %s"
        cursor.execute(sql, (email,))
        result = cursor.fetchone()
        if result is None:
            cursor.close()
            # return "Login failed"
            return "email atau password salah"
        else:
            stored_password = decrypt(result[3])
            if password == stored_password:
                sql = "SELECT * FROM user_token WHERE user_id = %s"
                iduser = result[0]
                cursor.execute(sql, (result[0],))
                token_result = cursor.fetchone()
                if token_result is None:
                    login_successful = True
                else:
                    validasi = is_token_valid(token_result[1])
                    if validasi == False:
                        newtoken = generate_token(email)
                        token_str = newtoken.decode('utf-8')
                        sql = "UPDATE user_token set token=%s where user_id=%s"
                        cursor.execute(sql, (newtoken, result[0]))
                        db.commit()
                        cursor.close()
                        return jsonify(token=token_str, id=iduser)
                    else:
                        cursor.close()
                        return jsonify(token=token_result[1], id=iduser)
            else:
                return "email atau password salah"
        if login_successful:
            # Generate a token
            token = generate_token(email)
            # Store the token in a separate table
            sql = "INSERT INTO user_token (user_id, token) VALUES (%s, %s)"
            cursor.execute(sql, (result[0], token))
            db.commit()
            cursor.close()
            token_str = token.decode('utf-8')
            return jsonify(token=token_str, id=iduser)
        else:
            cursor.close()
            return "Login failed"
    except Exception as e:
        logger.error("Error occurred in login API: %s", str(e))
        return "An error occurred during login."


def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        expiration_time = datetime.datetime.strptime(
            payload["exp"], "%Y-%m-%d %H:%M:%S"
        )
        current_time = datetime.datetime.utcnow()
        if current_time > expiration_time:
            return None  # Token is expired
        else:
            return payload  # Token is valid
    except ExpiredSignatureError:
        return False
    except Exception:
        return False


@app.route("/register", methods=["POST", "GET"])
def register():
    try:
        if request.method == "POST":
            name = request.get_json().get("name")
            email = request.get_json().get("email")
            password = encrypt(request.get_json().get("password"))

            try:
                # Get Data from MySQL
                cursor = db.cursor()
                sql = "SELECT id FROM user WHERE email = %s"
                cursor.execute(sql, (email,))
                result = cursor.fetchone()
                if result is None:
                    # Input Data into MySQL
                    sql = "INSERT INTO user (name, email, password) VALUES (%s, %s, %s)"
                    cursor.execute(sql, (name, email, password))
                    db.commit()
                    cursor.close()
                    logger.info("new user: %s has been create", email)

                    return "Registration successful"
                else:
                    return "Failed to register: Email already exists"
            except Exception as e:
                logger.error("Error occurred in register API: %s", str(e))
                return "Failed to register"


    except Exception as e:
        logger.error("Error occurred in register API: %s", str(e))
        return "An error occurred during registration."


@app.route("/history", methods=["POST"])
def history():
    try:
        token = request.get_json().get("token")
        awal = request.get_json().get("datetimestart")
        akhir = request.get_json().get("datetimeend")
        print(awal)
        print(akhir)
        if is_token_valid(token) == True:
            cursor = db.cursor()
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            email = payload["email"]
            sql = 'SELECT * FROM `location` WHERE `timedate` > %s and timedate < %s '
            cursor.execute(sql, (awal, akhir))
            print(cursor)
            result = cursor.fetchall()
            data = []
            for row in result:
                data.append({'x': row[0], 'y': row[1], 'datetime': row[2]})
            logger.info("User's history retrieved: %s with data in range %s %s", email,awal,akhir)
            return jsonify(data)
        else:
            return "token invalid"
    except Exception as e:
        logger.error("Error occurred in history API: %s", str(e))
        return "An error occurred during history retrieval."


@app.route("/validasi", methods=["POST"])
def validtoken():
    try:
        token = request.get_json().get("token")
        if(is_token_valid(token) == True):
            return jsonify("True")
        else:
            return jsonify("token invalid")
    except Exception as e:
        logger.error("Error occurred in validtoken API: %s", str(e))
        return "An error occurred during token validation."


@app.route("/logout", methods=["POST"])
def logout():
    try:
        token = request.get_json().get("token")
        if(is_token_valid(token) == True):
            cursor = db.cursor()
            sql = 'DELETE FROM `user_token` WHERE `token` = %s '
            cursor.execute(sql, (token,))
            db.commit()
        else:
            return "gagal log out"
        if cursor.rowcount > 0:
            return "berhasil logout"
        else:
            return "gagal log out"
    except Exception as e:
        logger.error("Error occurred in logout API: %s", str(e))
        return "An error occurred during logout."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)