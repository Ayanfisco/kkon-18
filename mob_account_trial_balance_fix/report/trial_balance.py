import logging

from odoo import api, models

_logger = logging.getLogger(__name__)

class TrialBalanceReport(models.AbstractModel):
    _name = "report.account_financial_report.trial_balance"
    _inherit = "report.account_financial_report.trial_balance"


    @api.model
    def _get_report_values(self, docids, data):
        res = super()._get_report_values(docids, data)

        _logger.info("Entering custom _get_report_values in report model.")
        company_id = data["company_id"]
        partner_ids = data["partner_ids"]
        journal_ids = data["journal_ids"]
        account_ids = data["account_ids"]
        date_to = data["date_to"]
        date_from = data["date_from"]
        hide_account_at_0 = data["hide_account_at_0"]
        foreign_currency = data["foreign_currency"]
        only_posted_moves = data["only_posted_moves"]
        show_partner_details = data["show_partner_details"]
        unaffected_earnings_account = data["unaffected_earnings_account"]
        fy_start_date = data["fy_start_date"]

        zero_initial_balance_account_ids = data.get("zero_initial_balance_account_ids", [])
        _logger.info(f"Received zero_initial_balance_account_ids in report: {zero_initial_balance_account_ids}")

        total_amount, accounts_data, partners_data = self._get_data(
            account_ids,
            journal_ids,
            partner_ids,
            company_id,
            date_to,
            date_from,
            foreign_currency,
            only_posted_moves,
            show_partner_details,
            hide_account_at_0,
            unaffected_earnings_account,
            fy_start_date,
            zero_initial_balance_account_ids=zero_initial_balance_account_ids # Pass the list
        )

        res['total_amount'] = total_amount
        res['accounts_data'] = accounts_data
        res['partners_data'] = partners_data

        trial_balance = []
        if not show_partner_details:
            # Populate accounts_data with calculated amounts (as in original)
            for account_id in accounts_data.keys():
                 if account_id in total_amount: # Check if account has data
                    accounts_data[account_id].update(
                        {
                            "initial_balance": total_amount[account_id]["initial_balance"],
                            "credit": total_amount[account_id]["credit"],
                            "debit": total_amount[account_id]["debit"],
                            "balance": total_amount[account_id]["balance"],
                            "ending_balance": total_amount[account_id]["ending_balance"],
                            "type": "account_type", # Keep this type identifier
                        }
                    )
                    if foreign_currency:
                        accounts_data[account_id].update(
                            {
                                "ending_currency_balance": total_amount[account_id].get("ending_currency_balance", 0.0),
                                "initial_currency_balance": total_amount[account_id].get("initial_currency_balance", 0.0),
                            }
                        )

            if res.get("show_hierarchy"): # Use the flag already in 'res'
                groups_data = self._get_groups_data(
                    accounts_data, total_amount, foreign_currency
                )
                trial_balance = list(groups_data.values())
                trial_balance += [acc for acc in accounts_data.values() if 'initial_balance' in acc] # Only add accounts with calculated data
                trial_balance = sorted(trial_balance, key=lambda k: k.get("complete_code", k.get("code", ""))) # Safe sort key
                for trial in trial_balance:
                    counter = trial.get("complete_code", "").count("/")
                    trial["level"] = counter
            else:
                trial_balance = [acc for acc in accounts_data.values() if 'initial_balance' in acc]
                trial_balance = sorted(trial_balance, key=lambda k: k.get("code", "")) # Safe sort key
        else:
             if foreign_currency:
                for account_id in accounts_data.keys():
                    if account_id in total_amount:
                        total_amount[account_id]["currency_id"] = accounts_data[account_id].get("currency_id")
                        total_amount[account_id]["currency_name"] = accounts_data[account_id].get("currency_name")

        res['trial_balance'] = trial_balance

        _logger.info("Exiting custom _get_report_values in report model.")
        return res


    @api.model
    def _get_data(
        self,
        account_ids,
        journal_ids,
        partner_ids,
        company_id,
        date_to,
        date_from,
        foreign_currency,
        only_posted_moves,
        show_partner_details,
        hide_account_at_0,
        unaffected_earnings_account,
        fy_start_date,
        zero_initial_balance_account_ids=None
    ):
        _logger.info("Entering custom _get_data in report model.")
        if zero_initial_balance_account_ids is None:
            zero_initial_balance_account_ids = []

        total_amount, accounts_data, partners_data = super()._get_data(
            account_ids=account_ids,
            journal_ids=journal_ids,
            partner_ids=partner_ids,
            company_id=company_id,
            date_to=date_to,
            date_from=date_from,
            foreign_currency=foreign_currency,
            only_posted_moves=only_posted_moves,
            show_partner_details=show_partner_details,
            hide_account_at_0=hide_account_at_0,
            unaffected_earnings_account=unaffected_earnings_account,
            fy_start_date=fy_start_date,
        )

        _logger.info(f"Original total_amount keys: {list(total_amount.keys())}")
        _logger.info(f"Accounts to zero initial balance for: {zero_initial_balance_account_ids}")

        company = self.env["res.company"].browse(company_id)
        rounding = company.currency_id.rounding

        accounts_zeroed_count = 0
        for acc_id in zero_initial_balance_account_ids:
            if acc_id in total_amount:

                total_amount[acc_id]["initial_balance"] = 0.0

                period_balance = total_amount[acc_id].get("balance", 0.0)
                total_amount[acc_id]["ending_balance"] = 0.0 + period_balance
                accounts_zeroed_count += 1

                if foreign_currency and "initial_currency_balance" in total_amount[acc_id]:
                     total_amount[acc_id]["initial_currency_balance"] = 0.0
  
        _logger.info(f"Applied zero initial balance to {accounts_zeroed_count} accounts.")
        if zero_initial_balance_account_ids and accounts_zeroed_count > 0:
             sample_acc_id = next((acc_id for acc_id in zero_initial_balance_account_ids if acc_id in total_amount), None)
             if sample_acc_id:
                  _logger.info(f"Sample modified account {sample_acc_id} data: {total_amount[sample_acc_id]}")

        if hide_account_at_0:
             _logger.info("Re-applying hide_account_at_0 check after zeroing initial balances.")
             self._remove_accounts_at_cero(total_amount, show_partner_details, company)
             _logger.info(f"total_amount keys after re-applying hide_account_at_0: {list(total_amount.keys())}")

        _logger.info("Exiting custom _get_data in report model.")
        return total_amount, accounts_data, partners_data