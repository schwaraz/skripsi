from flask import Flask, request, render_template, jsonify
import mysql.connector
from Crypto.Cipher import AES
import base64
import datetime
import jwt
from jwt.exceptions import ExpiredSignatureError
import dbsql


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
def tokencheck(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        exp = payload['exp']
        current_time = datetime.datetime.utcnow()
        if current_time > datetime.datetime.fromtimestamp(exp):
            return True  # Token has expired
        else:
            return False  # Token is still valid
    except jwt.ExpiredSignatureError:
        return True  # Token has expired
    except jwt.InvalidTokenError:
        return True  # Invalid token
def is_token_valid(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        cursor = db.cursor()
        sql = 'SELECT * FROM `user_token` WHERE `token` = %s'
        cursor.execute(sql,(token,))
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
            iduser=result[0]
            cursor.execute(sql, (result[0],))
            token_result = cursor.fetchone()
            if token_result is None:
                login_successful = True
            else:
                validasi=is_token_valid(token_result[1])
                if validasi==False:
                    newtoken=generate_token(email)
                    token_str = newtoken.decode('utf-8')
                    sql = "UPDATE user_token set token=%s where user_id=%s"
                    cursor.execute(sql, (newtoken,result[0]))
                    db.commit() 
                    cursor.close()
                    return jsonify(token=token_str,id=iduser)
                else:
                    cursor.close()
                    return jsonify(token=token_result[1],id=iduser)
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
        return jsonify(token=token_str,id=iduser)
    else:
        cursor.close()
        return "Login failed"
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

                return "Registration successful"
            else:
                return "Failed to register: Email already exists"
        except Exception as e:
            print("Failed to register:", e)
            return "Failed to register"

    else:
        return render_template("register.html")
@app.route("/history", methods=["post"])
def history():
    token = request.get_json().get("token")
    awal = request.get_json().get("datetimestart")
    akhir = request.get_json().get("datetimeend")
    if is_token_valid(token)==True:
        cursor = db.cursor()
        sql = 'SELECT * FROM `location` WHERE `timedate` > %s and timedate < %s '
        cursor.execute(sql,(awal,akhir))
        print(cursor)
        result = cursor.fetchall()
        data = []
        for row in result:
            data.append({'x': row[0], 'y': row[1], 'datetime': row[2]})
        return jsonify(data)
    else:
        return "token invalid"

@app.route("/validasi", methods=["POST"])
def validtoken():
    token = request.get_json().get("token")
    if(is_token_valid(token)==True):
        return jsonify("True")
    else:
        return jsonify("token invalid")
@app.route("/logout", methods=["POST"])
def logout():
    token = request.get_json().get("token")
    if(is_token_valid(token)==True):
        cursor = db.cursor()
        sql = 'DELETE FROM `user_token` WHERE `token` = %s '
        cursor.execute(sql,(token,))
        db.commit()
    else:
        return "gagal log out"
    if cursor.rowcount > 0:
        return "berhasil logout"
    else:
        return "gagal log out"
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)