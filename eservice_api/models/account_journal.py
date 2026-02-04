from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = "account.journal"

    eservice_code = fields.Char("eService Reference")
    deferred_revenue_reversal = fields.Boolean("Deferred Reversal")
