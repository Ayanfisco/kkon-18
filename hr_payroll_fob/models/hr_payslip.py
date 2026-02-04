from datetime import datetime

from odoo import api, fields, models, _
from odoo.tools import date_utils


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.depends('employee_id', 'contract_id', 'struct_id', 'date_from', 'date_to')
    def _compute_worked_days_line_ids(self):
        if not self or self.env.context.get('salary_simulation'):
            return
        valid_slips = self.filtered(
            lambda p: p.employee_id and p.date_from and p.date_to and p.contract_id and p.struct_id)
        # Make sure to reset invalid payslip's worked days line
        self.update({'worked_days_line_ids': [(5, 0, 0)]})
        # Ensure work entries are generated for all contracts
        generate_from = min(p.date_from for p in self)
        current_month_end = date_utils.end_of(fields.Date.today(), 'month')
        generate_to = max(min(fields.Date.to_date(p.date_to),
                          current_month_end) for p in self)
        generate_from = datetime.combine(generate_from, datetime.min.time())
        generate_to = datetime.combine(generate_to, datetime.max.time())
        self.mapped('contract_id')._generate_work_entries(
            generate_from, generate_to)

        for slip in valid_slips:
            if not slip.struct_id.use_worked_day_lines:
                continue
            # YTI Note: We can't use a batched create here as the payslip may not exist
            slip.update(
                {'worked_days_line_ids': slip._get_new_worked_days_lines()})
