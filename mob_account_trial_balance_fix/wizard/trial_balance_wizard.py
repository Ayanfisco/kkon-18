# models/trial_balance_wizard.py
from odoo import api, models

class TrialBalanceReportWizard(models.TransientModel):
    _inherit = "trial.balance.report.wizard"

    def _prepare_report_trial_balance(self):
        """
        Override to add custom data for zeroing initial balances of expense and income accounts.
        """
        self.ensure_one()

        data = super(TrialBalanceReportWizard, self)._prepare_report_trial_balance()

        target_account_types = ('expense', 'income')

        if data.get("account_ids"):
            accounts = self.env["account.account"].browse(data["account_ids"])
            zero_initial_balance_account_ids = accounts.filtered(
                lambda a: a.account_type.startswith(target_account_types)
            ).ids
        else:
            domain = [
                ('company_id', '=', self.company_id.id),
                '|',
                ('account_type', '=like', 'expense%'),
                ('account_type', '=like', 'income%'),
            ]
            zero_initial_balance_account_ids = self.env["account.account"].search(domain).ids

        data["zero_initial_balance_account_ids"] = zero_initial_balance_account_ids

        return data