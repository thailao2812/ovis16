from datetime import datetime, date
from odoo import api, fields, models, _
from odoo.osv import osv
from odoo.exceptions import UserError
import pytz


class SynchronizeData(models.Model):
    _name = 'res.sync.data'
    _description = 'Synchronize Data v14'

    sync_id = fields.Integer(string="Synchronize ID (v14)", default=0)


    def unlink(self):
        for rec in self:
            if rec.sync_id:
                raise UserError(_("The record has been synchronized with "
                                  "another version. You cannot delete!"))
        res = super(SynchronizeData, self).unlink()
        return res

    def unlink(self):
        for rec in self:
            if rec.sync_id:
                raise UserError(_("The record has been synchronized with "
                                  "another version. You cannot delete!"))
        res = super(SynchronizeData, self).unlink()
        return res


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'res.sync.data']

    def unlink(self):
        self.write({'active': False})


class ResBank(models.Model):
    _name = 'res.bank'
    _inherit = ['res.bank', 'res.sync.data']

    def unlink(self):
        self.write({'active': False})


class ResPartnerBank(models.Model):
    _name = 'res.partner.bank'
    _inherit = ['res.partner.bank', 'res.sync.data']

    active = fields.Boolean('Active', default=True)

    def unlink(self):
        self.write({'active': False})


class Country(models.Model):
    _name = 'res.country'
    _inherit = ['res.country', 'res.sync.data']


class CountryState(models.Model):
    _name = 'res.country.state'
    _inherit = ['res.country.state', 'res.sync.data']


class ResDistrict(models.Model):
    _name = 'res.district'
    _inherit = ['res.district', 'res.sync.data']


# class ResWard(models.Model):
#     _name = 'res.ward'
#     _inherit = ['res.ward', 'res.sync.data']


# class AccountType(models.Model):
#     _name = 'account.account.type'
#     _inherit = ['account.account.type', 'res.sync.data']


class Currency(models.Model):
    _name = 'res.currency'
    _inherit = ['res.currency', 'res.sync.data']


class Tax(models.Model):
    _name = 'account.tax'
    _inherit = ['account.tax', 'res.sync.data']


class Journal(models.Model):
    _name = 'account.journal'
    _inherit = ['account.journal', 'res.sync.data']


class AnalyticAccount(models.Model):
    _name = 'account.analytic.account'
    _inherit = ['account.analytic.account', 'res.sync.data']


class Account(models.Model):
    _name = 'account.account'
    _inherit = ['account.account', 'res.sync.data']


class StockPickingType(models.Model):
    _name = 'stock.picking.type'
    _inherit = ['stock.picking.type', 'res.sync.data']


class Location(models.Model):
    _name = 'stock.location'
    _inherit = ['stock.location', 'res.sync.data']


class Warehouse(models.Model):
    _name = 'stock.warehouse'
    _inherit = ['stock.warehouse', 'res.sync.data']


class ProductCategory(models.Model):
    _name = 'product.category'
    _inherit = ['product.category', 'res.sync.data']

    active = fields.Boolean('Active', default=True)

    def unlink(self):
        self.write({'active': False})


class UoM(models.Model):
    _name = 'uom.uom'
    _inherit = ['uom.uom', 'res.sync.data']


class ProductTemplate(models.Model):
    _name = 'product.template'
    _inherit = ['product.template', 'res.sync.data']

    def unlink(self):
        self.write({'active': False})


# class AccountFinancialReport(models.Model):
#     _name = 'account.financial.report'
#     _inherit = ['account.financial.report', 'res.sync.data']


# class AccountAsset(models.Model):
#     _name = 'account.asset.category'
#     _inherit = ['account.asset.category', 'res.sync.data']


class Sequence(models.Model):
    _name = 'ir.sequence'
    _inherit = ['ir.sequence', 'res.sync.data']


class UomCategory(models.Model):
    _name = 'uom.category'
    _inherit = ['uom.category', 'res.sync.data']
