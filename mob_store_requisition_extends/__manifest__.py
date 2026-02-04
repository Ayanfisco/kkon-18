{
    'name': 'Store Requisition Extension',
    'version': '1.6',
    'category': 'Inventory',
    'summary': 'Extensions for Store Requisition Module',
    'description': """
        Modifications to Store Requisition Module:
        - Links user field to employee field with auto-population
        - Changes HOD approval to manager approval in workflow
    """,
    'author': 'MOB - Ifeanyi Nneji',
    'website': 'https://www.mattobell.net/',
    'depends': ['base', 'ng_store_requisition', 'hr'],
    'data': [
        'views/store_request_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    "images": ["static/description/icon.png"] 
}