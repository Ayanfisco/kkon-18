from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import re
import logging

_logger = logging.getLogger(__name__)


class CustomAccountType(models.Model):
    _name = 'custom.account.type'
    _description = 'Custom Account Type'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    internal_group = fields.Selection([
        ('equity', 'Equity'),
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('off_balance', 'Off Balance'),
    ], string='Internal Group', required=True)

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'The name must be unique!'),
        ('unique_code', 'UNIQUE(code)', 'The code must be unique!')
    ]

    def unlink(self):
        # Consider if this is truly necessary. Odoo allows deleting many things.
        # Maybe check if it's linked to an account.account first?
        linked_accounts = self.env['account.account'].search_count([('custom_account_type_id', 'in', self.ids)])
        if linked_accounts > 0:
            raise UserError(_("You cannot delete an account type that is currently assigned to one or more accounts."))
        return super(CustomAccountType, self).unlink()

    @api.constrains('name', 'code')
    def _check_duplicates(self):
        for record in self:
            # Check for duplicate names (case-insensitive)
            duplicate_name = self.search([
                ('id', '!=', record.id),
                ('name', '=ilike', record.name)
            ])
            if duplicate_name:
                raise ValidationError(_("An account type with the name '%s' already exists.") % record.name)

            # Check for duplicate codes (case-insensitive)
            duplicate_code = self.search([
                ('id', '!=', record.id),
                ('code', '=ilike', record.code)
            ])
            if duplicate_code:
                raise ValidationError(_("An account type with the code '%s' already exists.") % record.code)


    @api.constrains('code', 'internal_group')
    def _check_code_format(self):
        for record in self:
            if record.code and record.internal_group:
                # Check if code is lowercase
                if record.code != record.code.lower():
                    raise ValidationError(_("The code must be in lowercase."))

                # Check if code starts with internal_group
                if not record.code.startswith(record.internal_group + '_'):
                    raise ValidationError(_("The code must start with the internal group name followed by an underscore."))

                                # Check if code only contains lowercase letters, numbers, and underscores
                if not re.match(r'^[a-z_]+$', record.code):
                    raise ValidationError(_("The code must only contain lowercase letters and underscores."))
                
    @api.constrains('code', 'internal_group')
    def _check_code_prefix(self):
        for record in self:
            if record.code and record.internal_group:
                expected_prefix = record.internal_group + '_'
                if not record.code.startswith(expected_prefix):
                    raise ValidationError(_(
                        "Invalid code prefix for %(name)s. "
                        "The code should start with '%(prefix)s' based on the selected internal group. "
                        "For example, use '%(prefix)s%(example)s' instead of '%(code)s'."
                    ) % {
                        'name': record.name,
                        'prefix': expected_prefix,
                        'example': record.code.split('_')[-1] if '_' in record.code else record.code,
                        'code': record.code
                    })
                
    @api.onchange('internal_group')
    def _onchange_internal_group(self):
        if self.internal_group and self.code:
            code_parts = self.code.split('_')
            if len(code_parts) > 1:
                self.code = f"{self.internal_group}_{'_'.join(code_parts[1:])}"
            else:
                self.code = f"{self.internal_group}_{self.code}"