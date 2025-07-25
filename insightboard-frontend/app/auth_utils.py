from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from flask import jsonify

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()  # Make sure JWT exists and is valid
        claims = get_jwt()
        if claims.get("priv") != "admin":
            return jsonify(msg="Admin privileges required"), 403
        return fn(*args, **kwargs)
    return wrapper
