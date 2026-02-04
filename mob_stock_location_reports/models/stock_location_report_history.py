from odoo import models, fields, api, _
from odoo.osv import expression
from odoo.tools.misc import format_datetime

class StockQuantityHistory(models.TransientModel):
    _inherit = 'stock.quantity.history'

    location_id = fields.Many2one(
        'stock.location',
        string='Location',
        required=True,
        domain=[('usage', '=', 'internal')],
        help='Select the stock location to view stock history'
    )
    start_date = fields.Datetime('Start Date', required=True, help='Start date for inventory history')
    end_date = fields.Datetime('End Date', required=True, help='End date for inventory history')

    @api.model
    def default_get(self, fields_list):
        result = super().default_get(fields_list)
        # Use context default_location_id if present
        location_id = self.env.context.get('default_location_id')
        if 'location_id' in fields_list and not result.get('location_id') and location_id:
            result['location_id'] = location_id
        elif 'location_id' in fields_list and not result.get('location_id'):
            location = self.env['stock.location'].search([('usage', '=', 'internal')], limit=1)
            if location:
                result['location_id'] = location.id
        return result

    def open_at_date(self):
        self.ensure_one()
        tree_view_id = self.env.ref('stock.view_stock_product_tree').id
        form_view_id = self.env.ref('stock.product_form_view_procurement_button').id
        domain = [('type', '=', 'product')]
        # Filter by location if set
        if self.location_id:
            domain = expression.AND([domain, [('stock_quant_ids.location_id', '=', self.location_id.id)]])
        # We pass `from_date` and `to_date` in the context so that `qty_available` will be computed across moves in the range.
        action = {
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_mode': 'tree,form',
            'name': _('Products'),
            'res_model': 'product.product',
            'domain': domain,
            'context': dict(self.env.context, from_date=self.start_date, to_date=self.end_date, location_id=self.location_id.id if self.location_id else False),
            'display_name': _('%s to %s') % (format_datetime(self.env, self.start_date), format_datetime(self.env, self.end_date)),
        }
        return action 