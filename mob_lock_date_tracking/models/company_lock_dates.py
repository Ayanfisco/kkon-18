import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class PeriodLockDates(models.Model):
    _name = 'period.lock.dates'
    _description = 'Period Lock Dates'
    
    company_id = fields.Many2one(
        'res.company', 
        string='Company', 
        required=True,
        default=lambda self: self.env.company,
        tracking=True
    )
    
    period_lock_date = fields.Date(
        string="Period Lock Date",
        tracking=True
    )
    
    fiscalyear_lock_date = fields.Date(
        string="Fiscal Year Lock Date", 
        tracking=True
    )
    
    tax_lock_date = fields.Date(
        string="Tax Lock Date",
        tracking=True
    )
    
    def write(self, vals):
        """Override write to automatically update company lock dates"""
        _logger.info("=== PERIOD LOCK DATES: Write method called ===")
        _logger.info(f"Values to write: {vals}")
        _logger.info(f"Current record values: period_lock_date={self.period_lock_date}, fiscalyear_lock_date={self.fiscalyear_lock_date}, tax_lock_date={self.tax_lock_date}")
        
        result = super().write(vals)
        
        # Update company lock dates if any of the tracking fields changed
        lock_date_fields = ['period_lock_date', 'fiscalyear_lock_date', 'tax_lock_date']
        if any(field in vals for field in lock_date_fields):
            _logger.info("Lock date fields detected in update, updating company dates")
            for record in self:
                company_vals = {}
                for field in lock_date_fields:
                    if field in vals:
                        company_vals[field] = vals[field]
                
                if company_vals:
                    _logger.info(f"Updating company {record.company_id.name} with values: {company_vals}")
                    try:
                        record.company_id.write(company_vals)
                        _logger.info("Successfully updated company lock dates")
                    except Exception as e:
                        _logger.error(f"Error updating company lock dates: {e}")
        else:
            _logger.info("No lock date fields in update, skipping company update")
        
        _logger.info("=== PERIOD LOCK DATES: Write method completed ===")
        return result 