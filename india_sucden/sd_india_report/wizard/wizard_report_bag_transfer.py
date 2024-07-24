# -*- coding: utf-8 -*-
from odoo import api
from odoo import SUPERUSER_ID
from odoo import tools
from odoo import fields, models
from odoo.tools.translate import _
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date
import time
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
from docutils.nodes import document
import calendar
import datetime
from time import gmtime, strftime

DATE_FORMAT = "%Y-%m-%d"


class WizardReportBagTransfer(models.TransientModel):
    _name = 'wizard.report.bag.transfer'
    _description = 'Report Bag Transfer'

    partner_id = fields.Many2many('res.partner', string='Supplier', domain=[('supplier_rank', '>', 0)])
    product_id = fields.Many2many('product.product', string='Product', domain="[('template_qc', '=', 'bag')]")

    def generate_report(self):
        self.env.cr.execute('''DELETE FROM report_bag_transfer;''')
        if self.partner_id and self.product_id:
            for par in self.partner_id:
                picking_par = self.env['stock.picking'].search([
                    ('template_qc', '=', 'bag'),
                    ('state', '=', 'done'),
                    ('partner_id', '=', par.id),
                    ('picking_type_id.code', 'in', ['material_in', 'material_out'])
                ])
                if picking_par:
                    for pro in self.product_id:
                        picking_pro = self.env['stock.picking'].search([
                            ('template_qc', '=', 'bag'),
                            ('state', '=', 'done'),
                            ('product_id', '=', pro.id),
                            ('picking_type_id.code', 'in', ['material_in', 'material_out'])
                        ])
                        if picking_pro:
                            min = self.env['stock.picking'].search([
                                ('template_qc', '=', 'bag'),
                                ('state', '=', 'done'),
                                ('partner_id', '=', par.id),
                                ('product_id', '=', pro.id),
                                ('picking_type_id.code', '=', 'material_in')
                            ])
                            mrn = self.env['stock.picking'].search([
                                ('template_qc', '=', 'bag'),
                                ('state', '=', 'done'),
                                ('partner_id', '=', par.id),
                                ('product_id', '=', pro.id),
                                ('picking_type_id.code', '=', 'material_out')
                            ])
                            sum_min = sum(min.mapped('total_init_qty'))
                            sum_mrn = sum(mrn.mapped('total_init_qty'))
                            vals = {
                                'partner_id': par.id,
                                'product_id': pro.id,
                                'bag_in': sum_min,
                                'bag_out': sum_mrn,
                            }
                            self.env['report.bag.transfer'].create(vals)
        if (self.partner_id and not self.product_id) or (not self.partner_id and self.product_id):
            if self.partner_id:
                product = self.env['product.product'].search([
                    ('template_qc', '=', 'bag')
                ])
                for par in self.partner_id:
                    picking_par = self.env['stock.picking'].search([
                        ('template_qc', '=', 'bag'),
                        ('state', '=', 'done'),
                        ('partner_id', '=', par.id),
                        ('picking_type_id.code', 'in', ['material_in', 'material_out'])
                    ])
                    if picking_par:
                        for pro in product:
                            picking_pro = self.env['stock.picking'].search([
                                ('template_qc', '=', 'bag'),
                                ('state', '=', 'done'),
                                ('product_id', '=', pro.id),
                                ('picking_type_id.code', 'in', ['material_in', 'material_out'])
                            ])
                            if picking_pro:
                                min = self.env['stock.picking'].search([
                                    ('template_qc', '=', 'bag'),
                                    ('state', '=', 'done'),
                                    ('partner_id', '=', par.id),
                                    ('product_id', '=', pro.id),
                                    ('picking_type_id.code', '=', 'material_in')
                                ])
                                mrn = self.env['stock.picking'].search([
                                    ('template_qc', '=', 'bag'),
                                    ('state', '=', 'done'),
                                    ('partner_id', '=', par.id),
                                    ('product_id', '=', pro.id),
                                    ('picking_type_id.code', '=', 'material_out')
                                ])
                                sum_min = sum(min.mapped('total_init_qty'))
                                sum_mrn = sum(mrn.mapped('total_init_qty'))
                                vals = {
                                    'partner_id': par.id,
                                    'product_id': pro.id,
                                    'bag_in': sum_min,
                                    'bag_out': sum_mrn,
                                }
                                self.env['report.bag.transfer'].create(vals)
            if self.product_id:
                partner = self.env['res.partner'].search([
                    ('supplier_rank', '>', 0)
                ])
                for par in partner:
                    picking_par = self.env['stock.picking'].search([
                        ('template_qc', '=', 'bag'),
                        ('state', '=', 'done'),
                        ('partner_id', '=', par.id),
                        ('picking_type_id.code', 'in', ['material_in', 'material_out'])
                    ])
                    if picking_par:
                        for pro in self.product_id:
                            picking_pro = self.env['stock.picking'].search([
                                ('template_qc', '=', 'bag'),
                                ('state', '=', 'done'),
                                ('product_id', '=', pro.id),
                                ('picking_type_id.code', 'in', ['material_in', 'material_out'])
                            ])
                            if picking_pro:
                                min = self.env['stock.picking'].search([
                                    ('template_qc', '=', 'bag'),
                                    ('state', '=', 'done'),
                                    ('partner_id', '=', par.id),
                                    ('product_id', '=', pro.id),
                                    ('picking_type_id.code', '=', 'material_in')
                                ])
                                mrn = self.env['stock.picking'].search([
                                    ('template_qc', '=', 'bag'),
                                    ('state', '=', 'done'),
                                    ('partner_id', '=', par.id),
                                    ('product_id', '=', pro.id),
                                    ('picking_type_id.code', '=', 'material_out')
                                ])
                                sum_min = sum(min.mapped('total_init_qty'))
                                sum_mrn = sum(mrn.mapped('total_init_qty'))
                                vals = {
                                    'partner_id': par.id,
                                    'product_id': pro.id,
                                    'bag_in': sum_min,
                                    'bag_out': sum_mrn,
                                }
                                self.env['report.bag.transfer'].create(vals)

        if not self.partner_id and not self.product_id:
            product = self.env['product.product'].search([
                ('template_qc', '=', 'bag')
            ])
            partner = self.env['res.partner'].search([
                ('supplier_rank', '>', 0)
            ])
            for par in partner:
                picking_par = self.env['stock.picking'].search([
                        ('template_qc', '=', 'bag'),
                        ('state', '=', 'done'),
                        ('partner_id', '=', par.id),
                        ('picking_type_id.code', 'in', ['material_in', 'material_out'])
                    ])
                if picking_par:
                    for pro in product:
                        picking_pro = self.env['stock.picking'].search([
                            ('template_qc', '=', 'bag'),
                            ('state', '=', 'done'),
                            ('product_id', '=', pro.id),
                            ('picking_type_id.code', 'in', ['material_in', 'material_out'])
                        ])
                        if picking_pro:
                            min = self.env['stock.picking'].search([
                                ('template_qc', '=', 'bag'),
                                ('state', '=', 'done'),
                                ('partner_id', '=', par.id),
                                ('product_id', '=', pro.id),
                                ('picking_type_id.code', '=', 'material_in')
                            ])
                            mrn = self.env['stock.picking'].search([
                                ('template_qc', '=', 'bag'),
                                ('state', '=', 'done'),
                                ('partner_id', '=', par.id),
                                ('product_id', '=', pro.id),
                                ('picking_type_id.code', '=', 'material_out')
                            ])
                            sum_min = sum(min.mapped('total_init_qty'))
                            sum_mrn = sum(mrn.mapped('total_init_qty'))
                            vals = {
                                'partner_id': par.id,
                                'product_id': pro.id,
                                'bag_in': sum_min,
                                'bag_out': sum_mrn,
                            }
                            self.env['report.bag.transfer'].create(vals)

        return {
            'name': _('Report Bag Transfer'),
            'view_type': 'tree',
            'view_mode': 'tree',
            'views': [(self.env.ref('sd_india_report.report_bag_transfer_view_tree').id, 'tree')],
            'res_model': 'report.bag.transfer',
            'context': {},
            'domain': [],
            'type': 'ir.actions.act_window',
        }
