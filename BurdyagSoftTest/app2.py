from flask import Flask, jsonify, request
import uuid, time

app = Flask(__name__)

USERS = {
    "alice@example.com": { "password": "pass123", "role": "user"},
    "admin@example.com": {"password":"admin1223","role": "admin"}
}

TOKENS = {

}


def require_bearer(req):
    auth = req.headers.get("Authorization","")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ",1)[1].strip()
    return TOKENS.get(token)


@app.get("/health")
def health():
    return jsonify({"ok":True})

@app.post("/login")
def login():
    data = request.get_json() or {}
    email = data.get("email")
    print(data)
    password = data.get("password")
    user = USERS.get(email)
    if not user or user["password"] != password:
        return jsonify({"error":"Credentials are bad"}), 401
    tok = str(uuid.uuid4())
    TOKENS[tok] = {'email':email, 'role': user['role']}
    time.sleep(0.15)
    return jsonify({'token':tok, 'role': user['role']})

@app.get("/me")
def me():
    princincipal  = require_bearer(request)
    if not princincipal:
        return jsonify({"error": "unauthorized"}),401
    return jsonify({"email":princincipal["email"], "role":princincipal["role"]})

@app.get("/admin")
def admin():
    princincipal  = require_bearer(request)
    if not princincipal:
        return jsonify({"error": "unauthorized"}),401
    if princincipal["role"] != "admin":
        return jsonify({"error": "forbidden"}),403
    return jsonify({"ok": True, "secret": "flag-123"})

@app.post("/logout")
def logout():
    princincipal  = require_bearer(request)
    if not princincipal:
        return jsonify({"error": "unauthorized"}),401
    token = request.headers.get("Authorization").split(" ",1)[1]
    TOKENS.pop(token, None)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)