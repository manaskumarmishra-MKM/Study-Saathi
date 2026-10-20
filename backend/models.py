"""models.py — StudySaathi v3 © Manas Kumar Mishra"""
import hashlib, hmac, base64, json, time, os, secrets
SECRET = os.environ.get("SS3_SECRET","studysaathi-v3-secret-key-change-in-prod")
def hash_pw(pw):
    salt=secrets.token_hex(16)
    h=hashlib.pbkdf2_hmac("sha256",pw.encode(),salt.encode(),310000)
    return f"{salt}:{h.hex()}"
def check_pw(pw,stored):
    try:
        salt,hx=stored.split(":",1)
        h=hashlib.pbkdf2_hmac("sha256",pw.encode(),salt.encode(),310000)
        return hmac.compare_digest(h.hex(),hx)
    except: return False
def make_token(uid,name,email):
    payload={"id":uid,"name":name,"email":email,"exp":int(time.time())+86400*14}
    data=base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    sig=hmac.new(SECRET.encode(),data.encode(),hashlib.sha256).hexdigest()
    return f"{data}.{sig}"
def verify_token(token):
    try:
        data,sig=token.rsplit(".",1)
        expected=hmac.new(SECRET.encode(),data.encode(),hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig,expected): return None
        payload=json.loads(base64.urlsafe_b64decode(data+"=="))
        if payload.get("exp",0)<time.time(): return None
        return payload
    except: return None
def auth_required(f):
    from functools import wraps
    from flask import request,jsonify
    @wraps(f)
    def wrapper(*args,**kwargs):
        token=request.headers.get("Authorization","").replace("Bearer ","").strip()
        user=verify_token(token)
        if not user: return jsonify({"error":"Unauthorized"}),401
        return f(user,*args,**kwargs)
    return wrapper
