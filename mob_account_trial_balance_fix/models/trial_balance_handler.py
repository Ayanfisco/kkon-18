from odoo import models, api, _
from odoo.tools import float_compare

def _patch_trial_balance_handler(env):
    """Apply the patch only after all modules are loaded"""
    if env.registry.get('account.trial.balance.report.handler'):
        # Now it's safe to apply your customizations
        ZeroInitialBalanceTrialBalanceHandler._patch_method(
            '_dynamic_lines_generator', 
            ZeroInitialBalanceTrialBalanceHandler._dynamic_lines_generator
        )

class ZeroInitialBalanceTrialBalanceHandler(models.AbstractModel):
    _name = 'zero.initial.balance.trial.balance.handler'
    _inherit = 'account.report.custom.handler'

    def _dynamic_lines_generator(self, report, options, all_column_groups_expression_totals=None, warnings=None):
        warnings = warnings or []
        lines = []

        # Your existing logic
        ...

        return lines


# class ZeroInitialBalanceTrialBalanceHandler(models.AbstractModel):
#     _inherit = 'account.trial.balance.report.handler'
#
#     def _dynamic_lines_generator(self, report, options, all_column_groups_expression_totals):
#         # Get the lines from the parent method
#         lines_with_index = super()._dynamic_lines_generator(report, options, all_column_groups_expression_totals)
#
#         # Extract just the lines
#         lines = [line[1] for line in lines_with_index]
#
#         # The last line is typically the total line
#         total_line = lines[-1] if lines else None
#         regular_lines = lines[:-1] if lines else []
#
#         # Find the indices for initial balance columns (debit and credit)
#         init_balance_debit_index = next((index for index, column in enumerate(options['columns'])
#                                          if column.get('expression_label') == 'debit' and
#                                          'Initial Balance' in options['column_headers'][0][0]['name']), None)
#
#         init_balance_credit_index = next((index for index, column in enumerate(options['columns'])
#                                           if column.get('expression_label') == 'credit' and
#                                           'Initial Balance' in options['column_headers'][0][0]['name']), None)
#
#         # Track total adjustment amounts to correct the total line later
#         total_debit_adjustment = 0
#         total_credit_adjustment = 0
#
#         # Process each line except the total
#         for line in regular_lines:
#             # Get the account associated with this line
#             model, model_id = report._get_model_info_from_id(line['id'])
#
#             if model == 'account.account':
#                 account = self.env['account.account'].browse(model_id)
#
#                 # Check if this account should have zero initial balance
#                 if self._should_zero_initial_balance(account):
#                     # Store original values for total adjustment
#                     if init_balance_debit_index is not None:
#                         orig_debit = line['columns'][init_balance_debit_index]['no_format']
#                         total_debit_adjustment += orig_debit
#                         # Set to zero
#                         line['columns'][init_balance_debit_index]['name'] = self.env['account.report'].format_value(0)
#                         line['columns'][init_balance_debit_index]['no_format'] = 0
#
#                     if init_balance_credit_index is not None:
#                         orig_credit = line['columns'][init_balance_credit_index]['no_format']
#                         total_credit_adjustment += orig_credit
#                         # Set to zero
#                         line['columns'][init_balance_credit_index]['name'] = self.env['account.report'].format_value(0)
#                         line['columns'][init_balance_credit_index]['no_format'] = 0
#
#         # Adjust the total line
#         if total_line and init_balance_debit_index is not None and init_balance_credit_index is not None:
#             # Subtract the adjustments from the total line
#             new_debit_total = total_line['columns'][init_balance_debit_index]['no_format'] - total_debit_adjustment
#             new_credit_total = total_line['columns'][init_balance_credit_index]['no_format'] - total_credit_adjustment
#
#             total_line['columns'][init_balance_debit_index]['name'] = self.env['account.report'].format_value(new_debit_total)
#             total_line['columns'][init_balance_debit_index]['no_format'] = new_debit_total
#
#             total_line['columns'][init_balance_credit_index]['name'] = self.env['account.report'].format_value(new_credit_total)
#             total_line['columns'][init_balance_credit_index]['no_format'] = new_credit_total
#
#         # Recreate the lines with index format
#         return [(index, line) for index, line in enumerate(lines)]
#
    def _should_zero_initial_balance(self, account):
        """
        Determine if an account should have its initial balance set to zero.
        Returns True for expense, income, tax, and asset accounts using pattern matching.
        """
        account_type = account.account_type
        
        # Check if the account type starts with 'income' or 'expense'
        if (account_type.startswith('income') or 
            account_type.startswith('expense') or account_type.startswith('asset')):
            return True
        
        return False
    
def _module_hook(env):
    _patch_trial_balance_handler(env)