# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import logging
from odoo.addons.api_auth.util.helper import validate_token

_logger = logging.getLogger(__name__)

PRODUCT_READ_FIELDS = [
    "name",
    "lst_price",
    "eservice_code",
]


class ProductHome(http.Controller):

    @validate_token
    @http.route(
        "/fb_api/products",
        auth="public",
        methods=["GET"],
        type="http",
        csrf=False,
    )
    def get_products(self, filter_is_eservice=False, limit=None):
        """Return a list of eservice products on the system."""
        domain = []
        if filter_is_eservice:
            domain = [("eservice_code", "!=", False)]
        limit = limit
        records = (
            request.env["product.product"]
            .sudo()
            .search(domain, limit=limit)
        )
        _logger.info(f"Fetched Products = {records}")
        res = records.read(PRODUCT_READ_FIELDS)
        res = [
            dict(
                id=prd.get("id"),
                name=prd.get("name") or "",
                selling_price=prd.get("lst_price") or 0,
                eservice_code=prd.get("eservice_code") or "",
            )
            for prd in res
        ]
        return request.make_json_response(res)
