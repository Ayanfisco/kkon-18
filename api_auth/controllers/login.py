from odoo import http, _, api, SUPERUSER_ID
from odoo.http import request
from odoo.exceptions import AccessDenied
from ..util.helper import (
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_token_secret_expires_delta,
    create_access_token
)


class LoginController(http.Controller):

    @http.route(
        "/api/v1/login",
        type="http",
        website=False,
        auth="none",
        methods=["POST"],
        csrf=False,
    )
    def log_me_in(self, **kwargs):
        values = dict()
        if request.httprequest.method == "POST":
            try:
                uid = request.session.authenticate(
                    request.db,
                    request.params["login"],
                    request.params["password"],
                )
                expires_delta, secret_key = get_token_secret_expires_delta(request._cr)
                print("&&&&&&&&&&&&&&&", get_token_secret_expires_delta(request._cr))
                user = request.env["res.users"].sudo().browse([int(uid)])
                return request.make_json_response(
                    {
                        "access_token": create_access_token(
                            uid, expires_delta=expires_delta, secret_key=secret_key
                        ),
                        "token_type": "bearer",
                        "user": {
                            "id": uid,
                            "login": user.login,
                            "email": user.email,
                        },
                    }
                )
            except AccessDenied as e:
                if e.args == AccessDenied().args:
                    values["error"] = _("Wrong login/password")
                else:
                    values["error"] = e.args[0]
        else:
            if "error" in request.params and request.params.get("error") == "access":
                values["error"] = _(
                    "Only employees can access this database. Please contact the administrator."
                )
