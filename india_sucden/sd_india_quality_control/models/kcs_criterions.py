# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class KCSCriterions(models.Model):
    _inherit = "kcs.criterions"

    moisture_india_ids = fields.One2many('moisture.india', 'kcs_criterion_id', string='Degree')
    grade_percent_india_ids = fields.One2many('grade.percent.india', 'kcs_criterion_id', string='Grade Percent')
    defectives_india_ids = fields.One2many('defective.india', 'kcs_criterion_id', string='Defectives')
    outturn_india_ids = fields.One2many('outturn.india', 'kcs_criterion_id', string='Outturn')
    foreign_matter_india_ids = fields.One2many('foreign.matter.india', 'kcs_criterion_id', string='Foreign Matters')
    other_india_ids = fields.One2many('other.india', 'kcs_criterion_id', string='Other Deduction')

    categ_id = fields.Many2one("product.category", string="Category", readonly=True,
                               states={'draft': [('readonly', False)]}, domain=False)


class MoistureIndia(models.Model):
    _name = 'moisture.india'

    kcs_criterion_id = fields.Many2one('kcs.criterions')
    range_start = fields.Float(string='From')
    range_end = fields.Float(string='To')
    percent = fields.Float(string='Percent %')


class GradePercentIndia(models.Model):
    _name = 'grade.percent.india'

    kcs_criterion_id = fields.Many2one('kcs.criterions')
    range_start = fields.Float(string='From')
    range_end = fields.Float(string='To')
    percent = fields.Float(string='Percent %')


class DefectiveIndia(models.Model):
    _name = 'defective.india'

    kcs_criterion_id = fields.Many2one('kcs.criterions')
    range_start = fields.Float(string='From')
    range_end = fields.Float(string='To')
    percent = fields.Float(string='Percent %')


class OutturnIndia(models.Model):
    _name = 'outturn.india'

    kcs_criterion_id = fields.Many2one('kcs.criterions')
    range_start = fields.Float(string='From')
    range_end = fields.Float(string='To')
    percent = fields.Float(string='Percent %')


class ForeignMatterIndia(models.Model):
    _name = 'foreign.matter.india'

    kcs_criterion_id = fields.Many2one('kcs.criterions')
    range_start = fields.Float(string='From')
    range_end = fields.Float(string='To')
    percent = fields.Float(string='Percent %')


class OtherDeduction(models.Model):
    _name = 'other.india'

    kcs_criterion_id = fields.Many2one('kcs.criterions')
    range_start = fields.Float(string='From')
    range_end = fields.Float(string='To')
    percent = fields.Float(string='Percent %')
