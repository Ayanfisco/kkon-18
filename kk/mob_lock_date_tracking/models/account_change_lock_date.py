import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class AccountChangeLockDate(models.TransientModel):
    _inherit = 'account.change.lock.date'
    
    def change_lock_date(self):
        """Override change_lock_date to track changes"""
        _logger.info("=== LOCK DATE TRACKING: change_lock_date method called ===")
        _logger.info(f"Current values: period_lock_date={self.period_lock_date}, fiscalyear_lock_date={self.fiscalyear_lock_date}, tax_lock_date={self.tax_lock_date}")
        
        # Get or create lock dates record for current company
        lock_dates = self.env['period.lock.dates'].search([('company_id', '=', self.env.company.id)], limit=1)
        _logger.info(f"Found existing lock_dates record: {lock_dates}")
        
        if not lock_dates:
            _logger.info("Creating new lock_dates record")
            lock_dates = self.env['period.lock.dates'].create({'company_id': self.env.company.id})
            _logger.info(f"Created lock_dates record: {lock_dates}")
        
        # Update the lock dates (this will automatically update company dates via write method)
        update_vals = {
            'period_lock_date': self.period_lock_date,
            'fiscalyear_lock_date': self.fiscalyear_lock_date,
            'tax_lock_date': self.tax_lock_date,
        }
        _logger.info(f"Updating lock_dates with values: {update_vals}")
        
        try:
            lock_dates.write(update_vals)
            _logger.info("Successfully updated lock_dates record")
        except Exception as e:
            _logger.error(f"Error updating lock_dates: {e}")
        
        # Call the original method
        result = super().change_lock_date()
        _logger.info("=== LOCK DATE TRACKING: change_lock_date method completed ===")
        return result