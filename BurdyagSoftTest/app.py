from flask import Flask, jsonify, request
import uuid, time, re

app = Flask(__name__)

USERS = {
    "alice@example.com": { "password": "pass123", "role": "user"},
    "admin@example.com": {"password":"admin123","role": "admin"}
}

TOKENS = {}

ORDERS = {}
def require_bearer(req):
    auth = req.headers.get("Authorization","")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ",1)[1].strip()
    return TOKENS.get(token)

@app.get("/health")
def health():
    return jsonify({"ok":True})

@app.post("/register")
def register():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    if not email or "@" not in email:
        return jsonify({"error": "Email is required and must be valid"}), 400
    if not password or len(password) < 6:
        return jsonify({"error": "Password is required and must be at least 6 characters long"}), 400
    if email in USERS:
        return jsonify({"error": "Email already registered"}), 409
    USERS[email] = {"password": password, "role": "user"}
    tok = str(uuid.uuid4())
    TOKENS[tok] = {'email': email, 'role': 'user'}
    
    return jsonify({'token': tok, 'email': email, 'role': 'user'}), 201

@app.post("/login")
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    user = USERS.get(email)

    if not user or user["password"] != password:
        return jsonify({"error":"Credentials are bad"}), 401
    
    tok = str(uuid.uuid4())
    TOKENS[tok] = {'email':email, 'role': user['role']}
    time.sleep(0.15)
    return jsonify({'token':tok, 'role': user['role']})

@app.post("/logout")
def logout():
    principal = require_bearer(request)
    if not principal:
        return jsonify({"error": "unauthorized"}), 401
    
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.split(" ", 1)[1].strip()
    if token in TOKENS:
        del TOKENS[token]
        
    return jsonify({"ok": True})


@app.get("/me")
def me():
    principal  = require_bearer(request)
    if not principal:
        return jsonify({"error": "unauthorized"}),401
    return jsonify({"email":principal["email"], "role":principal["role"]})

@app.post("/change-password")
def change_password():
    principal = require_bearer(request)
    if not principal:
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json() or {}
    old_password = data.get("old_password")
    new_password = data.get("new_password")
    
    email = principal['email']
    user = USERS[email]

    # Валидация
    if user['password'] != old_password:
        return jsonify({"error": "Old password does not match"}), 400
    if not new_password or len(new_password) < 6:
        return jsonify({"error": "New password must be at least 6 characters long"}), 400
    if old_password == new_password:
        return jsonify({"error": "New password cannot be the same as the old one"}), 400
    user['password'] = new_password
    old_token = request.headers.get("Authorization").split(" ", 1)[1].strip()
    if old_token in TOKENS:
        del TOKENS[old_token]
    new_token_str = str(uuid.uuid4())
    TOKENS[new_token_str] = {'email': email, 'role': user['role']}
    
    return jsonify({"token": new_token_str})


@app.get("/admin")
def admin():
    principal  = require_bearer(request)
    if not principal:
        return jsonify({"error": "unauthorized"}),401
    if principal["role"] != "admin":
        return jsonify({"error": "forbidden"}),403
    return jsonify({"ok": True, "secret": "flag-123"})


@app.post("/orders")
def create_order():
    principal = require_bearer(request)
    if not principal:
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json() or {}
    item_id = data.get("item_id")
    qty = data.get("qty")
    if not item_id:
        return jsonify({"error": "item_id is required"}), 400
    if not isinstance(qty, int) or not (1 <= qty <= 10):
        return jsonify({"error": "qty must be an integer between 1 and 10"}), 400
    
    order_id = str(uuid.uuid4())
    ORDERS[order_id] = {
        "id": order_id,
        "owner": principal["email"],
        "item_id": item_id,
        "qty": qty,
        "status": "created"
    }
    time.sleep(0.1)
    return jsonify(ORDERS[order_id]), 201

@app.get("/orders")
def get_orders():
    principal = require_bearer(request)
    if not principal:
        return jsonify({"error": "unauthorized"}), 401

    # Пагинация
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
    except ValueError:
        return jsonify({"error": "page and page_size must be integers"}), 400
    
    page_size = min(page_size, 50) # Максимум 50
    
    user_orders = [order for order in ORDERS.values() if order["owner"] == principal["email"]]
    
    start = (page - 1) * page_size
    end = start + page_size
    
    return jsonify({
        "items": user_orders[start:end],
        "page": page,
        "page_size": page_size,
        "total": len(user_orders)
    })

@app.get("/orders/<string:order_id>")
def get_order_by_id(order_id):
    principal = require_bearer(request)
    if not principal:
        return jsonify({"error": "unauthorized"}), 401

    order = ORDERS.get(order_id)
    if not order:
        return jsonify({"error": "Not Found"}), 404

    # владелец или админ
    if order["owner"] != principal["email"] and principal["role"] != "admin":
        return jsonify({"error": "forbidden"}), 403
        
    return jsonify(order)


if __name__ == "__main__":

    app.run(host="127.0.0.1", port=5000)
