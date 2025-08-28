import os
import json
from flask import Flask, request, jsonify, render_template, redirect, session, url_for
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from dotenv import load_dotenv
import psycopg

load_dotenv('/Users/pranav/Desktop/GSuite-MCP/.env')
# GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")  # optional: used if you want to inspect id_token later
DB_NAME = os.getenv('DBNAME')
DB_USER = os.getenv('DBUSER')
DB_PASSWORD = os.getenv('DBPASSWORD')
DB_PORT = os.getenv('DBPORT')

try:
    conn = psycopg.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT, autocommit=True)
    cursor = conn.cursor()
    print("PostgreSQL connection established successfully!")
except Exception as e:
    print(f"Error connecting to PostgreSQL: {e}")
    conn = None
    cursor = None

REDIRECT_URI = "http://localhost:8080/oauth2callback"
CLIENT_SECRETS_FILE = "credentials.json"
SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/calendar",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]
from client.gsuite_client_two import make_request  

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-key-for-dev")

#local dev
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# currently in-memory to store tokens -> replace with db 
USER_TOKENS = {}  # { email: {refresh_token: "..."} }

def get_google_client_config():
    with open(CLIENT_SECRETS_FILE, "r") as f:
        return json.load(f).get("web", {})

# def build_user_credentials_from_refresh(refresh_token: str) -> Credentials:
#     cfg = get_google_client_config()
#     return Credentials(
#         token=None,  # will be refreshed automatically
#         refresh_token=refresh_token,
#         token_uri="https://oauth2.googleapis.com/token",
#         client_id=cfg.get("client_id"),
#         client_secret=cfg.get("client_secret"),
#         scopes=SCOPES,
#     )

# ---------------- Routes ----------------

@app.route("/")
def index():
    if "email" in session:
        return redirect(url_for("client_request"))
    # Simple page with a link to start OAuth flow
    return render_template('login.html')

@app.route("/login")
def login():
    """
    Starts the Google OAuth Authorization Code flow.
    """
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI
    )
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",  # ensure refresh_token on every run during dev
    )
    session["state"] = state
    print("Stored state:", state)
    return redirect(authorization_url)

@app.route("/oauth2callback")
def oauth2callback():
    """
    Handles Google's redirect, validates state, exchanges code for tokens,
    and stores a refresh token per user.
    """
    incoming_state = request.args.get("state")
    stored_state = session.get("state")
    print("Incoming state:", incoming_state)
    print("Stored state:", stored_state)

    if not incoming_state or incoming_state != stored_state:
        return "State mismatch. Please try logging in again.", 400

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=incoming_state, redirect_uri=REDIRECT_URI
    )
    # Exchange code for tokens
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials  # has access_token, refresh_token, id_token (maybe)

    email = None
    if creds.id_token:
        try:
            info = id_token.verify_oauth2_token(creds.id_token, grequests.Request(), creds.client_id)
            email = info.get("email")
        except Exception as e:
            print(f"ID token verification failed: {e}")

    if not email:
        return "Unable to determine user email from id_token.", 400

    session["email"] = email

    # Persist refresh token
    if creds.refresh_token:
        try:
            sql_query = """
            INSERT INTO gsuite_users (email, refresh_token, s3_bucket_path)
            VALUES (%s, %s, %s)
            ON CONFLICT (email) DO UPDATE SET
                refresh_token = EXCLUDED.refresh_token,
                s3_bucket_path = EXCLUDED.s3_bucket_path;
            """
            cursor.execute(sql_query, (email, creds.refresh_token, f'gsuite-mcp-logs/{email}'))
        # USER_TOKENS[email] = {"refresh_token": creds.refresh_token}
            print(f"Stored refresh token for {email}")
        except Exception as e:
            print("Didn't insert due to ", e)
    else:
        print(f"Warning: No refresh_token for {email}.")
        cursor.execute("SELECT email FROM gsuite_users WHERE email = %s", (email,))
        if not cursor.fetchall():
            return ("No refresh token received.\n You may need to remove the app "
            "from https://myaccount.google.com/permissions and try again."), 400
        # if email not in USER_TOKENS:
        #     return ("No refresh token received.\n You may need to remove the app "
        #     "from https://myaccount.google.com/permissions and try again."), 400

    return redirect(url_for("client_request"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/main/", methods=["GET", "POST"])
def client_request():
    """
    Main page. POST accepts user input and routes to MCP client with user creds.
    """
    if "email" not in session:
        return redirect(url_for("index"))

    user_email = session["email"]

    if request.method == "POST":
        user_text = request.form.get("user_input") or (request.json or {}).get("user_input")
        print(f"User input from {user_email}: {user_text}")

        cursor.execute("SELECT refresh_token FROM gsuite_users WHERE email = %s", (user_email,))
        rt = cursor.fetchone()
        rt = rt[0]

        # rt = USER_TOKENS.get(user_email, {}).get("refresh_token")
        if not rt:
            return jsonify({"error": "Missing refresh token. Please log out and log in again."}), 400

        cfg = get_google_client_config()

        # Credentials dict passed to MCP client
        user_credentials = {
            "refresh_token": rt,
            "client_id": cfg.get("client_id"),
            "client_secret": cfg.get("client_secret"),
            "token_uri": "https://oauth2.googleapis.com/token",
            "scopes": SCOPES,
        }

        try:
            result = make_request(user_text, user_credentials, user_email)
            return jsonify({"result": result})
        except Exception as e:
            print("MCP error:", e)
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    # Simple form UI for quick testing
    return render_template('main.html', user_email=user_email)
    # return f"""
    # <html>
    #   <body>
    #     <p>Signed in as <b>{user_email}</b></p>
    #     <form method="POST">
    #       <input name="user_input" placeholder="Ask Google APIs via MCP" style="width:300px"/>
    #       <button type="submit">Send</button>
    #     </form>
    #     <p><a href="/logout">Logout</a></p>
    #   </body>
    # </html>
    # """

if __name__ == "__main__":
    app.run(port=8080, debug=True, use_reloader=False)
