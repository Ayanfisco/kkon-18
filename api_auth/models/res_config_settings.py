from odoo import models, fields, SUPERUSER_ID


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    token_expires_delta = fields.Integer(
        string="Token Expiration",
        config_parameter="api_auth.token_expires_delta",
    )
    token_secret = fields.Char(
        string="Secret",
        config_parameter="api_auth.token_secret",
    )

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        Param = self.env["ir.config_parameter"].with_user(SUPERUSER_ID)
        res.update(
            token_expires_delta=Param.get_param("api_auth.token_expires_delta")
            and int(Param.get_param("api_auth.token_expires_delta")),
            token_secret=Param.get_param("api_auth.token_secret", ""),
        )
        return res
