from odoo import models, fields

class ResCompany(models.Model):
    _inherit = "res.company"
    
    csv_template = fields.Many2one('ir.attachment', string='Material Items CSV Template')