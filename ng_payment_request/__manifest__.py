{
    "name": "Payment Request",
    "version": "18.0",
    "summary": "Manage and track payment requests, approvals, and notifications",
    "description": """
        This module provides a complete payment request management system:
        * Create and submit payment requests
        * Multi-level approval workflow
        * Email notifications for request status
        * Detailed payment request reports
        * Integration with accounting and HR modules
        * Company-specific payment request configurations
    """,
    "category": "Accounting/Payment",
    "author": "Mattobell",
    "website": "http://www.mattobell.com/",
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/request_sequence.xml",
        "views/payment_requisition_view.xml",
        "views/company_view.xml",
        "report/payment_request_report.xml",
        "report/request_report_view.xml",
    ],
    "depends": ["account", "hr", 'mail'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    "images": ["static/description/icon.png"]
}
