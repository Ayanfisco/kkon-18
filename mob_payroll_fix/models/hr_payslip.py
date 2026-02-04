# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from odoo import models
import logging

_logger = logging.getLogger(__name__)

class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def compute_sheet(self):
        """
        Override to ensure that date objects (not datetime) are passed to generate_work_entries.
        """
        self.ensure_one()
        _logger.info("compute_sheet called for HrPayslipEmployees")
        # Get the original context
        context = dict(self.env.context)
        _logger.debug("Original context: %s", context)
        # Proceed with normal flow but fix the date types
        if not context.get('active_id'):
            _logger.debug("No active_id in context. Calling super().compute_sheet()")
            return super(HrPayslipEmployees, self).compute_sheet()

        payslip_run = self.env['hr.payslip.run'].browse(context.get('active_id'))
        _logger.debug("Payslip run found: %s", payslip_run)
        # Convert dates if needed
        if hasattr(payslip_run, 'date_start') and hasattr(payslip_run, 'date_end'):
            # Store original values
            original_date_start = payslip_run.date_start
            original_date_end = payslip_run.date_end
            _logger.debug("Original date_start: %s, Original date_end: %s", original_date_start, original_date_end)

            # Temporarily modify the payslip_run object to ensure date type
            if isinstance(original_date_start, datetime):
                _logger.info("Temporarily converting payslip_run.date_start from datetime to date.")
                payslip_run.date_start = original_date_start.date()

            if isinstance(original_date_end, datetime):
                _logger.info("Temporarily converting payslip_run.date_end from datetime to date.")
                payslip_run.date_end = original_date_end.date()

            _logger.debug("Calling super().compute_sheet() with potentially modified dates.")
            # Call super with fixed dates
            result = super(HrPayslipEmployees, self).compute_sheet()
            _logger.debug("super().compute_sheet() returned: %s", result)

            # Restore original values if they were changed
            if isinstance(original_date_start, datetime):
                _logger.info("Restoring payslip_run.date_start to original datetime value.")
                payslip_run.date_start = original_date_start

            if isinstance(original_date_end, datetime):
                _logger.info("Restoring payslip_run.date_end to original datetime value.")
                payslip_run.date_end = original_date_end
            _logger.debug("Payslip run dates after restoring: date_start = %s , date_end= %s", payslip_run.date_start,payslip_run.date_end)
            return result
        _logger.debug("date_start or date_end not found as attributes of payslip_run. Calling super().compute_sheet().")
        return super(HrPayslipEmployees, self).compute_sheet()