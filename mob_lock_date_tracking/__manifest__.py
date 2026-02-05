{
    'name': 'Period Lock Date Tracking',
    'version': '1.0.2',
    'category': 'Accounting',
    'summary': 'Enable tracking for period lock date fields',
    'description': """
        This module enables tracking for period lock date fields using a regular model
        instead of TransientModel to ensure proper audit logging.
    """,
    'author': 'MOB - Ifeanyi Nneji',
    'website': 'https://mattobellonline.com',
    'depends': ['smile_audit', 'account_accountant'],
    'data': [
        'security/ir.model.access.csv',
        'data/audit_rule_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
