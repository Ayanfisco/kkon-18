from odoo import models, fields, SUPERUSER_ID


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    eservice_company_id = fields.Many2one(
        "res.company",
        string="Invoice Company",
        config_parameter="eservice_api.eservice_company_id",
    )
    deferred_revenue_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Deferred Revenue Account",
        config_parameter="eservice_api.deferred_revenue_account_id",
    )
    advance_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Advance Payment Account",
        config_parameter="eservice_api.advance_account_id",
    )

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        Param = self.env["ir.config_parameter"].with_user(
            SUPERUSER_ID
        )
        res.update(
            deferred_revenue_account_id=Param.get_param(
                "eservice_api.deferred_revenue_account_id"
            )
            and int(
                Param.get_param(
                    "eservice_api.deferred_revenue_account_id"
                )
            ),
            eservice_company_id=Param.get_param(
                "eservice_api.eservice_company_id"
            )
            and int(
                Param.get_param("eservice_api.eservice_company_id")
            ),
            advance_account_id=Param.get_param(
                "eservice_api.advance_account_id"
            )
            and int(
                Param.get_param("eservice_api.advance_account_id")
            ),
        )
        return res
