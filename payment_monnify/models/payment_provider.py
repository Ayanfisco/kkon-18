# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint

import requests
import base64
import json

from werkzeug.urls import url_join

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.payment_monnify.const import SUPPORTED_CURRENCIES


_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    # FIX: Changed ondelete parameter to use 'cascade' instead of 'set default'
    code = fields.Selection(
        selection_add=[('payment_monnify', "Monnify")], 
        ondelete={'payment_monnify': 'cascade'}
    )
    
    monnify_api_key = fields.Char(
        string="Monnify API Key",
        help="The key solely used to identify the account with Monnify.",
        required_if_provider='payment_monnify',
    )
    monnify_secret_key = fields.Char(
        string="Monnify Secret Key",
        help="The secret key used to authenticate requests from Monnify.",
        required_if_provider='payment_monnify',
        groups='base.group_system',
    )
    monnify_contract_code = fields.Char(
        string="Monnify Contract Code",
        help="The contract code provided by Monnify.",
        required_if_provider='payment_monnify',
        groups='base.group_system',
    )

    #=== COMPUTE METHODS ===#
    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'payment_monnify').update({
            'support_tokenization': True,
        })

    # === BUSINESS METHODS ===#

    @api.model
    def _get_compatible_providers(self, *args, currency_id=None, is_validation=False, **kwargs):
        """Override of payment to filter out Monnify providers for unsupported currencies.
        
        Args:
            currency_id (int, optional): ID of the currency to check compatibility with.
            is_validation (bool): Whether this is a validation operation.
            **kwargs: Additional keyword arguments.
            
        Returns:
            recordset: Filtered providers that are compatible with the given parameters.
        """

        _logger.debug("=== MONNIFY DEBUG ===")
        _logger.debug("All providers before filtering: %s", self.search([]))
        _logger.debug("Called with args: %s, kwargs: %s", args, kwargs)
        
        providers = super()._get_compatible_providers(*args, **kwargs)
        
        _logger.debug("Providers after parent filter: %s", providers)
        _logger.debug("Monnify providers after parent filter: %s", 
                    providers.filtered(lambda p: p.code == 'payment_monnify'))
        _logger.debug("=== END MONNIFY DEBUG ===")

        _logger.debug("Monnify: " + _("Getting compatible providers for currency %s.", currency_id))
        _logger.debug("Monnify: " + _("Currency ID: %s.", currency_id))
        _logger.debug("Monnify: " + _("Is validation: %s.", is_validation))
        _logger.debug("Monnify: " + _("Args: %s.", args))
        _logger.debug("Monnify: " + _("Kwargs: %s.", kwargs))

        providers = super()._get_compatible_providers(
            *args, currency_id=currency_id, is_validation=is_validation, **kwargs
        )
        
        _logger.debug("Monnify: " + _("Compatible providers: %s.", providers))
        _logger.debug("Monnify: " + _("Monnify providers: %s.", providers.filtered(lambda p: p.code == 'payment_monnify')))

        # Early return if no Monnify providers to check
        monnify_providers = providers.filtered(lambda p: p.code == 'payment_monnify')
        if not monnify_providers:
            return providers

        # Only check currency if one is provided
        if not currency_id:
            return providers

        currency = self.env['res.currency'].browse(currency_id).exists()
        if not currency:
            _logger.warning("Currency with ID %s not found", currency_id)
            return providers

        if currency.name not in SUPPORTED_CURRENCIES:
            _logger.debug(
                "Filtering out Monnify providers as currency %s is not supported",
                currency.name
            )
            providers = providers - monnify_providers

        return providers

    def _monnify_make_request(self, endpoint, payload=None, method='POST'):
        """ Make a request to Monnify API at the specified endpoint.

        Args:
            endpoint (str): The endpoint to be reached on Monnify API.
            payload (dict): The payload of the request.
            method (str): The HTTP method of the request.

        Returns:
             The JSON-formatted content of the response.
        """
        self.ensure_one()

        # Select the base URL based on the provider state
        base_url = 'https://sandbox.monnify.com' if self.state == 'test' else 'https://api.monnify.com'
        
        # Log provider details (without sensitive data)
        _logger.debug("=== MONNIFY PROVIDER DETAILS ===")
        _logger.debug("Provider ID: %s", self.id)
        _logger.debug("Provider Code: %s", self.code)
        _logger.debug("Provider State: %s", self.state)
        _logger.debug("Using Base URL: %s", base_url)
        _logger.debug("API Key (first 5 chars): %s", self.monnify_api_key[:5] + '...' if self.monnify_api_key else 'Not set')
        _logger.debug("Secret Key (first 5 chars): %s", self.monnify_secret_key[:5] + '...' if self.monnify_secret_key else 'Not set')
        _logger.debug("Contract Code: %s", self.monnify_contract_code or 'Not set')
        
        # First, get an access token
        auth_string = f"{self.monnify_api_key}:{self.monnify_secret_key}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        auth_headers = {
            'Authorization': f'Basic {encoded_auth}',
            'Content-Type': 'application/json',
        }
        
        _logger.debug("=== AUTHENTICATING WITH MONNIFY ===")
        _logger.debug("Auth URL: %s/api/v1/auth/login", base_url)
        _logger.debug("Auth Headers: %s", {k: '***' if 'Authorization' in k else v for k, v in auth_headers.items()})
        
        try:
            # Request access token
            auth_url = f"{base_url}/api/v1/auth/login"
            _logger.debug("Making authentication request to: %s", auth_url)
            
            auth_response = requests.post(
                auth_url,
                headers=auth_headers,
                timeout=30
            )
            
            _logger.debug("Auth Response Status: %s", auth_response.status_code)
            _logger.debug("Auth Response Headers: %s", dict(auth_response.headers))
            _logger.debug("Auth Response Body: %s", auth_response.text)
            
            # Check for authentication errors
            if auth_response.status_code == 401:
                _logger.error("Authentication failed with Monnify. Please check your API key and secret key.")
                _logger.error("API Key (first 5 chars): %s", self.monnify_api_key[:5] + '...' if self.monnify_api_key else 'Not set')
                _logger.error("Is Test Mode: %s", self.state == 'test')
                raise ValidationError(_("Authentication failed with Monnify. Please check your API credentials."))
                
            auth_response.raise_for_status()
            
            auth_data = auth_response.json()
            _logger.debug("Auth Data: %s", auth_data)
            
            if not auth_data.get('requestSuccessful') or not auth_data.get('responseBody', {}).get('accessToken'):
                _logger.error("Invalid authentication response from Monnify: %s", auth_data)
                raise ValidationError(_("Invalid response received from Monnify authentication service"))
            
            access_token = auth_data['responseBody']['accessToken']
            _logger.debug("Successfully obtained access token (first 10 chars): %s...", access_token[:10])
                
            # Prepare headers with the access token
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            }

            # Log the request details
            _logger.debug("=== MONNIFY API REQUEST ===")
            _logger.debug("URL: %s", url_join(base_url, endpoint))
            _logger.debug("Method: %s", method)
            _logger.debug("Headers: %s", {k: '***' if 'Authorization' in k else v for k, v in headers.items()})
            _logger.debug("Payload: %s", pprint.pformat(payload) if payload else 'None')

            # Make the actual API request
            request_kwargs = {
                'method': method,
                'url': url_join(base_url, endpoint),
                'headers': headers,
                'timeout': 60,
            }

            # Do not send a JSON body for GET requests to avoid 404/Bad Request
            if method and method.upper() == 'GET':
                if isinstance(payload, dict) and payload:
                    request_kwargs['params'] = payload
            else:
                request_kwargs['json'] = payload or {}

            response = requests.request(**request_kwargs)

            # Log the response details
            _logger.debug("=== MONNIFY API RESPONSE ===")
            _logger.debug("Status Code: %s", response.status_code)
            _logger.debug("Response Headers: %s", dict(response.headers))
            _logger.debug("Response Body: %s", response.text)

            # Parse the JSON response
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            error_details = ""
            if hasattr(e, 'response'):
                try:
                    error_details = e.response.json()
                    _logger.error("Monnify API Error Details: %s", error_details)
                except:
                    error_details = e.response.text
            
            _logger.error(
                "Monnify API HTTP Error: %s - %s\nURL: %s\nHeaders: %s\nResponse: %s",
                e.response.status_code if hasattr(e, 'response') else 'No response',
                str(e),
                e.response.url if hasattr(e, 'response') and hasattr(e.response, 'url') else 'Unknown',
                dict(e.response.headers) if hasattr(e, 'response') and hasattr(e.response, 'headers') else {},
                error_details
            )
            
            if hasattr(e, 'response') and getattr(e.response, 'status_code', None) == 401:
                error_msg = _(
                    "Authentication failed with Monnify. Please check your API credentials and ensure they are correct. "
                    "Make sure you're using the correct environment (test/production) for your credentials."
                )
            else:
                error_msg = _("Monnify API request failed with status %(status)s: %(details)s") % {
                    'status': e.response.status_code if hasattr(e, 'response') else 'Unknown',
                    'details': error_details or str(e)
                }
                
            raise ValidationError(error_msg) from e
            
        except requests.exceptions.RequestException as e:
            _logger.exception("Monnify API request failed")
            error_msg = _("Could not connect to Monnify: %s") % str(e)
            raise ValidationError(error_msg) from e
            
        except json.JSONDecodeError as e:
            _logger.exception("Failed to decode Monnify API response")
            error_msg = _("Invalid response received from Monnify. Please try again later.")
            raise ValidationError(error_msg) from e
            
        except Exception as e:
            _logger.exception("Unexpected error during Monnify API request")
            error_msg = _("An unexpected error occurred while processing your payment. Please try again later.")
            raise ValidationError(error_msg) from e