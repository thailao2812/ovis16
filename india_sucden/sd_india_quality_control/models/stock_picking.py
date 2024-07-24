# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from datetime import datetime, date, timedelta
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
import time
from odoo.exceptions import ValidationError, UserError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    reject_in_qc = fields.Text(string='Reason reject')
    state_kcs = fields.Selection(
        selection=[('draft', 'New'), ('commercial', 'Commercial'), ('approved', 'Approved'), ('waiting', 'Waiting Another Operation'),
                   ('rejected', 'Rejected'), ('cancel', 'Cancel')], string='KCS Status', readonly=True, copy=False,
        index=True, default='draft', tracking=True, )
    deduction_qty = fields.Float(string='Deduction Qty', related='kcs_line.qty_reached', store=True)

    def button_assign_commercial(self):
        for pick in self:
            for line in pick.kcs_line[0].deduction_ids:
                if line.reject:
                    raise UserError(_("You cannot Approve because we have reject quality here %s!") % line.name)
                if pick.picking_type_id.code in ['incoming', 'production_out', 'production_in', 'transfer_in']:
                    if line.name.code == 'MD' and line.percent == 0:
                        raise UserError(_("You need to input Moisture %"))
            if not pick.kcs_line:
                raise UserError(_('You cannot approve a Request KCS without any Request KCS Line.'))

            for line in pick.kcs_line:
                if line.sample_weight_india == 0:
                    raise UserError(_('You input sample weigh or sample weight before Approved '))

            if pick.kcs_criterions_id.reject_rule:
                for line in pick.kcs_line:
                    if (line.reject_mc or line.reject_foreign or line.reject_bb or line.reject_brown or line.reject_mold or line.reject_excelsa or line.reject_burned or line.reject_insect_bean):
                        raise UserError(_('Check Reject'))
            pick.state_kcs = 'commercial'
            for line in pick.kcs_line:
                line.state = 'commercial'
            if pick.picking_type_id.code in ['production_in', 'production_out']:
                pick.btt_approved()

    def btt_loads(self):
        for pick in self:
            if not pick.date_kcs:
                pick.date_kcs = datetime.now()
            if pick.picking_type_id.kcs != True:
                raise UserError(_('This transaction no need QC Analysis'))
                continue
            for move in pick.move_line_ids_without_package:
                self.env.cr.execute('''DELETE FROM request_kcs_line WHERE picking_id = %(picking_id)s;''' % ({'picking_id': pick.id}))

                var = {'picking_id': pick.id,
                       'name': move.picking_id.name or False,
                       'product_id': move.product_id.id or False,
                       'categ_id': move.product_id.product_tmpl_id.categ_id.id,
                       'product_qty': sum([x.init_qty for x in pick.move_line_ids_without_package]) or 0.0,
                       'qty_reached': sum([x.init_qty for x in pick.move_line_ids_without_package]) or 0.0,
                       # 'criterions_id': False,
                       'product_uom': move.product_uom_id.id or False,
                       'move_id': move.id or False,
                       'packing_id': move.packing_id and move.packing_id.id or False,
                       'bag_no': move.bag_no or 0.0,
                       'state': 'draft'}
                self.env['request.kcs.line'].create(var)

                self.env.cr.execute(''' update request_kcs_line set x_warehouse_id = 
                                            (SELECT warehouse_id 
                                            FROM stock_picking where request_kcs_line.picking_id = stock_picking.id)
                                            WHERE request_kcs_line.x_warehouse_id is NULL; ''')

            # if pick.picking_type_id.code == 'production_out':
            #     pick.kcs_line.refresh()
            #     pick.load_qc_gip()
            deduction = self.env['deduction.quality'].search([
                ('code', 'not in', ['OTH', 'BB', 'Bleach', 'IDB', 'RB', '4_kinds_deduction', 'WB']),
            ]).sorted(key=lambda i: i.id)
            deduction_special = self.env['deduction.quality'].search([
                ('id', 'not in', deduction.ids),
                ('code', 'not in', ['OTH', 'BB', 'Bleach', 'IDB', 'RB'])
            ]).sorted(key=lambda i: i.id)
            pick.kcs_line.deduction_ids = [(5, 0, 0)]
            pick.kcs_line.deduction_special_ids = [(5, 0, 0)]
            for i in deduction:
                self.env['deduction.line'].create({
                    'request_kcs_line_id': pick.kcs_line.id,
                    'name': i.id
                })
            for i in deduction_special:
                self.env['deduction.line'].create({
                    'request_kcs_line_id_2nd': pick.kcs_line.id,
                    'name': i.id
                })
            if pick.picking_type_id.code == 'production_out':
                pick.kcs_line.refresh()
                pick.load_qc_gip()

    def btt_approved(self):
        for pick in self:
            for line in pick.kcs_line[0].deduction_ids:
                if line.reject:
                    raise UserError(_("You cannot Approve because we have reject quality here %s!") % line.name)
                if pick.picking_type_id.code in ['incoming', 'production_out', 'production_in', 'transfer_in']:
                    if line.name.code == 'MD' and line.percent == 0:
                        raise UserError(_("You need to input Moisture %"))
        for pick in self:
            if not pick.kcs_line:
                raise UserError(_('You cannot approve a Request KCS without any Request KCS Line.'))

            for line in pick.kcs_line:
                if line.sample_weight_india == 0:
                    raise UserError(_('You input sample weigh or sample weight before Approved '))

            if pick.kcs_criterions_id.reject_rule:
                for line in pick.kcs_line:
                    if (
                            line.reject_mc or line.reject_foreign or line.reject_bb or line.reject_brown or line.reject_mold or line.reject_excelsa or line.reject_burned or line.reject_insect_bean):
                        raise UserError(_('Check Reject'))

        if self.picking_type_id.code == 'production_out':
            self.state_kcs = 'approved'
            for pick in self:
                for line in pick.kcs_line:
                    if line.state != 'commercial':
                        continue
                    line.state = 'approved'
                    if pick.picking_type_id.deduct:
                        line.move_id.write({'qty_done': line.basis_weight or 0.0})
                    else:
                        line.move_id.write({'qty_done': line.product_qty or 0.0})
                        # line.move_id.write({'reserved_uom_qty':line.product_qty or 0.0,'qty_done': line.product_qty or 0.0})
                    # Minh update QC transfer in and transfer out
                    if line.stack_id:
                        for pick_in in line.stack_id.move_line_ids.filtered(
                                lambda x: x.picking_id.picking_type_id.code == 'transfer_in').mapped('picking_id'):
                            pick_in.kcs_line.write({'state': 'draft'})
                            pick_in.kcs_line.unlink()
                            for move_in in pick_in.move_lines:
                                pick.kcs_line.filtered(lambda x: x.product_id == move_in.product_id).copy(
                                    {'picking_id': pick_in.id,
                                     'move_id': move_in.id})
                            if pick_in.backorder_id:
                                pick_in.backorder_id.kcs_line.write({'state': 'draft'})
                                pick_in.backorder_id.kcs_line.unlink()
                                for move_out in pick_in.backorder_id.move_lines:
                                    pick.kcs_line.filtered(lambda x: x.product_id == move_out.product_id).copy(
                                        {'picking_id': pick_in.backorder_id.id,
                                         'move_id': move_out.id})
            #                     line.move_id.write({'product_uom_qty': line.product_qty or 0.0})
            return True

        for pick in self:
            pick.state_kcs = 'approved'
            if all(x.zone_id for x in pick.kcs_line) and pick.picking_type_id.code == 'production_out':
                # SON: thêm sự kiện tìm và gán số STACK WIP tương ứng ZONE cho GRP khi KCS approve
                sql = '''
                    SELECT id FROM stock_stack 
                    WHERE zone_id = %s 
                        and name like '%%%s%%'
                ''' % (self.zone_id.id, 'WIP-')
                self.env.cr.execute(sql)
                for stack_obj in self.env.cr.dictfetchall():
                    stack_line = self.env['stock.lot'].browse(stack_obj['id'])
                    pick.stack_id = stack_line['id'] or 'null'

            for line in pick.kcs_line:
                if line.state != 'commercial':
                    continue
                line.state = 'approved'

                if pick.picking_type_id.deduct:
                    line.move_id.write({'qty_done': line.basis_weight or 0.0})
                    # Đây là nghiệp vụ hàng mua

                #                     pick.create_itr()
                else:
                    line.move_id.write({'qty_done': line.product_qty or 0.0})

                # Err phần sản xuất
                # produced_product = self.env['mrp.operation.result.produced.product'].search([('picking_id','=',pick.id)])
                # if produced_product:
                #     produced_product.kcs_notes = pick.note or 'null'
        self.write({'state_kcs': 'approved', 'approve_id': self.env.uid,
                    'date_kcs': time.strftime(DATETIME_FORMAT)})

        # Đồng thời ghi nhận trọng lượng vào stock.stack
        for linekcs in self.kcs_line:
            for linestack in linekcs.stack_id:
                if linestack:
                    linestack.write({'net_qty': linekcs.product_qty, 'basis_qty': linekcs.basis_weight,
                                     'init_qty': linekcs.product_qty, 'remaining_qty': linekcs.basis_weight,
                                     'bag_qty': self.total_bag})

        # Không dùng GRP tạm Áp dụng 30/04/2023
        # if self.picking_type_code == 'production_in':
        #     name_seq =  self.picking_type_id.sequence_id.with_context(ir_sequence_date=str(self.date_kcs)[0:10]).next_by_id()
        #     if pick.crop_id.short_name:
        #         crop = '-' + pick.crop_id.short_name +'-'
        #         name_seq = name_seq.replace("-", crop, 1)
        #         pick.name = name_seq
        #     else:
        #         pick.name = name_seq

        if self.picking_type_id.kcs_approved:
            operation = self.env['stock.move.line'].search([('picking_id', '=', self.id)])
            for i in self.kcs_line:
                if i.product_id == operation.product_id:
                    operation.write({'reserved_uom_qty': 0, 'qty_done': i.basis_weight})
            self.button_sd_validate()

    def load_qc_gip(self):
        res = super(StockPicking, self).load_qc_gip()
        for this in self:
            if this.kcs_line:
                this.kcs_line.update({
                    'sample_weight_india': 100,
                    'outturn_percent': this.kcs_line.stack_id.outturn_percent,
                    'aaa_percent': this.kcs_line.stack_id.aaa_percent,
                    'aa_percent': this.kcs_line.stack_id.aa_percent,
                    'a_percent': this.kcs_line.stack_id.a_percent,
                    'b_percent': this.kcs_line.stack_id.b_percent,
                    'c_percent': this.kcs_line.stack_id.c_percent,
                    'pb_percent': this.kcs_line.stack_id.pb_percent,
                    'bb_percent': this.kcs_line.stack_id.bb_percent,
                    'bleached_percent': this.kcs_line.stack_id.bleached_percent,
                    'idb_percent': this.kcs_line.stack_id.idb_percent,
                    'bits_percent': this.kcs_line.stack_id.bits_percent,
                    'hulks_percent': this.kcs_line.stack_id.hulks_percent,
                    'stone_percent': this.kcs_line.stack_id.stone_percent,
                    'skin_out_percent': this.kcs_line.stack_id.skin_out_percent,
                    'triage_percent': this.kcs_line.stack_id.triage_percent,
                    'wet_bean_percent': this.kcs_line.stack_id.wet_bean_percent,
                    'red_beans_percent': this.kcs_line.stack_id.red_beans_percent,
                    'stinker_percent': this.kcs_line.stack_id.stinker_percent,
                    'faded_percent': this.kcs_line.stack_id.faded_percent,
                    'flat_percent': this.kcs_line.stack_id.flat_percent,
                    'pb1_percent': this.kcs_line.stack_id.pb1_percent,
                    'pb2_percent': this.kcs_line.stack_id.pb2_percent,
                    'sleeve_6_up_percent': this.kcs_line.stack_id.sleeve_6_up_percent,
                    'sleeve_5_5_up_percent': this.kcs_line.stack_id.sleeve_5_5_up_percent,
                    'sleeve_5_5_down_percent': this.kcs_line.stack_id.sleeve_5_5_down_percent,
                    'sleeve_5_down_percent': this.kcs_line.stack_id.sleeve_5_down_percent,
                    'sleeve_5_up_percent': this.kcs_line.stack_id.sleeve_5_up_percent,
                    'unhulled_percent': this.kcs_line.stack_id.unhulled_percent,
                    'remaining_coffee_percent': this.kcs_line.stack_id.remaining_coffee_percent,
                    'half_monsoon_percent': this.kcs_line.stack_id.half_monsoon_percent,
                    'good_beans_percent': this.kcs_line.stack_id.good_beans_percent,
                    'moisture_percent': this.kcs_line.stack_id.moisture_percent,
                })

            for i in this.kcs_line.deduction_ids:
                if i.name.code == 'MD':
                    i.percent = this.kcs_line.stack_id.moisture_percent
        return res

    @api.model
    def update_gip_moisture(self):
        gip = self.env['stock.picking'].search([('picking_type_id.code', '=', 'production_out')])
        for rec in gip:
            for line in rec.kcs_line:
                for dec in line.deduction_ids:
                    if dec.name.code == 'MD':
                        dec.percent = rec.kcs_line.stack_id.moisture_percent

    def reopen_kcs_qc(self):
        for rec in self:
            check_stock_allocation_approve = self.env['stock.allocation'].search([
                ('picking_id', '=', rec.id),
                ('state', '=', 'approved')
            ])
            check_stock_allocation_draft = self.env['stock.allocation'].search([
                ('picking_id', '=', rec.id),
                ('state', '=', 'draft')
            ])
            if check_stock_allocation_approve:
                raise UserError(_("Please check your Stock Allocation, cancel it first and then Reopen this QC Analysis again!"))
            if check_stock_allocation_draft:
                check_stock_allocation_approve.unlink()
            rec.state_kcs = 'draft'
            for line in rec.kcs_line:
                line.state = 'draft'
