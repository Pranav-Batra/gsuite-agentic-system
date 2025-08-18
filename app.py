from flask import Flask, request, jsonify, render_template
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
import jwt, datetime, os
from dotenv import load_dotenv
from client.gsuite_client_two import make_request

load_dotenv('/Users/pranav/Desktop/GSuite-MCP/.env')

app = Flask(__name__)
SECRET_KEY = os.getenv("MY_APP_SECRET", "supersecret")  # your app’s key

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

@app.route("/auth/google", methods=["POST"])
def google_auth():
    token = request.json.get("id_token")
    try:
        # Verify Google token
        idinfo = id_token.verify_oauth2_token(token, grequests.Request(), GOOGLE_CLIENT_ID)
        email = idinfo["email"]

        # Issue your own JWT session
        payload = {
            "email": email,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        session_token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        return jsonify({"session_token": session_token, "email": email})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/main/', methods=['GET', 'POST', 'OPTIONS'])
def client_request():
    print('method used: ', request.method)
    if request.method == 'POST':
        user_text = request.form.get('user_input')
        print("User input received: ", user_text)

        result = make_request(user_text)
        return jsonify({"result": result})
    return render_template("main.html")

app.run(port=8080)