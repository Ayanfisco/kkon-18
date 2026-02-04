# -*- coding: utf-8 -*-

{
    'name': 'Trial Balance Fix for Income/Expense Accounts',
    'sequence': 100,
    'version': '0.0.6',
    'summary': 'Removes initial balance for income and expense accounts in trial balance report',
    'description': """
        This module modifies the trial balance computation to ensure
        income and expense accounts don't show initial balance values,
        as they should begin at zero for each fiscal year.
    """,
    'category': 'Accounting/Accounting',
    'author': 'MOB - Nneji Ifeanyi',
    'website': 'https://www.mattobell.net',
    'depends': ['account', 'account_reports', 'account_financial_report'],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    "images": ["static/description/icon.png"],
}
