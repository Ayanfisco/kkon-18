from odoo import models, fields, SUPERUSER_ID


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    default_journal_id = fields.Many2one(
        "account.journal", string="Journal", default_model="advance.payment.settlement"
    )
    default_advance_account_id = fields.Many2one(
        comodel_name="account.account", default_model="account.payment"
    )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        company = self.env.company
        if company:
            company.write(
                {
                    "advance_settlement_journal_id": self.default_journal_id.id,
                    "advance_account_id": self.default_advance_account_id.id,
                }
            )

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        company = self.env.company
        res.update(
            default_journal_id=company.advance_settlement_journal_id.id,
            default_advance_account_id=company.advance_account_id.id,
        )
        return res
