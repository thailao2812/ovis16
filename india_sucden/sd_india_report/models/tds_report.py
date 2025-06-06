# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
import re
DATE_FORMAT = "%Y-%m-%d"

class TDSReport(models.Model):
    _name = 'tds.report'
    _description = 'TDS Report'
    _auto = False

    financial_year_id = fields.Many2one('financial.year', string='Financial Year')
    partner_id = fields.Many2one('res.partner', string='Vendor Name')
    partner_code = fields.Char(string='Vendor Code')
    pan_number = fields.Char(string='PAN Number')
    pan_status = fields.Char(string='PAN Status')
    percent_tds = fields.Float(string='Percent TDS (%)')
    request_amount = fields.Float(string='Request Amount')
    interest_amount = fields.Float(string='Interest Amount')
    total_purchase = fields.Float(string='Total Purchase')
    threshold_amount = fields.Float(string='Threshold Limit')
    tds_assessable_calculation = fields.Float(string='TDS Assessable Calculation')
    tds_amount_calculation = fields.Float(string='TDS Amount Calculation')
    tds_assessable_payment = fields.Float(string='TDS Assessable Payment')
    tds_amount_payment = fields.Float(string='TDS Amount Payment')
    different_tds_assessable = fields.Float(string='Different TDS Assessable')
    different_tds_amount = fields.Float(string='Different TDS Amount')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'tds_report')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW public.tds_report AS
            select row_number() OVER (
                                ORDER BY (
                                    fy.id,
                                    partner.id
                                ) DESC  
            ) AS id, fy.id as financial_year_id, partner.id as partner_id, partner.partner_code as partner_code, partner.pan_number as pan_number,
       CASE
    WHEN partner.pan_number IS NOT NULL
         AND partner.pan_number != ''
         AND (partner.with_declaration IS NULL OR NOT partner.with_declaration) THEN 'With PAN'
    WHEN (partner.pan_number IS NULL
          OR partner.pan_number = '')
         AND (partner.with_declaration IS NULL OR NOT partner.with_declaration) THEN 'Without PAN'
    WHEN partner.with_declaration THEN 'With Declaration'
    ELSE 'Unknown'
END AS pan_status,
    CASE
    WHEN partner.pan_number IS NOT NULL
         AND partner.pan_number != ''
         AND (partner.with_declaration IS NULL OR NOT partner.with_declaration) THEN 0.1
    WHEN (partner.pan_number IS NULL
          OR partner.pan_number = '')
         AND (partner.with_declaration IS NULL OR NOT partner.with_declaration) THEN 5
    WHEN partner.with_declaration THEN 0
    ELSE 0
END AS percent_tds, sum(rp.request_amount) as request_amount, sum(rp.interest_amount) as interest_amount,
                    sum(rp.request_amount) + sum(rp.interest_amount) as total_purchase, fy.max_value as threshold_amount,
                    CASE WHEN sum(rp.request_amount) + sum(rp.interest_amount) - fy.max_value <= 0 THEN 0
                        ELSE sum(rp.request_amount) + sum(rp.interest_amount) - fy.max_value END as tds_assessable_calculation,
                    CASE
        WHEN (sum(rp.request_amount) + sum(rp.interest_amount)) - fy.max_value <= 0 THEN 0

        WHEN partner.pan_number IS NOT NULL
             AND partner.pan_number != ''
             AND (partner.with_declaration IS NULL OR NOT partner.with_declaration) THEN
             CASE
                WHEN ABS((sum(rp.request_amount) + sum(rp.interest_amount) - fy.max_value) * (0.1/100) - ROUND((sum(rp.request_amount) + sum(rp.interest_amount) - fy.max_value) * (0.1/100))) = 0.5
                    THEN CEIL((sum(rp.request_amount) + sum(rp.interest_amount) - fy.max_value) * (0.1/100))
                ELSE
                    ROUND((sum(rp.request_amount) + sum(rp.interest_amount) - fy.max_value) * (0.1/100))
             END

        WHEN (partner.pan_number IS NULL
              OR partner.pan_number = '')
             AND (partner.with_declaration IS NULL OR NOT partner.with_declaration) THEN
             CASE
                WHEN ABS((sum(rp.request_amount) + sum(rp.interest_amount) - fy.max_value) * (5/100) - ROUND((sum(rp.request_amount) + sum(rp.interest_amount) - fy.max_value) * (5/100))) = 0.5
                    THEN CEIL((sum(rp.request_amount) + sum(rp.interest_amount) - fy.max_value) * (5/100))
                ELSE
                    ROUND((sum(rp.request_amount) + sum(rp.interest_amount) - fy.max_value) * (5/100))
             END

        WHEN partner.with_declaration THEN 0
        ELSE 0
    END as tds_amount_calculation, sum(rp.tds_assessable_value) as tds_assessable_payment, sum(rp.tds_amount) as tds_amount_payment,
                                   -- Tính toán phần chênh lệch
    (CASE
        WHEN sum(rp.request_amount) + sum(rp.interest_amount) - fy.max_value <= 0 THEN 0
        ELSE sum(rp.request_amount) + sum(rp.interest_amount) - fy.max_value
    END) - sum(rp.tds_assessable_value) as different_tds_assessable,

    (CASE
        WHEN (sum(rp.request_amount) + sum(rp.interest_amount)) - fy.max_value <= 0 THEN 0
        WHEN partner.pan_number IS NOT NULL
             AND partner.pan_number != ''
             AND (partner.with_declaration IS NULL OR NOT partner.with_declaration) THEN
             CASE
                WHEN ABS((sum(rp.request_amount) + sum(rp.interest_amount) - fy.max_value) * (0.1/100) - ROUND((sum(rp.request_amount) + sum(rp.interest_amount) - fy.max_value) * (0.1/100))) = 0.5
                    THEN CEIL((sum(rp.request_amount) + sum(rp.interest_amount) - fy.max_value) * (0.1/100))
                ELSE
                    ROUND((sum(rp.request_amount) + sum(rp.interest_amount) - fy.max_value) * (0.1/100))
             END
        WHEN (partner.pan_number IS NULL OR partner.pan_number = '')
             AND (partner.with_declaration IS NULL OR NOT partner.with_declaration) THEN
             CASE
                WHEN ABS((sum(rp.request_amount) + sum(rp.interest_amount) - fy.max_value) * (5/100) - ROUND((sum(rp.request_amount) + sum(rp.interest_amount) - fy.max_value) * (5/100))) = 0.5
                    THEN CEIL((sum(rp.request_amount) + sum(rp.interest_amount) - fy.max_value) * (5/100))
                ELSE
                    ROUND((sum(rp.request_amount) + sum(rp.interest_amount) - fy.max_value) * (5/100))
             END
        WHEN partner.with_declaration THEN 0
        ELSE 0
    END) - sum(rp.tds_amount) as different_tds_amount

from request_payment rp
join financial_year fy on fy.id = rp.financial_year_id
join res_partner partner on partner.id = rp.partner_id
group by fy.id, partner.id;
        """)

