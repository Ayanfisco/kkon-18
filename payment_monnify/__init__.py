# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from . import controllers
from . import models

from odoo.addons.payment import setup_provider, reset_payment_provider

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    try:
        setup_provider(env, 'payment_monnify')

        # Verify the provider was created
        provider = env['payment.provider'].search([('code', '=', 'payment_monnify')], limit=1)
        if provider:
            _logger.info('Monnify provider found: %s (ID: %s, State: %s)',
                         provider.name, provider.id, provider.state)
            _logger.info('Provider details: %s', {
                'code': provider.code,
                'state': provider.state,
                'support_tokenization': provider.support_tokenization,
                'is_published': provider.is_published,
            })
        else:
            _logger.warning('Monnify provider not found after initialization')

    except Exception as e:
        _logger.error('Error setting up Monnify payment provider: %s', str(e), exc_info=True)


def uninstall_hook(env):
    reset_payment_provider(env, 'payment_monnify')


# # Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# import logging
# from . import controllers
# from . import models
#
# from odoo.addons.payment import setup_provider, reset_payment_provider
#
# _logger = logging.getLogger(__name__)
#
# def post_init_hook(cr, registry):
#     try:
#         setup_provider(cr, registry, 'payment_monnify')
#
#         # Verify the provider was created
#         env = registry(cr.cursor().cursor(), 1, {})
#         provider = env['payment.provider'].search([('code', '=', 'payment_monnify')], limit=1)
#         if provider:
#             _logger.info('Monnify provider found: %s (ID: %s, State: %s)',
#                        provider.name, provider.id, provider.state)
#             _logger.info('Provider details: %s', {
#                 'code': provider.code,
#                 'state': provider.state,
#                 'allow_tokenization': provider.allow_tokenization,
#                 'is_published': provider.is_published,
#             })
#         else:
#             _logger.warning('Monnify provider not found after initialization')
#
#     except Exception as e:
#         _logger.error('Error setting up Monnify payment provider: %s', str(e), exc_info=True)
#
# def uninstall_hook(cr, registry):
#     reset_payment_provider(cr, registry, 'payment_monnify')
