# -*- coding: utf-8 -*-
{
    "name": "API Integration",
    "summary": """
        API integration with an external system""",
    "description": """
API integration with an external system
=================================================
Module is expected to have:
1. Customer creation endpoint
2. Invoice creation endpoint
3. Payment registration endpoint
4. Endpoint to trigger new payment.
    """,
    "author": "Matt O'Bell Ltd",
    "website": "https://www.mattobell.net",
    "category": "Uncategorized",
    "version": "0.1",
    "license": "LGPL-3",
    "depends": [
        "sale",
        "api_auth",
    ],
    "data": [
        # "data/cron.xml",
        "views/account_journal_views.xml",
        "views/product_views.xml",
        "views/account_move_views.xml",
        "views/res_config_settings_views.xml",
        "views/sale_order_views.xml",
        "views/res_company_views.xml",
    ],
}
