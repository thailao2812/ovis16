# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
DIFFERENT_SYSTEM = 0.1

class DeductionLine(models.Model):
    _name = 'deduction.line'

    name = fields.Many2one('deduction.quality', string='Description')
    request_kcs_line_id = fields.Many2one('request.kcs.line')
    request_kcs_line_id_2nd = fields.Many2one('request.kcs.line')
    percent = fields.Float(string='% Quality Dept')
    kg = fields.Float(string='Kgs Quality Dept', compute='_compute_kg', store=True)
    commercial_input = fields.Float(string='Kgs Commercial Dept')
    reject = fields.Boolean(string='Reject')
    remark = fields.Text(string='Remark Comm Dept')

    @api.depends('name', 'percent', 'request_kcs_line_id', 'request_kcs_line_id.product_qty',
                 'request_kcs_line_id.categ_id', 'request_kcs_line_id.categ_id')
    def _compute_kg(self):
        for record in self:
            if record.percent == 0:
                record.kg = 0
            if record.name.code in ['4_kinds_deduction', 'WB']:
                if record.percent != 0:
                    tolerance_quality = self.env['tolerance.quality'].search([
                        ('product_category_id', '=', record.request_kcs_line_id_2nd.categ_id.id)
                    ], limit=1)
                    if tolerance_quality:
                        balance = record.percent - tolerance_quality.tolerance_percent
                        if balance > 0:
                            deduction = balance * tolerance_quality.after_deduction
                            record.kg = (deduction/100) * record.request_kcs_line_id_2nd.product_qty
                        if balance <= 0:
                            record.kg = 0
                    else:
                        record.kg = 0
                else:
                    record.kg = 0
            if record.name.code not in ['BB', 'Bleach', 'IDB', 'RB', 'OTH', '4_kinds_deduction', 'MD', 'WB']:
                if record.percent != 0:
                    record.kg = (record.percent/100) * record.request_kcs_line_id.product_qty
                else:
                    record.kg = 0
            if record.name.code == 'MD':
                record.reject = False
                percent = record.percent
                rule = self.env['moisture.configuration'].search([
                    ('product_category_id', '=', record.request_kcs_line_id.categ_id.id),
                    ('state', '=', 'approve'),
                    ('crop_id', '=', record.request_kcs_line_id.picking_id.crop_id.id)
                ])
                if rule:
                    if percent > rule.reject_percent:
                        record.reject = True
                        record.kg = 0
                    else:
                        checking = self.env['moisture.configuration.line'].search([
                            ('moisture_id', '=', rule.id),
                        ]).filtered(lambda x: x.from_percent <= percent <= x.to_percent)
                        if checking:
                            another_check = self.env['moisture.configuration.line'].search([
                                ('moisture_id', '=', rule.id),
                                ('to_percent', '<', checking.from_percent)
                            ])
                            kg = 0
                            if another_check:
                                for i in another_check.sorted(lambda x: x.to_percent):
                                    basis_diff = i.to_percent - i.from_percent + DIFFERENT_SYSTEM
                                    kg += round((basis_diff/100) * record.request_kcs_line_id.product_qty * (i.deduction_percent/100) * 100, 2)
                                for check in checking:
                                    max_to_percent = max(another_check.mapped('to_percent'))
                                    min_from_percent = min(another_check.mapped('from_percent'))
                                    basic_diff = max_to_percent - min_from_percent + DIFFERENT_SYSTEM
                                    kg += round(((percent - rule.standard - basic_diff) / 100) * record.request_kcs_line_id.product_qty * (check.deduction_percent/100) * 100, 2)
                                record.kg = kg
                            else:
                                different = percent - rule.standard
                                record.kg = (different/100) * record.request_kcs_line_id.product_qty * (checking.deduction_percent/100) * 100
                        if not checking:
                            record.kg = 0
                else:
                    record.kg = 0

            if record.name.code == 'OD':
                percent = record.percent
                rule = self.env['moisture.configuration'].search([
                    ('product_category_id', '=', record.request_kcs_line_id.categ_id.id),
                    ('state', '=', 'approve'),
                    ('using_deduction', '=', True),
                    ('crop_id', '=', record.request_kcs_line_id.picking_id.crop_id.id)
                ])
                if rule:
                    if percent > rule.standard_outturn_percent:
                        record.kg = 0
                    if 0 < percent <= rule.standard_outturn_percent:
                        diff = rule.standard_outturn_percent - percent
                        record.kg = (diff/100) * record.request_kcs_line_id.product_qty
                else:
                    record.kg = 0
            if record.name.code == 'GD':
                percent = record.percent
                rule = self.env['moisture.configuration'].search([
                    ('product_category_id', '=', record.request_kcs_line_id.categ_id.id),
                    ('state', '=', 'approve'),
                    ('crop_id', '=', record.request_kcs_line_id.picking_id.crop_id.id)
                ])
                if rule:
                    if percent > rule.standard_ab_percent:
                        record.kg = 0
                    if 0 < percent <= rule.standard_ab_percent:
                        diff = rule.standard_ab_percent - percent
                        deduction_percent = rule.deduction_percent_ab * diff
                        record.kg = (deduction_percent/100) * record.request_kcs_line_id.product_qty
                else:
                    record.kg = 0
            if record.name.code == 'HUSK':
                percent = record.percent
                rule = self.env['moisture.configuration'].search([
                    ('product_category_id', '=', record.request_kcs_line_id.categ_id.id),
                    ('state', '=', 'approve'),
                    ('crop_id', '=', record.request_kcs_line_id.picking_id.crop_id.id),
                    ('using_deduction_fm', '=', True)
                ])
                if not rule:
                    record.kg = 0
                else:
                    diff_from_rule = percent - rule.standard_for_fm
                    if diff_from_rule < 0:
                        record.kg = 0
                    else:
                        record.kg = (diff_from_rule/100) * record.request_kcs_line_id.product_qty

class DeductionQuality(models.Model):
    _name = 'deduction.quality'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')