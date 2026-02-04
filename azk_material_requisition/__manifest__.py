# -*- coding: utf-8 -*-
{
    'name': "Material Requisition",
    'summary': "Manages the handling of material requisition workflows, including requests initiated by PM handled by inventory, purchase till delivery of material",
    'description': "Manages the handling of material requisition workflows, including requests initiated by PM, handled by inventory, purchase till delivery of material",
    'license': 'AGPL-3',
    'author': "Azkatech",
    'website': "https://www.azka.tech",
    "support": "support+odoo@azka.tech",
    "price": 50,
    "currency": "USD",
    'category': 'Others',
    'version': '18.0',

    'depends': ['base','project', 'stock', 'analytic', 'purchase', 'purchase_requisition', 'hr_timesheet'],
    'data': [
        'data/data.xml',
       'data/attachment_data.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        
        'views/purchase_request.xml',
        'views/material_requisition_views.xml',
        'views/material_requisition_line_views.xml',
        'views/project.xml',
        'views/res_company.xml',
        'views/menuitems.xml',
        
        'wizards/create_transfer_wizard.xml',
        'wizards/create_purchase_order_wizard.xml',
        'wizards/import_material_csv.xml'
    ],
    'application': True,
    'images': ['static/description/banner.png'],
}
