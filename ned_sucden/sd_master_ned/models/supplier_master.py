# -*- encoding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError


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
                value = []
                for i in rec.import_ids.mapped('status_check'):
                    if i not in value:
                        value.append(i)
                if len(value) == 1:
                    if 'red' in value:
                        rec.status = 'red'
                    if 'green' in value:
                        rec.status = 'green'
                if len(value) > 1:
                    rec.status = 'yellow'
            else:
                rec.status = 'yellow'

    @api.constrains('supplier_id')
    def _check_constraint_supplier_id(self):
        for record in self:
            supplier_master = self.search([('supplier_id', '=', record.supplier_id.id),
                                      ('id', '!=', record.id)], limit=1)
            if supplier_master:
                raise UserError(_("Cannot create more than 1 record for %s") % (record.supplier_id.name))




