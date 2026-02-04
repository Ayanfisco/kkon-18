from odoo import models, fields, api

class StockQuantExtend(models.Model):
    _inherit = 'stock.quant'
    
    unit_cost = fields.Float(string='Unit Cost', compute='_compute_unit_cost', store=False)
    total_value = fields.Float(string='Total Value', compute='_compute_total_value', store=False)
    incoming_qty = fields.Float(string='Incoming', compute='_compute_incoming_outgoing', store=False)
    outgoing_qty = fields.Float(string='Outgoing', compute='_compute_incoming_outgoing', store=False)
    free_qty = fields.Float(string='Free Quantity', compute='_compute_free_qty', store=False)
    unit = fields.Char(string='Unit', compute='_compute_unit', store=False)
    
    @api.depends('product_id')
    def _compute_unit_cost(self):
        for quant in self:
            quant.unit_cost = quant.product_id.standard_price if quant.product_id else 0.0
    
    @api.depends('quantity', 'product_id')
    def _compute_total_value(self):
        for quant in self:
            quant.total_value = quant.quantity * quant.product_id.standard_price if quant.product_id else 0.0
    
    @api.depends('product_id')
    def _compute_incoming_outgoing(self):
        for quant in self:
            if quant.product_id:
                quant.incoming_qty = quant.product_id.incoming_qty
                quant.outgoing_qty = quant.product_id.outgoing_qty
            else:
                quant.incoming_qty = 0.0
                quant.outgoing_qty = 0.0
    
    @api.depends('product_id')
    def _compute_free_qty(self):
        for quant in self:
            quant.free_qty = quant.product_id.free_qty if quant.product_id else 0.0
    
    @api.depends('product_id')
    def _compute_unit(self):
        for quant in self:
            quant.unit = quant.product_id.uom_id.name if quant.product_id and quant.product_id.uom_id else ''
    
    def action_product_forecast_report(self):
        self.ensure_one()
        if self.product_id:
            return self.product_id.action_product_forecast_report()
        return {'type': 'ir.actions.act_window_close'}
    
    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """Override to dynamically change total_value field label"""
        result = super().fields_get(allfields, attributes)
        
        if 'total_value' in result:
            dynamic_value = self._get_total_stock_value()
            result['total_value']['string'] = f'Total Value ({self.env.company.currency_id.symbol}{dynamic_value:,.2f})'
        
        return result
    
    def _get_total_stock_value(self):
        """Calculate the total stock value for the selected location only"""
        location_id = self.env.context.get('location_id')
        domain = [('location_id.usage', '=', 'internal')]
        if location_id:
            domain.append(('location_id', '=', location_id))
        quants = self.search(domain)
        total = sum(quant.quantity * (quant.product_id.standard_price or 0.0) for quant in quants)
        return total