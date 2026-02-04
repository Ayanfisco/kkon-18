
{
    'name' : 'Employee Cash Advances',
    'version' : '18.0',
    'depends' : ["base", "hr", 'hr_expense', 'hr_contract', 'hr_payroll', 'account_accountant'],
    'author' : 'Mattobell',
    'website' : 'http://www.mattobell.com',
    'description': '''
Management of Various Cash Advances to Employees
============================

Features
--------
* Salary Advances and Payment
* Pretty Cash Advances for Expense and Retirements
    ''',
    'category' : 'Accounting & Finance',
    'sequence': 70,
    'data' : [
        'security/account_salary_security.xml',
        'security/ir.model.access.csv',
        'report/cash_advance_report_reg.xml',
        'report/cash_advance_report_view.xml',
        'company_view.xml',
        'ng_account_cash_view.xml',
        'ng_account_expense_view.xml',
        'hr_expense_view.xml',
        'ng_refund_advance_view.xml',
#        'report.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}