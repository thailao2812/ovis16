# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from datetime import datetime

class NedSecurityGateQueue(models.Model):
    _inherit = "ned.security.gate.queue"

    estate_name = fields.Char(string='Estate Name', related='supplier_id.estate_name', store=True)

    template_qc = fields.Selection(related='product_ids.template_qc', store=True)
    visual_quality_ids = fields.Many2many('visual.quality', string='Visual Quality')

    sample_weight_india = fields.Float(string='Sample Weight', digits=(12, 2))

    outturn_gram = fields.Float(string='Outturn', digits=(12, 2))
    outturn_percent = fields.Float(string='Outturn%', compute='compute_outturn_percent', store=True, digits=(12, 2))

    aaa_gram = fields.Float(string="AAA", digits=(12, 2))
    aaa_percent = fields.Float(string="AAA%", compute='compute_percent_india', store=True, digits=(12, 2))

    aa_gram = fields.Float(string="AA", digits=(12, 2))
    aa_percent = fields.Float(string="AA%", compute='compute_percent_india', store=True, digits=(12, 2))

    a_gram = fields.Float(string="A", digits=(12, 2))
    a_percent = fields.Float(string="A%", compute='compute_percent_india', store=True, digits=(12, 2))

    b_gram = fields.Float(string="B", digits=(12, 2))
    b_percent = fields.Float(string="B%", compute='compute_percent_india', store=True, digits=(12, 2))

    c_gram = fields.Float(string="C", digits=(12, 2))
    c_percent = fields.Float(string="C%", compute='compute_percent_india', store=True, digits=(12, 2))

    pb_gram = fields.Float(string="PB", digits=(12, 2))
    pb_percent = fields.Float(string="PB%", compute='compute_percent_india', store=True, digits=(12, 2))

    bb_gram = fields.Float(string="BB", digits=(12, 2))
    bb_percent = fields.Float(string="BB%", compute='compute_percent_india', store=True, digits=(12, 2))

    bleached_gram = fields.Float(string="Bleached", digits=(12, 2))
    bleached_percent = fields.Float(string="Bleached%", compute='compute_percent_india', store=True, digits=(12, 2))

    idb_gram = fields.Float(string="IDB", digits=(12, 2))
    idb_percent = fields.Float(string="IDB%", compute='compute_percent_india', store=True, digits=(12, 2))

    bits_gram = fields.Float(string="Bits", digits=(12, 2))
    bits_percent = fields.Float(string="Bits%", compute='compute_percent_india', store=True, digits=(12, 2))

    hulks_gram = fields.Float(string="Husk", digits=(12, 2))
    hulks_percent = fields.Float(string="Husk%", compute='compute_percent_india', store=True, digits=(12, 2))

    stone_gram = fields.Float(string="Stone", digits=(12, 2))
    stone_percent = fields.Float(string="Stone%", compute='compute_percent_india', store=True, digits=(12, 2))

    skin_out_gram = fields.Float(string='Skin Out', digits=(12, 2))
    skin_out_percent = fields.Float(string='Skin Out%', compute='compute_percent_india', store=True, digits=(12, 2))

    triage_gram = fields.Float(string='Triage', digits=(12, 2))
    triage_percent = fields.Float(string='Triage%', compute='compute_percent_india', store=True, digits=(12, 2))

    wet_bean_gram = fields.Float(string='Wet Beans', digits=(12, 2))
    wet_bean_percent = fields.Float(string='Wet Beans%', compute='compute_percent_india', store=True, digits=(12, 2))

    red_beans_gram = fields.Float(string='Red Beans', digits=(12, 2))
    red_beans_percent = fields.Float(string='Red Beans%', compute='compute_percent_india', store=True, digits=(12, 2))

    stinker_gram = fields.Float(string='Stinker', digits=(12, 2))
    stinker_percent = fields.Float(string='Stinker%', compute='compute_percent_india', store=True, digits=(12, 2))

    faded_gram = fields.Float(string='Faded', digits=(12, 2))
    faded_percent = fields.Float(string='Faded%', compute='compute_percent_india', store=True, digits=(12, 2))

    flat_gram = fields.Float(string='Flat', digits=(12, 2))
    flat_percent = fields.Float(string='Flat%', compute='compute_percent_india', store=True, digits=(12, 2))

    pb1_gram = fields.Float(string='PB1', digits=(12, 2))
    pb1_percent = fields.Float(string='PB1%', compute='compute_percent_india', store=True, digits=(12, 2))

    pb2_gram = fields.Float(string='PB2', digits=(12, 2))
    pb2_percent = fields.Float(string='PB2%', compute='compute_percent_india', store=True, digits=(12, 2))

    sleeve_6_up = fields.Float(string='6↑', digits=(12, 2))
    sleeve_6_up_percent = fields.Float(string='6↑ %', compute='compute_percent_india', store=True, digits=(12, 2))

    sleeve_5_5_up = fields.Float(string='5.5↑', digits=(12, 2))
    sleeve_5_5_up_percent = fields.Float(string='5.5↑ %', compute='compute_percent_india', store=True, digits=(12, 2))

    sleeve_5_5_down = fields.Float(string='5.5↓', digits=(12, 2))
    sleeve_5_5_down_percent = fields.Float(string='5.5↓%', compute='compute_percent_india', store=True, digits=(12, 2))

    sleeve_5_down = fields.Float(string='5↓', digits=(12, 2))
    sleeve_5_down_percent = fields.Float(string='5↓ %', compute='compute_percent_india', store=True, digits=(12, 2))

    sleeve_5_up = fields.Float(string='5↑', digits=(12, 2))
    sleeve_5_up_percent = fields.Float(string='5↑ %', compute='compute_percent_india', store=True, digits=(12, 2))

    unhulled = fields.Float(string='Unhulled', digits=(12, 2))
    unhulled_percent = fields.Float(string='Unhulled %', compute='compute_percent_india', store=True, digits=(12, 2))

    remaining_coffee = fields.Float(string='Remaining Coffee', digits=(12, 2))
    remaining_coffee_percent = fields.Float(string='Remaining Coffee %', compute='compute_percent_india', store=True, digits=(12, 2))

    blacks = fields.Float(string='Blacks', digits=(12, 2))
    blacks_percent = fields.Float(string='Blacks %', compute='compute_percent_india', store=True, digits=(12, 2))

    half_monsoon = fields.Float(string='Half Monsoon', digits=(12, 2))
    half_monsoon_percent = fields.Float(string='Half Monsoon %', compute='compute_percent_india', store=True, digits=(12, 2))

    good_beans = fields.Float(string='Good Beans', digits=(12, 2))
    good_beans_percent = fields.Float(string='Good Beans %', compute='compute_percent_india', store=True, digits=(12, 2))

    total_gram = fields.Float(string='Total', compute='compute_percent_india', store=True)
    total_percent = fields.Float(string='Total%', compute='compute_total_percent', store=True, digits=(12, 2))

    moisture_percent = fields.Float(string='Moisture%', digits=(12, 2))

    # Deduction O2m
    deduction_ids = fields.One2many('deduction.line', 'security_gate_id', string='Deduction Line')

    state = fields.Selection(
        [("draft", "Draft"), ("pur_approved", "Purchase"), ("qc_approved", "QC"), ('commercial', 'Commercial'),
         ("wh_approved", "WH"), ("approved", "Approved"), ("cancel", "Cancelled"), ("closed", "Closed"),
         ("reject", "Reject")], string="Status",
        readonly=True, copy=False, index=True, default='draft', tracking=True)

    reject_purchase = fields.Text(string='Reject by Purchase')
    reject_qc = fields.Text(string='Reject by QC')
    reject_commercial = fields.Text(string='Reject by Commercial')
    reject_warehouse = fields.Text(string='Reject by Warehouse')

    supplier_id = fields.Many2one('res.partner', string='Supplier', required=True, states={},
                                  domain=[('is_supplier_coffee', '=', True)])

    source_of_goods = fields.Many2one('source.goods', string='Source of goods')

    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", readonly=True, required=True,
                                   states={'draft': [('readonly', False)], 'wh_approved': [('readonly', False)]},
                                   default=False, domain=False)

    quality_slip_no = fields.Char(string='1St Quality Slip No', tracking=True)
    remark_note = fields.Text(string='Remarks')
    type_contract = fields.Selection([
        ('cr', 'Regular Contract'),
        ('cs', 'Consignment Contract')
    ], string='Type Contract', default=None, tracking=True)
    license_plate = fields.Char(string='Vehicle No.', required=True, states={}, tracking=True)
    change_warehouse_id = fields.Many2one('stock.warehouse', 'Change Warehouse', readonly=False,
                                          states={}, tracking=True)

    def button_commercial(self):
        for this in self:
            if this.state in ['approved', 'cancel', 'closed', 'reject']:
                raise UserError(_("Please refresh browser again for getting the new state at the moment!!"))
            if this.sample_weight_india == 0 or this.moisture_percent == 0 or this.total_percent != 100:
                raise UserError(_("You need input sample weight and moisture % and total percent = 100"
                                  " before confirm this DR!"))
            this.qc_approve_date = datetime.now()
            this.state = 'commercial'

    def button_wh_approved(self):
        for this in self:
            if this.state in ['approved', 'cancel', 'closed', 'reject']:
                raise UserError(_("Please refresh browser again for getting the new state at the moment!!"))
            this.state = 'wh_approved'
            this.qc_approve_date = datetime.now()

    def button_qc_approved(self):
        res = super().button_qc_approved()
        for this in self:
            if this.state in ['approved', 'cancel', 'closed', 'reject']:
                raise UserError(_("Please refresh browser again for getting the new state at the moment!!"))
        deduction = self.env['deduction.quality'].search([
            ('code', '!=', 'OTH')
        ]).sorted(key=lambda i: i.id)
        for record in self:
            record.deduction_ids = [(5, 0, 0)]
            for i in deduction:
                self.env['deduction.line'].create({
                    'security_gate_id': record.id,
                    'name': i.id
                })
        return res

    @api.constrains('total_gram', 'sample_weight_india')
    def _check_constraint_total_gram(self):
        for record in self:
            if record.total_gram != record.sample_weight_india:
                raise UserError(_("Sample Weight and Total Gram need to be equal!"))
    @api.depends('outturn_gram')
    def compute_outturn_percent(self):
        for record in self:
            if record.outturn_gram:
                record.outturn_percent = (record.outturn_gram / 1000) * 100
            else:
                record.outturn_percent = 0

    @api.depends('aaa_gram', 'aa_gram', 'a_gram', 'b_gram', 'c_gram', 'pb_gram', 'bb_gram', 'bleached_gram', 'idb_gram',
                 'bits_gram', 'hulks_gram', 'stone_gram', 'template_qc', 'sleeve_6_up', 'sleeve_5_5_up',
                 'sleeve_5_5_down', 'sleeve_5_down', 'skin_out_gram', 'triage_gram', 'wet_bean_gram', 'red_beans_gram',
                 'stinker_gram', 'faded_gram', 'flat_gram', 'pb1_gram', 'pb2_gram', 'sleeve_5_up', 'unhulled',
                 'remaining_coffee', 'blacks', 'half_monsoon', 'good_beans')
    def compute_percent_india(self):
        for record in self:
            record.total_gram = 0
            if record.template_qc == 'raw':
                record.total_gram = round(record.aaa_gram + record.aa_gram + record.a_gram + record.b_gram \
                                    + record.c_gram + record.pb_gram + record.bb_gram + record.bleached_gram \
                                    + record.idb_gram + record.bits_gram + record.hulks_gram + record.stone_gram \
                                    + record.skin_out_gram + record.triage_gram + record.wet_bean_gram \
                                    + record.red_beans_gram + record.stinker_gram + record.faded_gram, 2)
            if record.template_qc == 'bulk':
                record.total_gram = round(record.aaa_gram + record.aa_gram + record.a_gram + record.b_gram \
                                    + record.c_gram + record.pb_gram + record.bb_gram + record.bleached_gram \
                                    + record.idb_gram + record.bits_gram + record.hulks_gram + record.stone_gram \
                                    + record.skin_out_gram + record.triage_gram + record.wet_bean_gram \
                                    + record.red_beans_gram + record.stinker_gram + record.faded_gram + record.unhulled ,2)
            if record.template_qc == 'clean':
                record.total_gram = round(record.aaa_gram + record.aa_gram + record.a_gram + record.b_gram \
                                    + record.c_gram,2)
            if record.template_qc == 'clean_bulk':
                record.total_gram = round(record.aaa_gram + record.aa_gram + record.a_gram + record.b_gram \
                                          + record.c_gram + record.pb_gram, 2)
            if record.template_qc == 'c_grade':
                record.total_gram = round(record.sleeve_6_up + record.sleeve_5_5_down + record.sleeve_5_down + \
                                    record.sleeve_5_5_up,2)
            if record.template_qc == 'pb_grade':
                record.total_gram = round(record.flat_gram + record.pb1_gram + record.pb2_gram,2)
            if record.template_qc == 'lower':
                record.total_gram = round(record.good_beans + record.hulks_gram + record.unhulled + record.blacks +
                                          record.sleeve_5_up + record.bits_gram + record.stone_gram + record.idb_gram +
                                          record.bb_gram + record.triage_gram + record.remaining_coffee, 2)
            if record.total_gram > 0:
                record.aaa_percent = record.aaa_gram / record.total_gram * 100
                record.aa_percent = record.aa_gram / record.total_gram * 100
                record.a_percent = record.a_gram / record.total_gram * 100
                record.b_percent = record.b_gram / record.total_gram * 100
                record.c_percent = record.c_gram / record.total_gram * 100
                record.pb_percent = record.pb_gram / record.total_gram * 100
                record.bb_percent = record.bb_gram / record.total_gram * 100
                record.bleached_percent = record.bleached_gram / record.total_gram * 100
                record.idb_percent = record.idb_gram / record.total_gram * 100
                record.bits_percent = record.bits_gram / record.total_gram * 100
                record.hulks_percent = record.hulks_gram / record.total_gram * 100
                record.stone_percent = record.stone_gram / record.total_gram * 100
                record.skin_out_percent = record.skin_out_gram / record.total_gram * 100
                record.triage_percent = record.triage_gram / record.total_gram * 100
                record.wet_bean_percent = record.wet_bean_gram / record.total_gram * 100
                record.red_beans_percent = record.red_beans_gram / record.total_gram * 100
                record.stinker_percent = record.stinker_gram / record.total_gram * 100
                record.faded_percent = record.faded_gram / record.total_gram * 100
                record.flat_percent = record.flat_gram / record.total_gram * 100
                record.pb1_percent = record.pb1_gram / record.total_gram * 100
                record.pb2_percent = record.pb2_gram / record.total_gram * 100
                record.sleeve_6_up_percent = record.sleeve_6_up / record.total_gram * 100
                record.sleeve_5_5_up_percent = record.sleeve_5_5_up / record.total_gram * 100
                record.sleeve_5_5_down_percent = record.sleeve_5_5_down / record.total_gram * 100
                record.sleeve_5_down_percent = record.sleeve_5_down / record.total_gram * 100

                record.sleeve_5_up_percent = record.sleeve_5_up / record.total_gram * 100
                record.unhulled_percent = record.unhulled / record.total_gram * 100
                record.remaining_coffee_percent = record.remaining_coffee / record.total_gram * 100
                record.blacks_percent = record.blacks / record.total_gram * 100
                record.half_monsoon_percent = record.half_monsoon / record.total_gram * 100
                record.good_beans_percent = record.good_beans / record.total_gram * 100

    @api.depends('outturn_percent', 'aaa_percent', 'aa_percent', 'a_percent', 'b_percent', 'c_percent', 'pb_percent',
                 'bb_percent', 'bleached_percent', 'idb_percent', 'bits_percent', 'hulks_percent', 'stone_percent',
                 'skin_out_percent', 'triage_percent', 'wet_bean_percent', 'red_beans_percent', 'stinker_percent',
                 'faded_percent', 'flat_percent', 'pb1_percent', 'pb2_percent', 'sleeve_6_up_percent',
                 'sleeve_5_5_up_percent', 'sleeve_5_5_down_percent', 'sleeve_5_down_percent', 'template_qc', 'total_gram',
                 'sleeve_5_up_percent', 'unhulled_percent', 'remaining_coffee_percent', 'blacks_percent', 'half_monsoon_percent', 'good_beans_percent')
    def compute_total_percent(self):
        for record in self:
            record.total_percent = 0
            if record.template_qc == 'raw':
                record.total_percent = record.aaa_percent + record.aa_percent + record.a_percent \
                                       + record.b_percent + record.c_percent + record.pb_percent + record.bb_percent \
                                       + record.bleached_percent + record.idb_percent + record.bits_percent \
                                       + record.hulks_percent + record.stone_percent + record.skin_out_percent \
                                       + record.triage_percent + record.wet_bean_percent + record.red_beans_percent \
                                       + record.stinker_percent + record.faded_percent
            if record.template_qc == 'bulk':
                record.total_percent = record.aaa_percent + record.aa_percent + record.a_percent \
                                       + record.b_percent + record.c_percent + record.pb_percent + record.bb_percent \
                                       + record.bleached_percent + record.idb_percent + record.bits_percent \
                                       + record.hulks_percent + record.stone_percent + record.skin_out_percent \
                                       + record.triage_percent + record.wet_bean_percent + record.red_beans_percent \
                                       + record.stinker_percent + record.faded_percent + record.unhulled_percent
            if record.template_qc == 'clean':
                record.total_percent = record.aaa_percent + record.aa_percent + record.a_percent \
                                       + record.b_percent + record.c_percent
            if record.template_qc == 'clean_bulk':
                record.total_percent = record.aaa_percent + record.aa_percent + record.a_percent \
                                       + record.b_percent + record.c_percent + record.pb_percent
            if record.template_qc == 'c_grade':
                record.total_percent = record.sleeve_6_up_percent + record.sleeve_5_5_up_percent \
                                       + record.sleeve_5_5_down_percent + record.sleeve_5_down_percent
            if record.template_qc == 'pb_grade':
                record.total_percent = record.flat_percent + record.pb1_percent + record.pb2_percent
            if record.template_qc == 'lower':
                record.total_percent = round(record.good_beans_percent + record.hulks_percent + record.unhulled_percent + record.blacks_percent +
                    record.sleeve_5_up_percent + record.bits_percent + record.stone_percent + record.idb_percent +
                    record.bb_percent + record.triage_percent + record.remaining_coffee_percent, 2)
            if record.total_gram == 300:
                record.total_percent = 100

    def button_pur_approved(self):
        for this in self:
            this.state = 'pur_approved'
            this.arrivial_time = datetime.now()
        return True

    @api.onchange('warehouse_id', 'shipping_id')
    def onchange_warehouse(self):
        code_type = ''
        if self.env.context.get('default_type_transfer') == 'queue':
            code_type = 'incoming'
        elif self.env.context.get('default_type_transfer') == 'queue-exstore':
            code_type = 'outgoing'
        res = False
        if self.warehouse_id and self.shipping_id:
            # print(self.env.context.get('default_type_transfer')=='queue-exstore')
            s_contract = self.shipping_id.contract_id
            type_contract = s_contract.type
            if code_type == 'outgoing' and type_contract == 'local':
                res = self.env['stock.picking.type'].search(
                    [('code', '=', code_type), ('operation', '=', 'factory'), ('warehouse_id', '=', self.warehouse_id.id), ('name', 'like', 'Local')])
            if code_type == 'outgoing' and type_contract == 'export':
                res = self.env['stock.picking.type'].search(
                    [('code', '=', code_type), ('operation', '=', 'factory'),
                     ('warehouse_id', '=', self.warehouse_id.id), ('name', 'like', 'Export')])
        if self.warehouse_id and not self.shipping_id:
            if code_type == 'incoming':
                res = self.env['stock.picking.type'].search([('code', '=', code_type), ('operation', '=', 'factory'),
                                                             ('warehouse_id', '=', self.warehouse_id.id)])
        if res:
            self.picking_type_id = res.id
        else:
            self.picking_type_id = False

    def create_picking(self):
        for rec in self:
            if rec.picking_ids:
                return True
        return super(NedSecurityGateQueue, self).create_picking()

    def btt_change_warehouse(self):
        for sec in self:
            if sec.receive_state =='done' and sec.receive_state == 'approved':
                raise UserError(_('Can not change when transaction has completed!'))
            if sec.change_warehouse_id:
                #Change cho Security Gate
                sec.warehouse_id = sec.change_warehouse_id.id
                sec.picking_type_id = sec.change_warehouse_id.in_type_id.id
                #Change for Stock Picking
                for pick in sec.env['stock.picking'].sudo().search([('security_gate_id','=',sec.id)]):
                    if pick.security_gate_id:
                        pick.env['stock.picking'].sudo().search([('security_gate_id','=',sec.id)]).write({'location_dest_id':sec.change_warehouse_id.lot_stock_id.id,
                                                                                                            'warehouse_id':sec.change_warehouse_id.id,
                                                                                                            'picking_type_id': sec.change_warehouse_id.in_type_id.id})
                        if pick.picking_type_id and pick.picking_type_id.code =='incoming' and pick.picking_type_id.operation == 'factory' and pick.picking_type_id.sequence_id:
                            crop = self.env['ned.crop'].sudo().search([('start_date','<=',datetime.now().date()),('to_date','>=',datetime.now().date())],limit = 1)
                            if crop:
                                name = pick.picking_type_id.sequence_id.next_by_id()
                                a = _(name)[0:len(pick.picking_type_id.sequence_id.prefix)][:4]
                                pick.name = _(name)[0:len(pick.picking_type_id.sequence_id.prefix)][:4] + _(crop.short_name) + '-' + sec.change_warehouse_id.code + '-' + _(name)[len(pick.picking_type_id.sequence_id.prefix):len(pick.picking_type_id.sequence_id.prefix)+pick.picking_type_id.sequence_id.padding]
        return

    def print_security_gate(self):
        return self.env.ref('sd_india_security_gate.delivery_registration_india').report_action(self)

    def _get_printed_report_name(self):
        report_name = (_('%s')%(self.name))
        return report_name