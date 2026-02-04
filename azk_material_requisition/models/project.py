from odoo import models, fields

class Project(models.Model):
    _inherit = 'project.project'
    
    project_location_id = fields.Many2one('stock.location', string='Project Location')