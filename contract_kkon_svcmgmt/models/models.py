from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import json
import requests
import logging

_logger = logging.getLogger(__name__)
from werkzeug.urls import url_join
from odoo.addons.payment import utils as payment_utils

class ContractSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    email_notifications = fields.Boolean(string='Send Email Notifications', default=False, config_parameter='contract_kkon_svcmgmt.email_notifications')
    api_enabled = fields.Boolean(string='Enable Service Management API', default=False, config_parameter='contract_kkon_svcmgmt.api_enabled')
    api_url = fields.Char(string='API URL', config_parameter='contract_kkon_svcmgmt.api_url')
    api_username = fields.Char(string='API Username', config_parameter='contract_kkon_svcmgmt.api_username')
    api_password = fields.Char(string='API Password', config_parameter='contract_kkon_svcmgmt.api_password')


class ContractContractInherited(models.Model):
    _inherit = 'contract.contract'

    name = fields.Char(required=False, string='Service ID')
    contract_template_id = fields.Many2one(string='Service Template')
    ip_address = fields.Char(required=False, string='IP Address')
    enabled = fields.Boolean(required=False, string='Enabled', default=False)
    activated = fields.Boolean(required=False, string='Activated', default=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'name' not in vals:
                sequence_value = self.env['ir.sequence'].next_by_code('contract.contract.sequence') or '/'
                vals['name'] = sequence_value
        records = super(ContractContractInherited, self).create(vals_list)
        for record in records:
            self.call_external_api(record, 'create')
            record.recurring_create_invoice()
        return records

    def write(self, vals):
        res = super(ContractContractInherited, self).write(vals)
        for record in self:
            self.call_external_api(record, 'update')
        return res

    def unlink(self):
        for record in self:
            self.call_external_api(record, 'delete')
        return super(ContractContractInherited, self).unlink()

    def sync_data(self):
        for record in self:
            self.call_external_api(record, 'synchronize')
        return True


    def call_external_api(self, record, operation):
        api_enabled = self.env['ir.config_parameter'].sudo().get_param('contract_kkon_svcmgmt.api_enabled')
        if api_enabled:
            auth_token = ''
            base_url = self.env['ir.config_parameter'].sudo().get_param('contract_kkon_svcmgmt.api_url')

            try:
                endpoint = "api/auth"
                auth_url = url_join(base_url, endpoint)
                auth_payload = {"email": self.env['ir.config_parameter'].sudo().get_param('contract_kkon_svcmgmt.api_username'), 
                    "password": self.env['ir.config_parameter'].sudo().get_param('contract_kkon_svcmgmt.api_password')}
                auth_response = requests.post(auth_url, json=auth_payload)
                if auth_response.status_code == 200:
                    auth_token = auth_response.text
                else:
                    _logger.exception(f"Error: Request failed with status code {auth_response.status_code}")
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                _logger.exception("Unable to reach endpoint at %s", auth_url)

            try:
                endpoint = "api/account"
                url = url_join(base_url, endpoint)
                headers = {'x-auth-token': auth_token}
                payload = {
                    "id": f"{record.name}",
                    "enabled": record.enabled,
                    "activated": record.activated,
                    "fullname": f"{record.partner_id.name}",
                    "company": f"{record.partner_id.company_id.name}",
                    "phone": f"{record.partner_id.phone}",
                    "mobile": f"{record.partner_id.mobile}",
                    "address": f"{record.partner_id.contact_address}",
                    "comment": f"{record.name}",
                    "gpslat": "0",
                    "gpslong": "0",
                    "expiration": f"{record.recurring_next_date.strftime('%Y-%m-%dT%H:%M')}",
                    "staticip": f"{record.ip_address}",
                    "ipsubnet": "0",
                    "createdby": 1,
                    "nasid": "1",
                    "email": f"{record.partner_id.email}",
                    "downrate": "0",
                    "uprate": "0",
                    "enableburst": False,
                    "dlburstlimit": "0",
                    "ulburstlimit": "0",
                    "dlburstthreshold": "0",
                    "ulburstthreshold": "0",
                    "dlbursttime": "0",
                    "ulbursttime": "0",
                    "priority": "0"
                }

                if operation == 'create':
                    response = requests.post(url, json=payload, headers=headers, timeout=10)
                    if response.status_code == 200:
                        pass
                    else:
                        _logger.exception(f"Error: Request failed with status code {response.status_code}")
                elif operation == 'update':
                    url = f"{url}/{record.name}"
                    response = requests.put(url, json=payload, headers=headers, timeout=10)
                    if response.status_code != 200:
                        _logger.exception(f"Error: Request failed with status code {response.status_code}")
                elif operation == 'synchronize':
                    url = f"{url}/{ record.name}"
                    payload={}
                    response = requests.get(url, json=payload, headers=headers, timeout=10)
                    if response.status_code == 200:
                        json_response = response.json()
                        self.write({
                            'enabled': json_response['enabled'], 
                            'activated': json_response['activated'], 
                            'ip_address': json_response['staticip']
                        })
                    else:
                        _logger.exception(f"Error: Request failed with status code {response.status_code}")
                elif operation == 'delete':
                    url = f"{url}/{record.name}"
                    response = requests.delete(url, json=payload, headers=headers, timeout=10)
                    if response.status_code != 200:
                        _logger.exception(f"Error: Request failed with status code {response.status_code}")
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                _logger.exception("Unable to reach endpoint at %s", url)

    def _generate_recurring_invoice(self):
        invoices = super(ContractContractInherited, self)._generate_recurring_invoice()
        for invoice in invoices:
            self.send_invoice_email(invoice)
        return invoices

    def _cron_generate_invoices(self):
        contracts = self.search([('enabled', '=', True)])
        for contract in contracts:
            if contract.recurring_next_date == fields.Date.today() + relativedelta(days=15):
                contract._generate_recurring_invoice()

    def _send_reminder(self, days, template_ref, is_overdue=False):
        today = fields.Date.today()
        domain = [
            ('state', '=', 'posted'),
            ('payment_state', '!=', 'paid')
        ]
        
        if is_overdue:
            due_date = today - timedelta(days=days)
        else:
            due_date = today + timedelta(days=days)
        
        domain.append(('invoice_date_due', '=', due_date)) 

        invoices = self.env['account.move'].search(domain)
        template_id = self.env.ref(template_ref).id
        template = self.env['mail.template'].browse(template_id)

        for invoice in invoices:
            # Customize the email subject and body based on days and overdue status
            if is_overdue:
                template.subject = template.subject.replace(
                    '[DAYS]', str(abs(days))
                ).replace('[OVERDUE]', 'overdue')
                template.body_html = template.body_html.replace(
                    '[DAYS]', str(abs(days))
                ).replace('[OVERDUE]', 'overdue')
            else:
                template.subject = template.subject.replace(
                    '[DAYS]', str(days)
                ).replace('[OVERDUE]', 'due soon')
                template.body_html = template.body_html.replace(
                    '[DAYS]', str(days)
                ).replace('[OVERDUE]', 'due soon')
            
            template.send_mail(invoice.id, force_send=True)

    def _cron_send_reminders(self):
        reminder_days_before = [10, 5]
        reminder_days_after = [1]

        for days in reminder_days_before:
            self._send_reminder(days, 'contract_kkon_svcmgmt.upcoming_invoice_reminder_email')

        for days in reminder_days_after:
            self._send_reminder(days, 'contract_kkon_svcmgmt.outstanding_invoice_reminder_email', is_overdue=True)


    def _compute_invoice_status(self):
        for contract in self:
            if contract._get_related_invoices():
                draft_invoices = contract._get_related_invoices().filtered(lambda invoice: invoice.state == 'draft')
                unpaid_invoices = contract._get_related_invoices().filtered(lambda invoice: invoice.invoice_has_outstanding)
                due_date_passed = any(inv.invoice_date_due and inv.invoice_date_due <= fields.Date.today() for inv in unpaid_invoices)
                contract.enabled = not due_date_passed and not unpaid_invoices and not draft_invoices
            else:
                contract.enabled = False

    @api.model
    def _cron_update_contract_status(self):
        _logger.info("Checking overdue invoices and services...")
        contracts = self.search([])
        for contract in contracts:
            contract._compute_invoice_status()

    def send_upcoming_invoice_reminder_email(self):
        for record in self:
            template = self.env.ref('contract_kkon_svcmgmt.upcoming_invoice_reminder_email')
            template.send_mail(record.id, force_send=True)

    def send_outstanding_invoice_reminder_email(self):
        for record in self:
            template = self.env.ref('contract_kkon_svcmgmt.outstanding_invoice_reminder_email')
            template.send_mail(record.id, force_send=True)

    def send_invoice_email(self, invoice):
        template_id = self.env.ref('contract_kkon_svcmgmt.invoice_email').id
        self.env['mail.template'].browse(template_id).send_mail(invoice.id, force_send=True)

    # Update API Details
    @api.model
    def update_api_credentials(self):
        for record in self:
            record.call_external_api(record, 'update_api_credentials')
