# -*- encoding: utf-8 -*-
from odoo import fields, models, api, _


class SupplierMasterDate(models.Model):
    _name = 'supplier.master.data'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Supplier', related='supplier_id.name')
    supplier_id = fields.Many2one('res.partner', string='Supplier')
    upload_count = fields.Integer(string='# Uploads', compute='compute_data', store=True)
    last_upload = fields.Date(string='Last Upload', compute='compute_data', store=True)
    status = fields.Selection([
        ('red', 'Red'),
        ('green', 'Green'),
        ('yellow', 'Yellow')
    ], string='Supplier Status', compute='compute_status', store=True)
    import_ids = fields.One2many('import.geojson', 'supplier_master_id')

    @api.depends('import_ids', 'import_ids.state', 'import_ids.status_check')
    def compute_data(self):
        for rec in self:
            rec.upload_count = (len(rec.import_ids))
            rec.last_upload = max(rec.import_ids.mapped('import_date')) if rec.import_ids else False

    @api.depends('import_ids', 'import_ids.status_check', 'import_ids.state')
    def compute_status(self):
        for rec in self:
            if rec.import_ids:
                print(rec.import_ids.mapped('status_check'))
                if 'green' in rec.import_ids.mapped('status_check') and len(rec.import_ids.mapped('status_check')) == 1:
                    rec.status = 'green'
                if 'red' in rec.import_ids.mapped('status_check') and len(rec.import_ids.mapped('status_check')) == 1:
                    rec.status = 'red'
                if 'red' in rec.import_ids.mapped('status_check') and 'green' in rec.import_ids.mapped('status_check'):
                    rec.status = 'yellow'
            else:
                rec.status = 'yellow'




