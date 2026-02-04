{
    'name': 'AZK Material Requisition Extends',
    'version': '1.6',
    'summary': 'Extends AZK Material Requisition with custom approval workflow and fields',
    'description': 'Adds user, employee, and manager fields, and extends the approval workflow for material requisitions.',
    'author': 'MOB - Ifeanyi Nneji',
    'website': 'http://mattobellonline.com',
    'category': 'Inventory',
    'depends': ['azk_material_requisition'],
    'data': [
        'security/security.xml',
        'data/mail_template_data.xml',
        'views/material_requisition_extends_views.xml',
        'views/purchase_request_extends_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    "images": ["static/description/icon.png"] 
}