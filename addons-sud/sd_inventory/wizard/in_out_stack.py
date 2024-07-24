
# -*- coding: utf-8 -*-

import time
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class wizradInOutStack(models.TransientModel):
    _name = "wizard.in.out.stack"
    
    def _default_warehouse(self):
        warehouse_ids = self.env['stock.warehouse'].with_context(user_workers=True).search(
            [('company_id', '=', self.env.user.company_id.id)])
        # default with user only working 1 company account analytic
        if warehouse_ids:
            return warehouse_ids[0]
    
    @api.model
    def _domain_warehouse(self):
        return "[('id', 'in', %s)]" % self.env.user._warehouses_domain()
        
    warehouse_id = fields.Many2one('stock.warehouse' ,string="Warehouse", default=_default_warehouse, domain=lambda self: self._domain_warehouse())
    
    
    stack_id = fields.Many2one('stock.lot' ,string="Stack")
    date  = fields.Date(string="Date")
    zone_id = fields.Many2one('stock.zone' ,string="Zone")
    qty_stack = fields.Float(string="Stack")
    bag = fields.Float(string="Bag")
    packing_id = fields.Many2one('ned.packing' ,string="Packing")
    
    stack_ids = fields.Many2many('stock.lot', string='Stack' ,)
#     detail_stack = fields.M
    
    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        res.update({'date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT) or False,
                   'stack_ids' :[[6, False, active_ids]]})
        return res
    
    def check_data(self):
        product_id = False
        warehouse_id = False
        for i in self.stack_ids:
            if not product_id:
                product_id = i.product_id.id
            if product_id != i.product_id.id:
                raise ValidationError(_('Merge Stack need to be the same product %s', i.product_id.code))
            
            if not warehouse_id:
                warehouse_id = i.warehouse_id.id
            if warehouse_id != i.warehouse_id.id:
                raise ValidationError(_('Merge Stack need to be the same Warehouse %s', i.warehouse_id.code))
            
    
    def merg_stack(self):
        stack_id = False
        this = self
        company = self.env.user.company_id.id or False
        warehouse_id = self.warehouse_id
        picking_type_id = self.env['stock.picking.type'].search([('name', '=', 'DF')], limit=1)
        init_qty = product_qty = 0
        stick_count = stone_count = mc = immature = eaten = burn = screen12 = screen13 = screen16 = screen18 = screen19 = screen20 = excelsa = 0
        greatersc12 = 0
        belowsc12 = 0
        screen17 =0
        screen15 = 0
        screen14 = 0
        cherry = mold = fm = black = brown = broken = 0.0
        packing_id = False
        bag = 0
        count = 0
        remarks_note = ''
        product_id = False
        this.check_data()
        history_stack = []

        for line in self.stack_ids:
            product_id = line.product_id

            stack_id = line
            init_qty += line.init_qty
            product_qty += line.remaining_qty
            mc += line.mc * line.init_qty or 0.0
            fm += line.fm * line.init_qty or 0.0
            black += line.black * line.init_qty or 0.0
            broken += line.broken * line.init_qty or 0.0
            brown += line.brown * line.init_qty or 0.0
            mold += line.mold * line.init_qty or 0.0
            cherry += line.cherry * line.init_qty or 0.0
            excelsa += line.excelsa * line.init_qty or 0.0

            screen20 += line.screen20 * line.init_qty or 0.0
            screen19 += line.screen19 * line.init_qty or 0.0
            screen18 += line.screen18 * line.init_qty or 0.0
            screen17 += line.screen17 * line.init_qty or 0.0
            screen16 += line.screen16 * line.init_qty or 0.0
            screen15 += line.screen15 * line.init_qty or 0.0
            screen14 += line.screen14 * line.init_qty or 0.0
            screen13 += line.screen13 * line.init_qty or 0.0
            greatersc12 += line.greatersc12 * line.init_qty or 0.0
            # belowsc12 += line.belowsc12 * line.init_qty or 0.0

            screen12 += line.screen12 * line.init_qty or 0.0
            burn += line.burn * line.init_qty or 0.0
            eaten += line.eaten * line.init_qty or 0.0
            immature += line.immature * line.init_qty or 0.0
            stick_count = line.stick_count
            stone_count = line.stone_count
            maize_yn = line.maize
            count += line.init_qty

            bag += line.bag_qty or 0.0
            if not packing_id:
                packing_id = line.packing_id and line.packing_id.id or False

            remarks_note += line.name + ', '
            history_stack.append(stack_id)

            var = {
                'name': '/',
                'picking_type_id': picking_type_id.id,
                'scheduled_date': this.date,
                'date_done': this.date,
                'partner_id': False,
                'picking_type_code': picking_type_id.code or False,
                'location_id': picking_type_id.default_location_src_id.id or False,
                'location_dest_id': picking_type_id.default_location_dest_id.id or False,
                'state': 'draft',
                'date_kcs': this.date,
                'merge': True
            }

            new_id = self.env['stock.picking'].create(var)
            name = line.name

            move_id = self.env['stock.move.line'].create({'picking_id': new_id.id or False,
                                                          # 'name': name,
                                                          'product_uom_id': line.product_id.uom_id.id or False,
                                                          # 'product_uom_qty': line.remaining_qty or 0.0,
                                                          'init_qty': line.init_qty or 0.0,
                                                          'weighbridge': line.init_qty or 0.0,
                                                          'qty_done': line.init_qty or 0.0,
                                                          'price_unit': 0.0,
                                                          'picking_type_id': picking_type_id.id or False,
                                                          'location_id': picking_type_id.default_location_src_id.id or False,
                                                          # 'date_expected': this.date or False, 'partner_id': False,
                                                          'location_dest_id': picking_type_id.default_location_dest_id.id or False,
                                                          # 'type': picking_type_id.code or False, 'scrapped': False,
                                                          'company_id': company,
                                                          'zone_id': line.zone_id.id or False,
                                                          'product_id': line.product_id.id or False,
                                                          'date': self.date or False, 'currency_id': False,
                                                          'state': 'done',
                                                          'warehouse_id': warehouse_id.id or False,
                                                          'lot_id': line.id,
                                                          # 'state_kcs': 'approved',
                                                          'packing_id': line.packing_id.id,
                                                          'bag_no': line.bag_qty
                                                          })

            new_id.button_validate()

        var_picking = {
            'name': '/',
            'picking_type_id': picking_type_id.id,
            'scheduled_date': this.date,
            'date_done': this.date,
            'partner_id': False,
            'picking_type_code': picking_type_id.code or False,
            'location_dest_id': picking_type_id.default_location_src_id.id or False,
            'location_id': picking_type_id.default_location_dest_id.id or False,
            'state': 'draft',
            'state_kcs': 'approved',
        }

        new_id = self.env['stock.picking'].create(var_picking)

        var_lot = {
            'zone_id': this.zone_id.id,
            'date': this.date,
            'name': '/',
            'remarks_note': remarks_note,
            'product_id': product_id.id,
            'warehouse_id': this.warehouse_id.id,
            'merge': True
        }
        new_stack = self.env['stock.lot'].create(var_lot)
        for i in history_stack:
            i.parent_id = new_stack.id

        move_id = self.env['stock.move.line'].create({'picking_id': new_id.id or False,
                                                      # 'name': name,
                                                      'product_uom_id': stack_id.product_id.uom_id.id or False,
                                                      # 'product_uom_qty': product_qty or 0.0,
                                                      'init_qty': product_qty or 0.0,
                                                      'weighbridge': product_qty or 0.0,
                                                      'qty_done': product_qty or 0.0,

                                                      'price_unit': 0.0,
                                                      'picking_type_id': picking_type_id.id or False,
                                                      'location_dest_id': picking_type_id.default_location_src_id.id or False,
                                                      # 'date_expected': this.date or False, 'partner_id': False,
                                                      'location_id': picking_type_id.default_location_dest_id.id or False,
                                                      # 'type': picking_type_id.code or False, 'scrapped': False,
                                                      'company_id': company,
                                                      'zone_id': this.zone_id.id or False,
                                                      'product_id': stack_id.product_id.id or False,
                                                      'date': self.date or False, 'currency_id': False,
                                                      'warehouse_id': warehouse_id.id or False,
                                                      'lot_id': new_stack.id,
                                                      'packing_id': packing_id or False,
                                                      'bag_no': bag
                                                      })

        var_kcs = {
            'picking_id': new_id.id,
            'name': name or False,
            'product_id': stack_id.product_id.id or False,
            'categ_id': stack_id.product_id.product_tmpl_id.categ_id.id,
            'product_qty': init_qty or 0.0,
            'qty_reached': init_qty or 0.0,
            'criterions_id': False,
            'product_uom': stack_id.product_id.uom_id.id or False,
            'move_id': move_id.id or False,
            'state': 'draft',
        }

        request = self.env['request.kcs.line'].create(var_kcs)
        new_id.button_validate()
        mc_avf = mc / count
        request.write({
            'sample_weight': 100,
            'bb_sample_weight': 100,
            'mc_degree': mc_avf / (1 - (0.01 * mc_avf)),
            'fm_gram': fm / count,
            'black_gram': black / count,
            'broken_gram': broken / count,
            'brown_gram': brown / count,
            'mold_gram': mold / count,
            'cherry_gram': cherry / count,
            'excelsa_gram': excelsa / count,
            'screen20_gram': screen20 / count,
            'screen19_gram': screen19 / count,
            'screen18_gram': screen18 / count,
            'screen17_gram': screen17 / count,
            'screen16_gram': screen16 / count,
            'screen15_gram': screen15 / count,
            'screen14_gram': screen14 / count,
            'screen13_gram': screen13 / count,
            # 'screen12':screen12/count,
            'greatersc12_gram': greatersc12 / count,
            'belowsc12_gram': belowsc12 / count,
            'burned_gram': burn / count,
            'eaten_gram': eaten / count,
            'immature_gram': immature / count,
            'stone_count': stone_count,
            'stick_count': stick_count
        })
        request._percent_mc()
        request._percent_fm()
        request._percent_black()
        request._percent_broken()
        request._percent_brown()
        request._percent_mold()
        request._percent_cherry()
        request._percent_excelsa()
        request._percent_screen20()
        request._percent_screen19()
        request._percent_screen18()
        request._percent_screen17()
        request._percent_screen16()
        request._percent_screen15()
        request._percent_screen14()
        request._percent_screen13()
        request._greatersc12_gram()
        request._percent_greatersc12()
        request._percent_belowsc12()
        request._screen12_deduct()
        request._percent_burned()
        request._percent_eaten()
        request._percent_immature()
        new_id.btt_approved()
        new_stack._compute_qc()
        

    def stack(self):
        stack_id = False
        remarks_note = 'Split Stack \n'
        product_id = False
        for line in self.stack_ids:
            stack_id = line
            remarks_note += line.name
            product_id = line.product_id
        for this in self:
            # if this.product_qty > this.qty_stack -this.basis_qty:
            #     raise UserError(u'Request Qty is over')

            company = self.env.user.company_id.id or False
            warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
            picking_type_id = self.env['stock.picking.type'].search([('name', '=', 'DF')], limit=1)

            var = {
                'name': '/',
                'picking_type_id': picking_type_id.id,
                'scheduled_date': this.date,
                'date_done': this.date,
                'partner_id': False,
                'picking_type_code': picking_type_id.code or False,
                'location_id': picking_type_id.default_location_src_id.id or False,
                'location_dest_id': picking_type_id.default_location_dest_id.id or False,
                'state': 'draft',
                'date_kcs': this.date,
            }

            new_id = self.env['stock.picking'].create(var)
            product_uom_qty = this.qty_stack

            name = stack_id.name
            move_id = self.env['stock.move.line'].create({'picking_id': new_id.id or False,
                                                          'product_uom_id': stack_id.product_id.uom_id.id or False,
                                                          'init_qty': product_uom_qty or 0.0,
                                                          'weighbridge': product_uom_qty or 0.0,
                                                          'qty_done': product_uom_qty or 0.0,

                                                          'price_unit': 0.0,
                                                          'picking_type_id': picking_type_id.id or False,
                                                          'location_id': picking_type_id.default_location_src_id.id or False,
                                                          # 'date': this.date or False, 'partner_id': False,
                                                          'location_dest_id': picking_type_id.default_location_dest_id.id or False,
                                                          'company_id': company,
                                                          'zone_id': this.zone_id.id or False,
                                                          'product_id': stack_id.product_id.id or False,
                                                          'date': self.date or False, 'currency_id': False,
                                                          'state': 'done',
                                                          'warehouse_id': warehouse_id.id or False,
                                                          'lot_id': stack_id.id,
                                                          'packing_id': this.packing_id.id,
                                                          'bag_no': this.bag
                                                          })

            var = {'picking_id': new_id.id,
                   'name': name or False,
                   'product_id': stack_id.product_id.id or False,
                   'categ_id': stack_id.product_id.product_tmpl_id.categ_id.id,
                   'product_qty': product_uom_qty or 0.0,
                   'qty_reached': product_uom_qty or 0.0,
                   'criterions_id': False,
                   'product_uom': stack_id.product_id.uom_id.id or False,
                   'move_id': move_id.id or False,
                   'state': 'draft',
                   'date': this.date

                   }
            request = self.env['request.kcs.line'].create(var)
            new_id.button_validate()
            request.write({
                'sample_weight': 100,
                'bb_sample_weight': 100,
                'mc_degree': stack_id.mc / (1 - (0.01 * stack_id.mc)),
                'fm_gram': stack_id.fm,
                'black_gram': stack_id.black,
                'broken_gram': stack_id.broken,
                'brown_gram': stack_id.brown,
                'mold_gram': stack_id.mold,
                'cherry_gram': stack_id.cherry,
                'excelsa_gram': stack_id.excelsa,
                'screen20_gram': stack_id.screen20,
                'screen19_gram': stack_id.screen19,
                'screen18_gram': stack_id.screen18,
                'screen17_gram': stack_id.screen17,
                'screen16_gram': stack_id.screen16,
                'screen15_gram': stack_id.screen15,
                'screen14_gram': stack_id.screen14,
                'screen13_gram': stack_id.screen13,
                'greatersc12_gram': stack_id.greatersc12,
                'belowsc12_gram': stack_id.screen12,
                # 'screen12_gram': stack_id.screen12,
                'burned_gram': stack_id.burn,
                'eaten_gram': stack_id.eaten,
                'immature_gram': stack_id.immature,
                'stone_count': stack_id.stone_count,
                'stick_count': stack_id.stick_count,
                'maize_yn': stack_id.maize,
            })
            request._percent_mc()
            request._percent_fm()
            request._percent_black()
            request._percent_broken()
            request._percent_brown()
            request._percent_mold()
            request._percent_cherry()
            request._percent_excelsa()
            request._percent_screen20()
            request._percent_screen19()
            request._percent_screen18()
            request._percent_screen17()
            request._percent_screen16()
            request._percent_screen15()
            request._percent_screen14()
            request._percent_screen13()
            request._greatersc12_gram()
            request._percent_greatersc12()
            request._percent_belowsc12()
            request._screen12_deduct()
            request._percent_burned()
            request._percent_eaten()
            request._percent_immature()
            new_id.btt_approved()

            var = {
                'name': '/',
                'picking_type_id': picking_type_id.id,
                'scheduled_date': this.date,
                'date_done': this.date,
                'partner_id': False,
                'picking_type_code': picking_type_id.code or False,
                'location_dest_id': picking_type_id.default_location_src_id.id or False,
                'location_id': picking_type_id.default_location_dest_id.id or False,
                'state': 'draft',
                'state_kcs': 'approved',
                'date_kcs': this.date,
            }

            new_id = self.env['stock.picking'].create(var)
            var = {
                'zone_id': this.zone_id.id,
                'date': this.date,
                'name': '/',
                'remarks_note': remarks_note,
                'product_id': product_id.id,
                'warehouse_id': this.zone_id.warehouse_id.id
            }
            new_stack = self.env['stock.lot'].create(var)

            move_id = self.env['stock.move.line'].create({'picking_id': new_id.id or False,
                                                          # 'name': name,
                                                          'product_uom_id': stack_id.product_id.uom_id.id or False,
                                                          # 'product_uom_qty': product_uom_qty or 0.0,
                                                          'init_qty': product_uom_qty or 0.0,
                                                          'weighbridge': product_uom_qty or 0.0,
                                                          'qty_done': product_uom_qty or 0.0,

                                                          'price_unit': 0.0,
                                                          'picking_type_id': picking_type_id.id or False,
                                                          'location_dest_id': picking_type_id.default_location_src_id.id or False,
                                                          # 'date_expected': this.date or False, 'partner_id': False,
                                                          'location_id': picking_type_id.default_location_dest_id.id or False,
                                                          # 'type': picking_type_id.code or False, 'scrapped': False,
                                                          'company_id': company,
                                                          'zone_id': this.zone_id.id or False,
                                                          'product_id': stack_id.product_id.id or False,
                                                          'date': self.date or False, 'currency_id': False,
                                                          'warehouse_id': warehouse_id.id or False,
                                                          'lot_id': new_stack.id,
                                                          'packing_id': this.packing_id.id,
                                                          'bag_no': this.bag
                                                          })

            var = {'picking_id': new_id.id,
                   'name': name or False,
                   'product_id': stack_id.product_id.id or False,
                   'categ_id': stack_id.product_id.product_tmpl_id.categ_id.id,
                   'product_qty': product_uom_qty or 0.0,
                   'qty_reached': product_uom_qty or 0.0,
                   'criterions_id': False,
                   'product_uom': stack_id.product_id.uom_id.id or False,
                   'move_id': move_id.id or False,
                   'state': 'draft',
                   }

            request = self.env['request.kcs.line'].create(var)
            new_id.button_validate()

            request.write({
                'sample_weight': 100,
                'bb_sample_weight': 100,
                'mc_degree': stack_id.mc / (1 - (0.01 * stack_id.mc)),
                'fm_gram': stack_id.fm,
                'black_gram': stack_id.black,
                'broken_gram': stack_id.broken,
                'brown_gram': stack_id.brown,
                'mold_gram': stack_id.mold,
                'cherry_gram': stack_id.cherry,
                'excelsa_gram': stack_id.excelsa,
                'screen20_gram': stack_id.screen20,
                'screen19_gram': stack_id.screen19,
                'screen18_gram': stack_id.screen18,
                'screen17_gram': stack_id.screen17,
                'screen16_gram': stack_id.screen16,
                'screen15_gram': stack_id.screen15,
                'screen14_gram': stack_id.screen14,
                'screen13_gram': stack_id.screen13,
                'greatersc12_gram': stack_id.greatersc12,
                # 'screen12_gram': stack_id.screen12,
                'belowsc12_gram': stack_id.screen12,
                'burned_gram': stack_id.burn,
                'eaten_gram': stack_id.eaten,
                'immature_gram': stack_id.immature,
                'stone_count': stack_id.stone_count,
                'stick_count': stack_id.stick_count,
                'maize_yn': stack_id.maize,
            })
            request._percent_mc()
            request._percent_fm()
            request._percent_black()
            request._percent_broken()
            request._percent_brown()
            request._percent_mold()
            request._percent_cherry()
            request._percent_excelsa()
            request._percent_screen20()
            request._percent_screen19()
            request._percent_screen18()
            request._percent_screen17()
            request._percent_screen16()
            request._percent_screen15()
            request._percent_screen14()
            request._percent_screen13()
            request._greatersc12_gram()
            request._percent_greatersc12()
            request._percent_belowsc12()
            request._screen12_deduct()
            request._percent_burned()
            request._percent_eaten()
            request._percent_immature()
            new_id.btt_approved()
            new_stack._compute_qc()
