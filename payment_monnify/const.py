# See LICENSE file for full copyright and licensing details.

# The currencies supported by Monnify, in ISO 4217 format.
SUPPORTED_CURRENCIES = [
    'GBP',
    'CAD',
    'CLP',
    'COP',
    'EGP',
    'EUR',
    'GHS',
    'GNF',
    'KES',
    'MWK',
    'MAD',
    'NGN',
    'RWF',
    'SLL',
    'STD',
    'ZAR',
    'TZS',
    'UGX',
    'USD',
    'XAF',
    'XOF',
    'ZMW',
]


# Mapping of transaction states to Monnify payment statuses.
PAYMENT_STATUS_MAPPING = {
    'pending': ['pending auth'],
    'done': ['paid'],
    'cancel': ['pending'],
    'error': ['failed'],
}
