from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ContractContractInheritedExtended(models.Model):
    _inherit = 'contract.contract'
    
    partner_full_address = fields.Char(
        string='Partner Full Address',
        compute='_compute_partner_full_address',
        store=True
    )
    
    @api.depends('partner_id', 'partner_id.street', 'partner_id.street2', 
                 'partner_id.city', 'partner_id.state_id', 'partner_id.country_id')
    def _compute_partner_full_address(self):
        for record in self:
            if record.partner_id:
                address_parts = []
                if record.partner_id.street:
                    address_parts.append(record.partner_id.street)
                if record.partner_id.street2:
                    address_parts.append(record.partner_id.street2)
                if record.partner_id.city:
                    address_parts.append(record.partner_id.city)
                if record.partner_id.state_id:
                    address_parts.append(record.partner_id.state_id.name)
                if record.partner_id.country_id:
                    address_parts.append(record.partner_id.country_id.name)
                
                record.partner_full_address = ', '.join(filter(None, address_parts))
            else:
                record.partner_full_address = False

    def _prepare_recurring_invoices_values(self, date_ref=False):
        """Override to replace name with address during initial creation"""
        values_list = super()._prepare_recurring_invoices_values(date_ref)
        
        for values in values_list:
            if values.get('invoice_line_ids') and self.partner_full_address:
                for line_command in values['invoice_line_ids']:
                    if line_command[0] == 0:  # creation command
                        line_command[2]['name'] = self.partner_full_address
        
        return values_list

class ContractLineExtended(models.Model):
    _inherit = 'contract.line'

    def _prepare_invoice_line(self):
        """Override to replace name with address"""
        vals = super()._prepare_invoice_line()
        if vals and self.contract_id and self.contract_id.partner_full_address:
            vals['name'] = self.contract_id.partner_full_address
        return vals

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _get_formatted_address(self, partner):
        """Helper method to format partner address consistently"""
        if not partner:
            return False
            
        address_parts = []
        if partner.street:
            address_parts.append(partner.street)
        if partner.street2:
            address_parts.append(partner.street2)
        if partner.city:
            address_parts.append(partner.city)
        if partner.state_id:
            address_parts.append(partner.state_id.name)
        if partner.country_id:
            address_parts.append(partner.country_id.name)
        
        return ', '.join(filter(None, address_parts)) if address_parts else False

    @api.model_create_multi
    def create(self, vals_list):
        """Ensure manually created invoice lines also use only the address"""
        for vals in vals_list:
            move_id = vals.get('move_id')
            if move_id and vals.get('contract_line_id'):
                contract_line = self.env['contract.line'].browse(vals['contract_line_id'])
                if contract_line.contract_id and contract_line.contract_id.partner_id:
                    formatted_address = self._get_formatted_address(contract_line.contract_id.partner_id)
                    if formatted_address:
                        vals['name'] = formatted_address
        
        return super().create(vals_list)
