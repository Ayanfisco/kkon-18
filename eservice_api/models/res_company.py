from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    payment_term_id = fields.Many2one("account.payment.term", string="Payment Term")
