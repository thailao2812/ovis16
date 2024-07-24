# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ByProductDerivable(models.Model):
    _name = 'by.product.derivable'

    name = fields.Char(string='Option', compute='compute_name', store=True)
    option = fields.Selection([
        ('version_1', 'Version 1'),
        ('version_2', 'Version 2')
    ], string='Version', default='version_1')
    crop_id = fields.Many2one('ned.crop', string='Crop')
    state = fields.Selection([
        ('deactive', 'Deactive'),
        ('active', 'Active')
    ], string='State', default='deactive')
    line_ids = fields.One2many('by.product.line', 'by_product_id',string='Detail')


    def active_by_product(self):
        for record in self:
            record.state = 'active'


    def deactive_by_product(self):
        for record in self:
            record.state = 'deactive'

    @api.depends('option')
    def compute_name(self):
        for record in self:
            if record.option:
                if record.option == 'version_1':
                    record.name = 'Version 1'
                if record.option == 'version_2':
                    record.name = 'Version 2'
            else:
                record.name = 'New'

    @api.constrains('option', 'crop_id')
    def _check_duplicate_option_in_crop(self):
        for record in self:
            if record.option and record.crop_id:
                check = self.search([
                    ('crop_id', '=', record.crop_id.id),
                    ('option', '=', record.option),
                    ('id', '!=', record.id)
                ], limit=1)
                if check:
                    raise UserError(_('You can not choose duplicate Option in Crop!'))


class ByProductLine(models.Model):
    _name = 'by.product.line'

    by_product_id = fields.Many2one('by.product.derivable')
    grade_id = fields.Many2one('product.category', 'Pro. Group')
    product_id = fields.Many2one('product.product', 'Product Code')
    current_stock = fields.Float(string='Currency Stock')
    g2_percent = fields.Integer(string='G2 %')
    quantity_g2 = fields.Float(string='Quantity G2')
    g3_percent = fields.Integer(string='G3 %')
    quantity_g3 = fields.Float(string='Quantity G3')
    description = fields.Char(string='Description')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            stack = self.env['stock.lot'].search([
                ('product_id', '=', self.product_id.id)
            ])
            if stack:
                self.current_stock = sum(stack.mapped('init_qty'))
                self.quantity_g2 = (self.current_stock * self.g2_percent) / 100
                self.quantity_g3 = (self.current_stock * self.g3_percent) / 100

    @api.onchange('current_stock', 'g2_percent', 'g3_percent')
    def onchange_cal_qty(self):
        self.quantity_g2 = (self.current_stock * self.g2_percent) / 100
        self.quantity_g3 = (self.current_stock * self.g3_percent) / 100

