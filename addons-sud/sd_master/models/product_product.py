# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    hide_report = fields.Boolean(string='Hide Report', readonly=False, required=False)
    contract_commodity_vn = fields.Char(string="Commodity (VN)",size=256)
    contract_quality_vn = fields.Char(string="Quality Detail (VN)",size=256)
    contract_commodity_en = fields.Char(string="Commodity (EN)",size=256)
    contract_quality_en = fields.Char(string="Quality Detail (EN)",size=256)
    pass_kcs_for_loss = fields.Boolean(string='Pass KCS', copy= False)

    display_wb = fields.Char(string='Display Weight Bridge', compute='_compute_display_wp', store=True)

    @api.depends('default_code', 'name')
    def _compute_display_wp(self):
        for record in self:
            record.display_wb = ''
            if record.default_code:
                record.display_wb = record.default_code

    @tools.ormcache()
    def _get_default_category_id(self):
        # Deletion forbidden (at least through unlink)
        # categ = self.env.ref('product.product_category_all')
        return False
        # if categ:
        #     return cate_id 
        # else:
        #     return False
    
    
    categ_id = fields.Many2one(
        'product.category', 'Product Category',
        change_default=True, default=_get_default_category_id, group_expand='_read_group_categ_id',
        required=True)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    display_wb = fields.Char(string='Display Weight Bridge', compute='_compute_display_wp', store=True)

    @api.depends('default_code', 'name')
    def _compute_display_wp(self):
        for record in self:
            record.display_wb = ''
            if record.default_code:
                record.display_wb = record.default_code

    def name_get(self):
        result = []
        for pro in self:
            result.append((pro.id, pro.default_code))
        return result