from odoo import api, SUPERUSER_ID


def get_eservice_default_company(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    default_company = (
        env["res.config.settings"]
        .get_values()
        .get("eservice_company_id", 0)
    )
    return default_company or int(env.company)


def get_eservice_deferred_revenue_account_id(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    config_settings = (
        env["res.config.settings"]
        .get_values()
        .get("deferred_revenue_account_id", 0)
    )
    return config_settings
