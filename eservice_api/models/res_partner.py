import logging
from odoo import models

from ..constants import PARTNER_FIELDS, get_cleaned_create_values

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    # def _find_or_create_partner(self, partner_id=""):
    #     """ Fetch or Create Partner Record

    #     :param str partner_id: FOBID of customer
    #     :return: A matching customer record
    #     :rtype: recordset of `res.partner`
    #     """
    #     customer = Partner = self.env['res.partner'].sudo()
    #     _logger.info(
    #         f"---------- Partner vals {partner_vals} -------------------")

    #     customer = Partner.search(
    #         [('x_studio_partner_id', '=', partner_id)], limit=1)
    #     if not customer:  # customer doesn't exist
    #         partner_vals = get_cleaned_create_values(PARTNER_FIELDS, partner_vals)
    #         _logger.info(
    #             f"---------- Partner vals {partner_vals} -------------------")
    #         partner_vals.setdefault('customer_rank', 1)
    #         partner_vals.setdefault('country_id', self.env.ref(
    #             "base.ng") and int(self.env.ref("base.ng")) or False)
    #         customer = Partner.create(partner_vals)
    #     return customer
