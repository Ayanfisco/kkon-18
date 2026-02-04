{
    'name': 'Account Type Custom',
    'version': '0.82',
    'summary': 'Create custom account types',
    'description': """
        This module helps an organization to create custom account types from settings configuration.
        """,
    'category': 'Accounting',
    'author': 'MOB - Nneji Ifeanyi',
    'website': 'https://www.mattobell.net',
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/custom_account_type_view.xml',
        'views/account_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ng_mob_account_type_extend/static/src/js/account_type_selection.js',
            'ng_mob_account_type_extend/static/src/xml/account_type_selection.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
    "images": ["static/description/icon.png"] 
}