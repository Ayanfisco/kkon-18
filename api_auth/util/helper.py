import jwt
import json
import logging
import functools
import werkzeug.wrappers
from datetime import datetime
from odoo import api, SUPERUSER_ID
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone

from typing import Union, Any

try:
    from odoo.http import request
except RuntimeError:
    pass


RES_CONFIG_SETTINGS = "res.config.settings"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10
SECRET_KEY = "xlyinWyXx3iNYao7JmiKXucdJGdvbM9X94L4t0uIEHQ="


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None, secret_key: str = ""
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def get_token_secret_expires_delta(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    config_values = env[RES_CONFIG_SETTINGS].get_values()
    expires_delta = int(config_values.get("token_expires_delta", ACCESS_TOKEN_EXPIRE_MINUTES))
    token_secret = config_values.get("token_secret", SECRET_KEY)
    return expires_delta, token_secret


def validate_token(func):
    """validate the JWT token generated"""
    try:
        cr = request._cr
    except:
        cr = False

    @functools.wraps(func)
    def wrap(*args, **kwargs):
        """."""
        token = request.httprequest.headers.get("token")
        if not token:
            return invalid_response(
                "token_not_found",
                "Please provide token in the request header",
                401,
            )
        try:
            secret_key = request.env["res.config.settings"].get_values().get("token_secret", SECRET_KEY)
            payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
            payload = SimpleNamespace(**payload)
            request.session.uid = int(payload.sub)
            request.update_env(user=request.env["res.users"].browse([int(payload.sub)]))
        except (
            jwt.exceptions.InvalidTokenError,
            jwt.exceptions.DecodeError,
        ) as e:
            return invalid_response("Invalid", "Token is invalid!", 401)
        except Exception as e:
            print("Error {}".format(e))
        return func(*args, **kwargs)

    return wrap


def invalid_response(type, message=None, status=401):
    """Invalid Response
    This will be the return value whenever the server runs into an error
    either from the client or the server."""
    return werkzeug.wrappers.Response(
        status=status,
        content_type="application/json; charset=utf-8",
        response=json.dumps(
            {
                "type": type,
                "message": (
                    str(message)
                    if str(message)
                    else "wrong arguments (missing validation)"
                ),
            },
            default=datetime.isoformat,
        ),
    )
