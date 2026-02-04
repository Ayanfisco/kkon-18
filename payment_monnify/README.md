# Monnify

## Technical details

API: [Monnify standard](https://developers.monnify.com/docs/collections/one-time-payments)

This module integrates Monnify using the generic payment with redirection flow based on form
submission provided by the `payment` module.

## Supported features

- Payment with redirection flow
- Webhook notifications

## Usage

- Install the module payment_monnify
- To activate got to:
  - Invoices (Accounting?) -> Configuration -> Payment Providers
  - Select Monnify
  - Enter API Key, API Secret and Contract Code
  - Set State to Enabled or Test Mode as required
  - In the Monnify Portal, Go to Developer -> Webhook URLs
  - Enter the Transaction Completion URL as "{ODOO_URL}/payment/monnify/webhook"Installing Docker on Debian 12 using the apt repository


## Using Payment Providers Across Multiple Companies
- To ensure payment acquirers are accessible and visible in another company:
  - Access the original company (the one initially set up when creating the database).
  - Navigate to the payment providers menu.
  - Enable the multi-company view by selecting the checkboxes next to the company names.
  - Choose an existing payment provider.
  - Duplicate the selected payment provider: Action -> Duplicate.
  - Select the other company in the "Company" field.
  - The payment provider should now be visible and accessible in the other company.