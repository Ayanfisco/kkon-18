# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint
import json

from werkzeug import urls

from odoo import _, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_monnify.const import PAYMENT_STATUS_MAPPING
from odoo.addons.payment_monnify.controllers.main import MonnifyController


_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return Monnify-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific processing values.
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'payment_monnify':
            return res

        # Initiate the payment and retrieve the payment link data.
        base_url = self.provider_id.get_base_url()
        payload = {
            "amount": self.amount,
            "customerName": self.partner_name,
            "customerEmail": self.partner_email,
            "paymentReference": self.reference,
            "paymentDescription": f"Payment for {self.reference}",
            "currencyCode": self.currency_id.name,
            "contractCode": self.provider_id.monnify_contract_code,
            "redirectUrl": urls.url_join(base_url, MonnifyController._return_url),
        }
        payment_link_data = self.provider_id._monnify_make_request('api/v1/merchant/transactions/init-transaction', payload=payload)
        
        # Extract the payment link URL and embed it in the redirect form.
        rendering_values = {
            'api_url': payment_link_data['responseBody']['checkoutUrl'],
        }

        self.write({'provider_reference': payment_link_data['responseBody']['transactionReference']})

        return rendering_values

    def _send_payment_request(self):
        """ Override of payment to send a payment request to Monnify.

        Note: self.ensure_one()

        :return: None
        :raise UserError: If the transaction is not linked to a token.
        """
        super()._send_payment_request()
        if self.provider_code != 'payment_monnify':
            return

        # Prepare the payment request to Monnify.
        if not self.token_id:
            raise UserError("Monnify: " + _("The transaction is not linked to a token."))

        first_name, last_name = payment_utils.split_partner_name(self.partner_name)
        data = {
            'token': self.token_id.provider_reference,
            'email': self.token_id.monnify_customer_email,
            'amount': self.amount,
            'currency': self.currency_id.name,
            'country': self.company_id.country_id.code,
            'paymentReference': self.reference,
            'first_name': first_name,
            'last_name': last_name,
            'ip': payment_utils.get_customer_ip_address(),
        }

        # Make the payment request to Monnify.
        response_content = self.provider_id._monnify_make_request(
            'tokenized-charges', payload=data
        )

        # Handle the payment request response.
        _logger.info(
            "payment request response for transaction with reference %s:\n%s",
            self.reference, pprint.pformat(response_content)
        )
        self._handle_notification_data('monnify', response_content['responseBody'])

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override of payment to find the transaction based on Monnify data.

        :param str provider_code: The code of the provider that handled the transaction.
        :param dict notification_data: The notification data sent by the provider.
        :return: The transaction if found.
        :rtype: recordset of `payment.transaction`
        :raise ValidationError: If inconsistent data were received.
        :raise ValidationError: If the data match no transaction.
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'payment_monnify' or len(tx) == 1:
            return tx

        reference = notification_data.get('paymentReference')
        if not reference:
            raise ValidationError("Monnify: " + _("Received data with missing reference."))

        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'payment_monnify')])
        if not tx:
            raise ValidationError(
                "Monnify: " + _("No transaction found matching reference %s.", reference)
            )
        return tx

    def _process_notification_data(self, notification_data):
        """ Override of payment to process the transaction based on Monnify data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider.
        :return: None
        :raise ValidationError: If inconsistent data were received.
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'payment_monnify' or self.provider_id.code != 'payment_monnify':
            return
        
        # Verify the notification data using URL-encoded path parameter as required by Monnify
        encoded_reference = urls.url_quote(self.provider_reference, safe='')
        endpoint = f'api/v2/transactions/{encoded_reference}'
        verification_response_content = self.provider_id._monnify_make_request(endpoint, method='GET')
        _logger.info(verification_response_content['responseBody'])
        verified_data = verification_response_content['responseBody']

        # Process the verified notification data.
        payment_status = verified_data['paymentStatus'].lower()
        if payment_status in PAYMENT_STATUS_MAPPING['pending']:
            self._set_pending()
        elif payment_status in PAYMENT_STATUS_MAPPING['done']:
            self._set_done()
            has_token_data = 'token' in verified_data.get('card', {})
            if self.tokenize and has_token_data:
                self._monnify_tokenize_from_notification_data(verified_data)
        elif payment_status in PAYMENT_STATUS_MAPPING['cancel']:
            self._set_canceled()
        elif payment_status in PAYMENT_STATUS_MAPPING['error']:
            self._set_error(_(
                "An error occurred during the processing of your payment (status %s). Please try "
                "again.", payment_status
            ))
        else:
            _logger.warning(
                "Received data with invalid payment status (%s) for transaction with reference %s.",
                payment_status, self.reference
            )
            self._set_error("Monnify: " + _("Unknown payment status: %s", payment_status))

    def _monnify_tokenize_from_notification_data(self, notification_data):
        """ Create a new token based on the notification data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider.
        :return: None
        """
        self.ensure_one()

        token = self.env['payment.token'].create({
            'provider_id': self.provider_id.id,
            'payment_details': notification_data['card']['last_4digits'],
            'partner_id': self.partner_id.id,
            'provider_ref': notification_data['card']['token'],
            'monnify_customer_email': notification_data['customer']['email'],
            'verified': True,  # The payment is confirmed, so the payment method is valid.
        })
        self.write({
            'token_id': token,
            'tokenize': False,
        })
        _logger.info(
            "created token with id %(token_id)s for partner with id %(partner_id)s from "
            "transaction with reference %(ref)s",
            {
                'token_id': token.id,
                'partner_id': self.partner_id.id,
                'ref': self.reference,
            },
        )
