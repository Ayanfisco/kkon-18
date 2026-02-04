# -*- coding: utf-8 -*-
{
    'name': 'HR Payroll Date Type Fix',
    'version': '18.0',
    'category': 'Human Resources/Payroll',
    'summary': 'Fixes date type issues in HR Payroll',
    'description': """
HR Payroll Date Type Fix
========================
This module fixes the issue where datetime objects are passed to generate_work_entries method
which expects date objects, causing an AssertionError.
    """,
    'author': 'MOB - Ifeanyi Nneji',
    'website': 'http://www.mattobell.com/',
    'depends': ['hr_payroll', 'hr_work_entry_contract'],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    "images": ["static/description/icon.png"],
    'license': 'LGPL-3',
}