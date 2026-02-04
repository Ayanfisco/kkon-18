from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    advance_settlement_journal_id = fields.Many2one(
        "account.journal", string="Advance Settlement Journal"
    )
    advance_account_id = fields.Many2one("account.account", string="Advance Account")
