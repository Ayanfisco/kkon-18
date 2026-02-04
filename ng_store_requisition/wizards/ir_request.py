from odoo import api, fields, models


class IrRequestWizard(models.TransientModel):
    """docstring for IRReasons"""

    _name = "ir.request.wizard"
    _description = "ir.request.wizard"

    reason = fields.Text(string="Reason", required=True)

    def reject(self):
        request_id = self.env.context.get("request_id")
        rejecter_name = self.env.context.get("rejecter_name")
        if request_id:
            request_id = self.env["ng.store.request"].browse([request_id])
            # send email here
            request_id.write({"state": "draft", "reason": self.reason})

            mail_template = self.env.ref("ng_store_requisition.ng_store_requisition_reject")
            mail_template.with_context({'rejecter_name': rejecter_name, 'reason': self.reason}).send_mail(request_id.id, force_send=True)
            return {"type": "ir.actions.act_window_close"}
