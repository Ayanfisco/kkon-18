from odoo import fields, models, api, _

class purchase_request(models.Model):
    _inherit = 'az.purchase.request'


    def action_approve(self):
        for record in self:
            record.state = 'approved'

    def action_cancel(self):
        for record in self:
            record.state = 'cancel'

    def action_in_progress(self ):
        for record in self:
            record.state = 'in_progress'

    def action_done(self):
        for record in self:
            record.state = 'done'

    def action_reset(self):
        for record in self:
            record.state = 'to_approve'