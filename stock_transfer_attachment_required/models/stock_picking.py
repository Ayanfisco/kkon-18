from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    def _has_attachment(self):
        self.ensure_one()
        attachment_count = self.env['ir.attachment'].search_count([
            ('res_model', '=', 'stock.picking'),
            ('res_id', '=', self.id)
        ])
        return attachment_count > 0

    def button_validate(self):
        _logger.info("Custom button_validate method called")
        for picking in self:
            _logger.info(f"Checking attachments for picking {picking.name}")
            if not picking._has_attachment():
                _logger.error(f"Validation failed: No attachment found for picking {picking.name}")
                raise UserError(_("You must attach a waybill document before validating this transfer."))
        _logger.info("Calling super method")
        return super(StockPicking, self).button_validate()

    def action_confirm(self):
        _logger.info("Custom action_confirm method called")
        for picking in self:
            if picking.state == 'draft' and not picking._has_attachment():
                _logger.error(f"Validation failed: No attachment found for picking {picking.name}")
                raise UserError(_("You must attach a waybill document before confirming this transfer."))
        return super(StockPicking, self).action_confirm()

    @api.constrains('state')
    def _check_attachment_before_done(self):
        for picking in self:
            if picking.state == 'done' and not picking._has_attachment():
                _logger.error(f"Validation failed: No attachment found for picking {picking.name}")
                raise ValidationError(_("You must attach a waybill document before completing this transfer."))
