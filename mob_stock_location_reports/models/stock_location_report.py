from odoo import models, fields, api


class StockLocationReport(models.TransientModel):
    _name = 'stock.location.report'
    _description = 'Stock Location Report'

    location_id = fields.Many2one(
        'stock.location',
        string='Location',
        required=True,
        domain=[('usage', '=', 'internal')],
        help='Select the stock location to view current stock'
    )

    @api.model
    def default_get(self, fields_list):
        """Set default location to the first internal location"""
        result = super().default_get(fields_list)
        if 'location_id' in fields_list and not result.get('location_id'):
            location = self.env['stock.location'].search([('usage', '=', 'internal')], limit=1)
            if location:
                result['location_id'] = location.id
        return result

    def action_view_stock_quants(self):
        """Action to view stock quants for the selected location"""
        self.ensure_one()
        return {
            'name': f'Current Stock - {self.location_id.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.quant',
            'view_mode': 'tree,form',
            'domain': [('location_id', '=', self.location_id.id), ('quantity', '>', 0)],
            'context': {
                'search_default_locationgroup': 1,
                'search_default_internal_loc': 1,
                'location_id': self.location_id.id,
            },
            'target': 'current',
        }

    def action_open_inventory_at_date(self):
        """Open the inventory at date wizard with the selected location as default."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.quantity.history',
            'view_mode': 'form',
            'target': 'new',
            'context': dict(self.env.context, default_location_id=self.location_id.id),
        }

    def name_get(self):
        result = []
        for record in self:
            location_name = record.location_id.name or 'No Location'
            name = f'Stock Location Report ({location_name})'
            result.append((record.id, name))
        return result


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def get_current_stock_action(self, location_id):
        """Method to get current stock action for a specific location"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Current Stock',
            'res_model': 'stock.quant',
            'view_mode': 'tree',
            'domain': [('location_id', '=', location_id), ('quantity', '>', 0)],
            'context': {
                'search_default_locationgroup': 1,
                'search_default_internal_loc': 1,
            },
            'target': 'current',
        }