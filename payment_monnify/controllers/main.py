# Part of Odoo. See LICENSE file for full copyright and licensing details.

import hashlib
import hmac
import json
import logging
import pprint

from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request


_logger = logging.getLogger(__name__)


class MonnifyController(http.Controller):
    _return_url = '/payment/monnify/return'
    _webhook_url = '/payment/monnify/webhook'

    @http.route(_return_url, type='http', methods=['GET'], auth='public')
    def monnify_return_from_checkout(self, **data):
        """ Process the notification data sent by Monnify after redirection from checkout.

        :param dict data: The notification data.
        """
        _logger.info("Handling redirection from Monnify with data:\n%s", pprint.pformat(data))

        # Handle the notification data.
        if data.get('status') != 'cancelled':
            request.env['payment.transaction'].sudo()._handle_notification_data('payment_monnify', data)
        else:  # The customer cancelled the payment by clicking on the close button.
            pass  # Don't try to process this case because the transaction id was not provided.

        # Redirect the user to the status page.
        return request.redirect('/payment/status')

    @http.route(_webhook_url, type='http', methods=['POST'], auth='public', csrf=False)
    def monnify_webhook(self):
        """ Process the notification data sent by Monnify to the webhook.

        :return: An empty string to acknowledge the notification.
        :rtype: str
        """
        # data = request.get_json_data()
        raw_data = http.request.httprequest.data
        decoded_data = raw_data.decode('utf-8')
        data = json.loads(decoded_data)
        _logger.info("Notification received from Monnify with data:\n%s", pprint.pformat(data))
        _logger.info("Raw data:\n%s", raw_data)

        if data['eventType'] == 'SUCCESSFUL_TRANSACTION':
            try:
                # Check the origin of the notification.
                tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
                    'payment_monnify', data['eventData']
                )
                signature = request.httprequest.headers.get('monnify-signature')
                self._verify_notification_signature(signature, tx_sudo, decoded_data)

                # Handle the notification data.
                notification_data = data['eventData']
                tx_sudo._handle_notification_data('payment_monnify', notification_data)
            except ValidationError:  # Acknowledge the notification to avoid getting spammed.
                _logger.exception("Unable to handle the notification data; skipping to acknowledge")
        return request.make_json_response('')

    @staticmethod
    def _verify_notification_signature(received_signature, tx_sudo, data):
        """ Check that the received signature matches the expected one.

        :param dict received_signature: The signature received with the notification data.
        :param recordset tx_sudo: The sudoed transaction referenced by the notification data, as a
            `payment.transaction` record.
        :return: None
        :raise Forbidden: If the signatures don't match.
        """
        # Check for the received signature.
        if not received_signature:
            _logger.warning("Received notification with missing signature.")
            raise Forbidden()

        # Compare the received signature with the expected signature.
        monnify_secret_key = tx_sudo.provider_id.monnify_secret_key

        secret_key_bytes = monnify_secret_key.encode("utf-8") 
        payload_in_bytes = data.encode("utf-8")

        expected_signature = hmac.new(secret_key_bytes, msg=payload_in_bytes, digestmod=hashlib.sha512).hexdigest()

        if not hmac.compare_digest(received_signature, expected_signature):
            _logger.warning("Received notification with invalid signature.")
            raise Forbidden()
