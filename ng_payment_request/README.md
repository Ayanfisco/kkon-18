
## **FOB Issue Resolutions:**

1. **Journal Entry Currency Handling:**
   - Updated the debit and credit amounts to reflect the company's base currency (Naira).

2. **Field Readonly Conditions:**
   - Set `requested_amount`, `approved_amount` and `description`  fields to readonly when the form state is not in 'draft'.

3. **Currency Conversion Rate Correction:**
   - Resolved the currency conversion rate discrepancy.

4. **Field Update for Company Currency Amount:**
   - Modified `amount_in_company_currency` to display the updated company currency amount.

4. **Make Payment Submission Error:**
   - Fixed error that occurs when user tries to make payment to an employee that has not set their address.
