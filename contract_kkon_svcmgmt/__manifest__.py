# -*- coding: utf-8 -*-
{
    'name': "KKONTech Service Management",
    'author': "Mikromtech Limited",
    'website': "https://www.mikromtech.com",
    'version': '1.0',
    'category': 'Services',
    'description': " ",  # Non-empty string to avoid loading the README file.
    'depends': ['base', 'sale', 'contract', 'contract_sale', 'base_automation'],

    'data': [
        # 'security/ir.model.access.csv',
        'security/ir.model.access.xml',
        'data/kkon_svcmgmt_sequence.xml',
        'data/kkon_svcmgmt_api_settings.xml',
        'data/kkon_svcmgmt_scheduled_actions.xml',
        'data/kkon_svcmgmt_automated_actions.xml',
        'data/kkon_svcmgmt_email_templates.xml',
        'views/views.xml',
    ],
    
    'demo': [
        'demo/demo.xml',
    ],
    'license': 'LGPL-3',
}
