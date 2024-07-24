# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID

class Cron(models.Model):
    _inherit = "ir.cron"

    @api.model
    def run_manual_many_cron(self, domain, order):
        for rec in self.search(domain=domain, order=order):
            rec.method_direct_trigger()

    is_api_reach = fields.Boolean('Reach API Schedule')
    number_of_retries = fields.Integer('Number of Retries')
