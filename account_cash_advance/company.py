

from odoo import models, fields

class company_settings(models.Model):
    _inherit = 'res.company'
    _description = 'Company'

    cash_employee_journal = fields.Many2one('account.journal', string='Cash Advance Journal')
    ex_employee_journal = fields.Many2one('account.journal', string='Expense Advance Journal')
    ret_employee_journal = fields.Many2one('account.journal', string='Expense Retirements Journal')

    cash_employee_account = fields.Many2one('account.account', string='Employee Cash Advance Account')#, domain="[('type','in',('receivable','payable'))]"
    ex_employee_account = fields.Many2one('account.account', string='Employee Expense Advance Account')
    ret_employee_account = fields.Many2one('account.account', string='Employee Expense Retirements Account')
