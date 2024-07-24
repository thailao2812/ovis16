# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError


class AnalysisBatchReport(models.Model):
    _name = 'analysis.batch.report'

    name = fields.Char(string='Name', compute='compute_name', store=True)
    crop_id = fields.Many2one('ned.crop', string='Season')
    grade_id = fields.Many2one('product.category', string='Grade')
    percent = fields.Float(string='Outturn %', digits=(12, 2))
    expectation_percent = fields.Float(string='Expected Main Grades', digits=(12, 2))
    state = fields.Selection([
        ('new', 'New'),
        ('approve', 'Approve')
    ], string='State', default='new')

    @api.depends('crop_id', 'grade_id')
    def compute_name(self):
        for rec in self:
            if rec.crop_id and rec.grade_id:
                rec.name = 'Analysis setting for %s in %s' % (rec.grade_id.name, rec.crop_id.name)
            else:
                rec.name = ''

    def approve_analysis(self):
        for rec in self:
            rec.state = 'approve'

    def set_to_draft(self):
        for rec in self:
            rec.state = 'new'

    @api.constrains('state', 'crop_id', 'grade_id')
    def _constrains_current_analysis(self):
        for obj in self:
            check = self.env['analysis.batch.report'].search([
                ('crop_id', '=', obj.crop_id.id),
                ('grade_id', '=', obj.grade_id.id),
                ('state', '=', 'approve'),
                ('id', '!=', obj.id)
            ])
            if check:
                raise UserError(_("You cannot Approve duplicate Category and Season setting for Batch Analysis"))