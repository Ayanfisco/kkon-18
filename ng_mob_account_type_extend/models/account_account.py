from odoo import api, fields, models

class AccAccExt(models.Model):
    _inherit = "account.account"

    custom_account_type_id = fields.Many2one('custom.account.type', string='Custom Account Type')
    
    account_type = fields.Selection(
        selection='_get_account_types',
        string="Type",
        tracking=True,
        required=True,
        compute="_compute_account_type",
        store=True,
        readonly=False,
        precompute=True,
        help="Account Type is used for information purpose, to generate country-specific legal reports, and set the rules to close a fiscal year and generate opening entries.",
    )

    @api.model
    def _get_account_types(self):
        original_types = [
            # NEW ACCOUNT TYPES
            # Assets
            ("asset_other", "Other Assets"),
            ("asset_properties", "Properties Plant & Equipment"),
            ("asset_cash_equivalents", "Cash & Cash Equivalents"),
            # Income
            ("income_revenue", "Revenue"),
            ("income_radiology_imaging", "Income RADIOLOGY & IMAGING SERVICES"),
            ("income_ancillary_services", "Income ANCILLIARY SERVICES"),
            ("income_laboratory_investigations", "Income LABORATORY INVESTIGATIONS"),
            ("income_ambulatory_services", "Income AMBULATORY SERVICES"),
            ("income_consultation", "Income CONSULTATION"),
            ("income_dialysis", "Income from Dialysis"),
            ("income_surgery", "Income from Surgery"),
            ("income_dental", "Dental Income"),
            ("income_miscellaneous", "Miscellaneous Income"),
            # Expenses
            ("expense_consultation", "COS CONSULTATION"),
            ("expense_radiology_imaging", "COS RADIOLOGY & IMAGING SERVICES"),
            ("expense_ancillary_services", "COS ANCILLIARY SERVICES"),
            ("expense_ambulatory_services", "COS AMBULATORY SERVICES"),
            ("expense_dialysis", "COS DIALYSIS"),
            ("expense_surgery", "COS SURGERY"),
            ("expense_dental", "COS DENTAL"),
            ("expense_marketing_distribution", "Marketing / Distribution Expenses"),
            ("expense_communications", "Communications Expenses"),
            ("expense_professional_service", "Professional Service"),
            ("expense_prepaid", "Prepaid Expenses"),
            ("expense_depreciation", "Depreciation"),
            ("expense_cost_of_sales", "Cost of Sales"),
            ("expense_miscellaneous", "Miscellaneous Expenses"),

            # OLD ACCOUNT TYPES
            ("asset_receivable", "Receivable"),
            ("asset_cash", "Bank and Cash"),
            ("asset_current", "Current Assets"),
            ("asset_non_current", "Non-current Assets"),
            ("asset_prepayments", "Prepayments"),
            ("asset_fixed", "Fixed Assets"),
            ("asset_accumulated_depreciation", "Accumulated Depreciation"),
            ("asset_inventory", "Inventory"),
            ("asset_other_current", "Other Current Assets"),
            ("asset_intangible", "Intangible Assets"),
            ("asset_lease_receivables", "Lease Receivables"),
            ("asset_consumables", "Consumables"),
            ("asset_motor_vehicles", "Motor Vehicles"),
            ("asset_raw_materials", "Raw Materials"),
            ("asset_third_party_stocks", "Third Party Stock"),
            ("asset_rigs_n_related_equipments", "Rigs and Related Equipment"),
            ("asset_construction_inprogress", "Construction In Progress"),
            ("asset_non_current_recv", "Non Current Receivables - Other"),
            ("asset_software_cost", "Software Costs"),
            ("asset_bonus_dep_res", "Bonus Depreciation Reserve"),
            ("asset_deferred_inv_tax", "Deferred Income Tax Assets"),
            ("asset_quoted_invest", "Quoted Investments"),
            ("asset_unquoted_invest", "Unquoted Investments"),
            ("asset_noncurrent_prepayments", "Noncurrent Prepayments"),
            ("asset_inv_prov_acc", "Inventory Provision Accounts"),
            ("asset_trade_n_other_rec", "Trade and Other Receivables"),
            ("asset_dividend_rec", "Dividend Receivables"),
            ("asset_statutory_rec", "Statutory Receivables"),
            ("asset_staff_rec", "Staff Receivables"),
            ("asset_other_rec", "Other Receivables"),
            ("asset_deposits", "Deposits"),
            ("asset_current_lease_rec", "Current Lease Receivables"),
            ("asset_prov_for_doubt_bank_bal", "Provision for Doubtful Bank Balances"),
            ("asset_land_n_building", "Land and Building"),
            ("asset_it_equip", "Information Technology"),
            ("asset_furn_fix_equip", "Furniture, Fixtures, and Equipment"),
            ("asset_classified_as_held_for_sale", "Assets Classified as Held for Sale"),
            ("asset_goodwill", "Goodwill"),
            ("asset_capitalized_interest", "Capitalized Interest"),
            ("asset_investments", "Investments"),
            ("asset_intercompany_receivables", "Intercompany Receivables"),
            ("liability_payable", "Payable"),
            ("liability_credit_card", "Credit Card"),
            ("liability_current", "Current Liabilities"),
            ("liability_non_current", "Non-current Liabilities"),
            ("liability_accured_exp", "Accrued Expenses"),
            ("liability_bank_overdraft", "Bank Overdraft"),
            (
                "liability_cur_portion_long_term_debt",
                "Current Portion of Long-Term Debt",
            ),
            ("liability_emp_related", "Employee Related Liabilities"),
            ("liability_intercom_payable", "Intercompany Payables"),
            ("liability_member_deferred_revenue", "Membership Deferred Revenue"),
            ("liability_other_current", "Other Current Liabilities"),
            ("liability_rent_deferred_revenue", "Rent Deferred Revenue"),
            ("liability_taxes_payable", "Taxes Payable"),
            ("liability_trade_payable", "Trade Payable"),
            ("liability_statutory_payable", "Statutory Payables"),
            ("liability_accurals_n_provisions", "Accruals and Provisions"),
            ("liability_other_current_payables", "Other Current Payables"),
            ("liability_vouchers_payables", "Vouchers Payable"),
            ("liability_inc_tax_payables", "Income Taxes Payable"),
            ("liability_deferred_tax_current", "Deferred Tax Liability - Current"),
            ("liability_overdrafts", "Overdrafts"),
            ("liability_finance_lease_obl", "Finance Lease Obligations"),
            ("liability_convertible_loans", "Convertible Loans"),
            ("liability_med_term_borrowing", "Medium Term Borrowing"),
            ("liability_non_current_borrowing", "Non-Current Borrowings"),
            (
                "liability_non_current_finance_lease_obl",
                "Non-Current Finance Lease Obligations",
            ),
            ("liability_deferred_inc_tax", "Deferred Income Tax Liabilities"),
            ("liability_retire_benefit_obl", "Retirement Benefit Obligations"),
            ("liability_govt_grant", "Government Grant"),
            ("equity", "Equity"),
            ("equity_unaffected", "Current Year Earnings"),
            ("equity_retained_earnings", "Retained Earnings"),
            ("equity_share_capital", "Share Capital"),
            ("equity_share_premium", "Share Premium"),
            ("equity_revaluation_reserve", "Revaluation Reserve"),
            ("equity_other_reserve", "Other Reserves"),
            ("equity_non_controlling_interest", "Non-Controlling Interests"),
            ("income", "Income"),
            ("income_other", "Other Income"),
            ("income_interest_inc", "Interest Income"),
            ("income_other_opt_inc", "Other Operating Income"),
            ("income_unallocated_revn_acc", "Unallocated Revenue Account"),
            ("income_dividend", "Dividend"),
            ("income_finance_inc_interest_rec", "Finance Income/Interest Received"),
            ("income_net_finance_cost_inc", "  Net Finance (Cost)/Income"),
            ("expense", "Expenses"),
            ("expense_interest", "Interest Expense"),
            ("expense_operating", "Operating Expenses"),
            ("expense_inbound_freight", "Inbound Freight"),
            ("expense_outbound_freight", "Outbound Freight"),
            ("expense_pre_finance_related", "Prepaid Finance Related Expenses"),
            ("expense_payroll", "Payroll Expenses"),
            ("expense_other_emp_costs", "Other Employee Costs"),
            ("expense_training", "Training"),
            ("expense_entertainment", "Entertainment Expenses"),
            ("expense_traveling", "Traveling Expenses"),
            ("expense_stationery_n_consumables", "Stationery and Consumables"),
            ("expense_utility", "Utilities Expenses"),
            ("expense_interest_rate_swaps", "Interest Rate Swaps"),
            ("expense_exchange_rate_swaps", "Exchange Rate Swaps"),
            ("expense_stock_options", "Stock Options"),
            ("expense_statutory_payments", "Statutory Payments"),
            ("expense_business_dev", "Business Development Expenses"),
            ("expense_board", "Board Expenses"),
            ("expense_agm", "AGM Expenses"),
            ("expense_subscription", "Subscription"),
            ("expense_donations", "Donations"),
            ("expense_other_admin", "Other Administrative Expenses"),
            ("expense_business_com", "Business Communication Expenses"),
            ("expense_repairs_n_maintenance", "Repairs and Maintenance Expenses"),
            ("expense_prods_consumption", "Products Consumption"),
            ("expense_minor_contract", "Minor Contracts"),
            ("expense_exchange_loss_acc", "Exchange Loss Account"),
            ("expense_provisions_n_write_off", "Provisions and Write Offs"),
            ("expense_amortization_n_impairment", "Amortization and Impairment"),
            ("expense_finance_cost_interest_paid", "Finance Cost/Interest Paid"),
            ("expense_inc_tax", "Income Tax Expenses"),
            ("expense_rental_cost", "Rental Costs"),
            ("expense_oes_payable_conversion", "OES Payable Conversion"),
            ("off_balance", "Off-Balance Sheet"),
            ("off_balance_interest_rate_swap", "Interest Rate Swaps"),
            ("off_balance_exchange_rate_swap", "Exchange Rate Swaps"),
            ("off_balance_stock_options", "Stock Options"),
            ("expense_direct_cost", "Cost of Revenue"),
        ]
        
        custom_types = self.env['custom.account.type'].search([])
        for custom_type in custom_types:
            original_types.append((custom_type.code, custom_type.name))
        
        return original_types

    @api.depends('custom_account_type_id')
    def _compute_account_type(self):
        for record in self:
            if record.custom_account_type_id:
                record.account_type = record.custom_account_type_id.code
            elif not record.account_type:
                pass

    def _inverse_account_type(self):
        for record in self:
            custom_type = self.env['custom.account.type'].search([('code', '=', record.account_type)], limit=1)
            if custom_type:
                record.custom_account_type_id = custom_type.id
            else:
                record.custom_account_type_id = False

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(AccAccExt, self).fields_get(allfields, attributes)
        if 'account_type' in res:
            res['account_type']['selection'] = self._get_account_types()
        return res