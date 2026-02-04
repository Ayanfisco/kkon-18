# -*- coding: utf-8 -*-
{
    'name': 'Contract Invoice Address Extension',
    'version': '0.0.3',
    'category': 'Contract Management',
    'summary': 'Add customer address to contract invoice lines',
    'description': """
        This module extends the contract module to include the customer's address
        in the invoice line descriptions when generating invoices from contracts.
    """,
    'author': 'MOB - Ifeanyi Nneji',
    'website': 'https://www.mattobell.net/',
    'depends': [
        'contract',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'AGPL-3',
    "images": ["static/description/icon.png"] 
}