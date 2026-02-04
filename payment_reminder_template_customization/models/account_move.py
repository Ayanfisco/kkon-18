from odoo import models, fields, api
from datetime import date

class AccountMove(models.Model):
    _inherit = 'account.move'

    def cron_upcoming_invoice_reminders(self):
        """Send reminders for invoices due in 5, 10, 15, 20 days"""
        today = date.today()
        reminder_days = [5, 10, 15, 20]  # stages you want

        invoices = self.search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', '=', 'not_paid'),
            ('invoice_date_due', '!=', False),
        ])

        for inv in invoices:
            days_before_due = (inv.invoice_date_due - today).days
            if days_before_due in reminder_days:
                # Choose email template based on how many days left
                template_xml_id = f'your_module.invoice_reminder_{days_before_due}_days'
                template = self.env.ref(template_xml_id, raise_if_not_found=False)
                if template:
                    template.send_mail(inv.id, force_send=True)
