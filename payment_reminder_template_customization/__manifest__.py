{
    'name': 'Payment Reminder and Expiration Template Customization',
    'version': '18.0',
    'category': 'Accounting',
    'summary': 'Payment Reminder and expiration Template Customization',
    'description': """
    This module customizes the payment reminder template to include additional details
    """,
    'author': 'Mattobell - Ayanfe Ojo',
    'website': 'https://www.mattobell.net/',
    'depends': [
    'account_accountant',
    ],
    'data': [
        'data/payment_reminder_email_template_extended.xml',
        # 'data/cron_job.xml',
        # 'data/account_move_email_temp.xml',
        'data/expiration_reminder_email_template.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}