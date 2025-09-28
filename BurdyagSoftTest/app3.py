from flask import Flask, request
import uuid,time

app = Flask(__name__)


USERS = { "alice@example.com":{"password": "pass123","role":"user"},
         "admin@example.com":{"password": "admin123","role":"admin"}
        }

TOKENS = {}

# bearer sdfgyuiolkhgtre323456yhgvfdr
def requirer_bearer(req):
    auth= req.headers.get("Authorization","")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ",1)[1].strip()
    return TOKENS.get(token)

@app.get('/health')
def health():
    return {"status": "ok"}

@app.post("/login")
def login():
    data = request.get_json()
    print(data)
    email = data.get('email')
    password = data.get('password')
    user = USERS.get(email)
    if not user or user['password'] != password:
        return {"error": "Credentials are bad"},401
    tok = str(uuid.uuid4())
    TOKENS[tok] = {"email":email, 'role':user['role']}
    time.sleep(0.15)
    return {"token": tok,'role': user['role']}


@app.get("/me")
def me():
   principals = requirer_bearer(request)
   if not principals:
       return {"error": "unauthorized"}, 401
   return {"email": principals["email"], "role":principals['role']}



if __name__ == "__main__":
    app.run(host='127.0.0.1' , port=5000)
