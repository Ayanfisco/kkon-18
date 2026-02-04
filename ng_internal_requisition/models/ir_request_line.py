from datetime import datetime
from odoo import models, fields, api, _


class IRRequestApprove(models.Model):
    _name = "ng.ir.request.approve"
    _description = "ng.ir.request.approve"

    STATE = [
        ("not_available", "Not Available"),
        ("partially_available", "Partially Available"),
        ("available", "Available"),
        ("awaiting", "Awaiting Availability"),
    ]

    request_id = fields.Many2one(comodel_name="ng.ir.request", string="Request")
    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    quantity = fields.Float(string="Quantity", default=1.0)
    uom = fields.Many2one(comodel_name="uom.uom", string="UOM", related="product_id.uom_id", store=True)
    purchase_agreement_id = fields.Many2one(
        comodel_name="purchase.requisition", string="Purchase Agreement", readonly=True
    )   
    button_show_state = fields.Boolean(string="Show State", compute="_compute_button_show_state")

    @api.depends("product_id", "request_id.state")
    def _compute_button_show_state(self):
        for rec in self:
            rec.button_show_state = rec.request_id.state == "approval1"

    def procure(self):
        product_id, quantity = self.product_id, self.quantity - self.qty
        requisition = self.env["purchase.requisition"]
        line = self.env["purchase.requisition.line"]
        request_identity = self.request_id.name
        requisition_id = requisition.create({"name": ""})
        payload = {
            "product_id": product_id.id,
            "product_uom_id": product_id.uom_id.id,
            "product_qty": quantity,
            "qty_ordered": quantity,
            "requisition_id": requisition_id.id,
            "price_unit": product_id.standard_price,
        }
        line.create(payload)
        self.purchase_agreement_id = requisition_id.id
        # Rename the purchase requestion name to ref
        origin = "{}".format(request_identity,)
        requisition_id.write({"name": origin})
