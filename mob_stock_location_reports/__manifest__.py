{
    'name': 'Stock Location Reports',
    'version': '1.6',
    'category': 'Inventory/Inventory',
    'summary': 'Dynamic Stock Location Reports',
    'description': """
        This module adds a Stock Location Reports menu under Reports
        that allows dynamic switching between different stock locations
        to view current stock information.
    """,
    'author': 'MOB - Ifeanyi Nneji',
    'website': 'https://mattobellonline.com',
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_location_report_views.xml',
        'views/menu_views.xml',
        'views/stock_quant_tree_inherit.xml',
        'views/stock_location_report_history_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    "images": ["static/description/icon.png"] 
}