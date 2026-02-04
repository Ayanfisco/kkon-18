# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from odoo import models
import logging

_logger = logging.getLogger(__name__)


class HrContract(models.Model):
    _inherit = 'hr.contract'

    def generate_work_entries(self, date_start, date_stop, force=False):
        """
        Override to ensure date_start and date_stop are date objects, not datetime objects.
        """
        _logger.debug("generate_work_entries called with date_start: %s, date_stop: %s, force: %s", date_start, date_stop, force)

        # Convert to date objects if needed
        if isinstance(date_start, datetime):
            _logger.info("Converting date_start from datetime to date.")
            date_start = date_start.date()

        if isinstance(date_stop, datetime):
            _logger.info("Converting date_stop from datetime to date.")
            date_stop = date_stop.date()

        _logger.debug("Calling super().generate_work_entries with date_start: %s, date_stop: %s, force: %s", date_start, date_stop, force)
        result = super(HrContract, self).generate_work_entries(date_start, date_stop, force=force)
        _logger.debug("super().generate_work_entries returned: %s", result)
        return result