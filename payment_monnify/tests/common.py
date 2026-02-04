# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.payment.tests.common import PaymentCommon


class MonnifyCommon(PaymentCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.monnify = cls._prepare_provider('monnify', update_values={
            'monnify_api_key': 'FLWPUBK_TEST-abcdef-X',
            'monnify_secret_key': 'FLWSECK_TEST-123456-X',
            'monnify_webhook_secret': 'coincoin_motherducker',
        })

        cls.provider = cls.monnify

        cls.redirect_notification_data = {
            'status': 'successful',
            'tx_ref': cls.reference,
        }
        cls.webhook_notification_data = {
            'event': 'charge.completed',
            'data': {
                'tx_ref': cls.reference,
            },
        }
        cls.verification_data = {
            'status': 'success',
            'data': {
                'id': '123456789',
                'status': 'successful',
                'card': {
                    'last_4digits': '2950',
                    'token': 'flw-t1nf-f9b3bf384cd30d6fca42b6df9d27bd2f-m03k',
                },
                'customer': {
                    'email': 'user@example.com',
                },
            },
        }
