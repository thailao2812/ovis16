# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class PSSManagement(models.Model):
    _inherit = "pss.management"

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')

    outturn_percent = fields.Float(string='Outturn%', digits=(12, 2))
    aaa_percent = fields.Float(string="AAA%",  )
    aa_percent = fields.Float(string="AA%",  )
    a_percent = fields.Float(string="A%",  )
    b_percent = fields.Float(string="B%",  )
    c_percent = fields.Float(string="C%",  )
    pb_percent = fields.Float(string="PB%",  )
    bb_percent = fields.Float(string="BB%",  )
    bleached_percent = fields.Float(string="Bleached%",  )
    idb_percent = fields.Float(string="IDB%",  )
    bits_percent = fields.Float(string="Bits%",  )
    hulks_percent = fields.Float(string="Husk%",  )
    stone_percent = fields.Float(string="Stone%",  )
    skin_out_percent = fields.Float(string='Skin Out%',  )
    triage_percent = fields.Float(string='Triage%',  )
    wet_bean_percent = fields.Float(string='Wet Beans%',  )
    red_beans_percent = fields.Float(string='Red Beans%',  )
    stinker_percent = fields.Float(string='Stinker%',  )
    faded_percent = fields.Float(string='Faded%',  )
    flat_percent = fields.Float(string='Flat%',  )
    pb1_percent = fields.Float(string='PB1%',  )
    pb2_percent = fields.Float(string='PB2%',  )
    sleeve_6_up_percent = fields.Float(string='6↑ %',  )
    sleeve_5_5_up_percent = fields.Float(string='5.5↑ %',  )
    sleeve_5_5_down_percent = fields.Float(string='5.5↓%',  )
    sleeve_5_down_percent = fields.Float(string='5↓ %',  )

    sleeve_5_up_percent = fields.Float(string='5↑ %',  )
    unhulled_percent = fields.Float(string='Unhulled %',  )
    remaining_coffee_percent = fields.Float(string='Remaining Coffee %',  )
    blacks_percent = fields.Float(string='Blacks %',  )
    half_monsoon_percent = fields.Float(string='Half Monsoon %',  )
    good_beans_percent = fields.Float(string='Good Beans %',  )

    moisture_percent = fields.Float(string='Moisture%', digits=(12, 2),  )

    # New field for india
    s_contract_id = fields.Many2one('s.contract', string='Sale Contract')
    product_id = fields.Many2one("product.product", related='s_contract_id.product_id', string="Product", store=True)
    s_contract_date = fields.Date(related='s_contract_id.date', store=True, string='Sale Contract Date')
    shipping_id = fields.Many2one("shipping.instruction", string="SI No.", compute='_compute_data_from_s_contract', store=True)
    shipping_date = fields.Date(string='SI Date', related='shipping_id.date', store=True)
    partner_id = fields.Many2one("res.partner", string="Customer", related='shipping_id.partner_id', store=True)
    ship_to = fields.Many2one('res.partner', string='Ship To', related='shipping_id.ship_to', store=True)
    certificate_id = fields.Many2one('ned.certificate', compute='_compute_data_from_s_contract', store=True)
    crop_id = fields.Many2one('ned.crop', string='Crop Year', related='s_contract_id.crop_id', store=True)
    pss_type = fields.Selection(related='s_contract_id.pss_type', store=True, string='PSS Type')
    contract_qty = fields.Float(string='Contract Qty', related='s_contract_id.total_qty', store=True)
    sample_qty = fields.Float(string='Sample Qty')
    sample_sent_date = fields.Date(string='Sample Sent On')
    sample_ref = fields.Char(string='Sample Ref No')
    courier = fields.Char(string='Courier')
    awb_no = fields.Char(string='AWB No.')
    shipt_month = fields.Many2one('s.period', related='s_contract_id.shipt_month', store=True)
    pss_delivery_date = fields.Date(string='PSS Delivery Date')
    pss_status = fields.Selection(
        [('pending', 'Pending'), ('sent', 'Sent'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        string="PSS status", default='pending')
    approve_date = fields.Date(string='Approve On')
    reject_date = fields.Date(string='Reject On')
    reason_reject = fields.Text(string='Reason Reject')
    buyer_ref = fields.Char(string='Buyer Ref')
    note = fields.Text(string='Note')
    buyer_comment = fields.Text(string="Buyer's Comment")
    comment = fields.Text(string='Our Comment')
    inspector = fields.Char(string='Inspector')
    qc_staff_id = fields.Many2one('res.users', string='QC Staff')

    @api.depends('s_contract_id')
    def _compute_data_from_s_contract(self):
        for rec in self:
            if rec.s_contract_id:
                shipping_id = self.env['shipping.instruction'].search([
                    ('contract_id', '=', rec.s_contract_id.id)
                ])
                if rec.s_contract_id.certificated_ids:
                    rec.certificate_id = rec.s_contract_id.certificated_ids[0].id
                else:
                    rec.certificate_id = False
                if shipping_id:
                    rec.shipping_id = shipping_id.id
                else:
                    rec.shipping_id = False
            else:
                rec.certificate_id = False
                rec.shipping_id = False