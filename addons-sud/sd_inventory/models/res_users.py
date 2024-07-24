# -*- coding: utf-8 -*-
from datetime import datetime, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import format_date, format_datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import pytz

# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.tools.safe_eval import safe_eval


class Users(models.Model):
    _inherit = "res.users"
    
    
    def write(self, vals):
        self.clear_caches()
        res = super(Users, self).write(vals)
        return res
    
    def _convert_user_datetime(self, datetime_value):
        if isinstance(datetime_value, str):
            try:
                datetime_value = datetime.strptime(datetime_value, DEFAULT_SERVER_DATETIME_FORMAT)
            except Exception as e:
                raise UserError(e.args and e.args[0] or str(e))
        return fields.Datetime.context_timestamp(self, datetime_value)
    
    @api.depends('warehouse_ids', 'working_all_warehouse', 'company_ids', 'company_id')
    def _get_warehouses_dom(self):
        for user in self:
            if user.working_all_warehouse:
                warehouses = self.env['stock.warehouse'].with_context(active_test=False).sudo().\
                            search([('company_id', 'in', user.company_ids.ids)])
                domain = "[%s]" % (','.join(map(str, [i.id for i in warehouses])))
                user.warehouses_dom = domain
                # warehouses = self.env['stock.warehouse'].with_context(active_test=False).sudo(). \
                #     search([('company_id', '=', user.company_id.id)])
                user.sudo().warehouse_ids = warehouses.ids
            else:
                warehouses = user.warehouse_ids
                domain = "[%s]" % (','.join(map(str, [i.id for i in warehouses])))
                user.warehouses_dom = domain
                user.sudo().warehouse_ids = warehouses.ids
                # user.sudo()._warehouses_domain()

            
    @api.depends('warehouse_allow_ids', 'follow_all_warehouse', 'company_ids')
    def _get_warehouses_allow_dom(self):
        for user in self:
            if user.follow_all_warehouse:
                warehouses = self.env['stock.warehouse'].with_context(active_test=False).sudo(). \
                    search([('company_id', 'in', user.company_ids.ids)])
                domain = "[%s]" % (','.join(map(str, [i.id for i in warehouses])))
                user.warehouses_allow_dom = domain
                # warehouses = self.env['stock.warehouse'].with_context(active_test=False).sudo(). \
                #     search([('company_id', '=', user.company_id.id)])
                user.sudo().warehouse_allow_ids = warehouses.ids
            else:
                warehouses = user.warehouse_allow_ids
                domain = "[%s]"%(','.join(map(str, [i.id for i in warehouses])))
                user.warehouses_allow_dom = domain
                user.sudo().warehouse_allow_ids = warehouses.ids
    
    # THANH 19102020 - field working_all_warehouse mang y nghia user lam viec o tat ca kho (bao gom archived)
    working_all_warehouse = fields.Boolean(string='Working All Warehouse', default=False)
    warehouse_ids = fields.Many2many('stock.warehouse', 'current_warehouse_user_rel', 'user_id', 'warehouse_id',
        string='Working Warehouses', help='This user can read/create/modify inventory documents (e.g., delivery order or recepts.) from these warehouses.')

    # THANH 19102020 - field follow_all_warehouse mang y nghia user co the xem ton kho o tat ca kho (bao gom archived)
    follow_all_warehouse = fields.Boolean(string='Follow All Warehouse', default=False)
    warehouse_allow_ids = fields.Many2many('stock.warehouse', 'allow_warehouse_user_rel', 'user_id', 'warehouse_id',
        string='Follow Warehouses', help='This user can only see warehouses from linked many2one field on Warehouse Transfer.')
    
    warehouses_dom = fields.Char(compute="_get_warehouses_dom", store=True)
    warehouses_allow_dom = fields.Char(compute="_get_warehouses_allow_dom", store=True)
    
    @api.depends('user_picking_type_ids', 'company_id','warehouse_ids','working_all_picking_type')
    def _get_picking_type_dom(self):
        for user in self:
            picking_type = []
            if user.working_all_picking_type:
                picking_type = self.env['stock.picking.type'].with_context().sudo(). \
                    search([('warehouse_id', 'in', user.warehouse_ids.ids)])
                
                picking_type2 = self.env['stock.picking.type'].sudo().search([('active','=',False),('warehouse_id', 'in', user.warehouse_ids.ids)])
                
                if picking_type2:
                    picking_type = picking_type + picking_type2
                
                domain = "[%s]" % (','.join(map(str, [i.id for i in picking_type])))
                user.picking_type_dom = domain
                user.sudo().user_picking_type_ids = picking_type.ids
                
            else:
                picking_type = user.user_picking_type_ids
                domain = "[%s]" % (','.join(map(str, [i.id for i in picking_type])))
                user.picking_type_dom = domain

    def _picking_type_domain(self):
        domain = "[]"
        if self.picking_type_dom:
            domain = safe_eval(self.picking_type_dom)
        return domain
    
    working_all_picking_type = fields.Boolean(string='Working All Picking type', default=False)
    picking_type_dom = fields.Char(compute="_get_picking_type_dom", store=True)
    
    @api.model
    def _domain_warehouse(self):
        return "[('warehouse_id', 'in', %s)]" % self.env.user.warehouses_dom
        
    
    user_picking_type_ids = fields.Many2many('stock.picking.type', 'picking_type_users_ref','picking_type_id','user_id', 
                                            string= 'Allowed Picking type', domain=lambda self: self._domain_warehouse())
    
    def _warehouses_domain(self):
        domain = "[]"
        if self.warehouses_dom:
            domain = safe_eval(self.warehouses_dom)
        return domain
    
    def _warehouses_allow_stock(self):
        domain = "[]"
        if self.warehouses_allow_dom:
            domain = safe_eval(self.warehouses_allow_dom) 
        return domain 
    
    def _get_all_warehouses(self):
        warehouses_current = self._warehouses_domain() or []
        warehouses_allow = self._warehouses_allow_stock() or []
        merged_list = list(set(warehouses_current + warehouses_allow))
        warehouses = self.env['stock.warehouse'].browse(merged_list)
        return warehouses
    
    @api.onchange('company_id')
    def onchange_company(self):
        if not self.company_id:
            self.warehouse_ids = False
            self.warehouse_allow_ids = False
            return

    @api.onchange('company_ids')
    def _onchange_company_ids(self):
        if self.company_ids and not self.working_all_warehouse and self.warehouse_ids:
            warehouses = self.warehouse_ids.filtered(lambda x: x.company_id.id in self.company_ids.ids)
            self.warehouse_ids = warehouses.ids
        if self.company_ids and not self.follow_all_warehouse and self.warehouse_ids:
            allow_warehouses = self.warehouse_allow_ids.filtered(lambda x: x.company_id.id in self.company_ids.ids)
            self.warehouse_allow_ids = allow_warehouses.ids
        if not self.company_ids:
            self.working_all_warehouse = False
            self.warehouse_ids = False
            self.follow_all_warehouse = False
            self.warehouse_allow_ids = False
        if not self.user_has_groups('stock.group_stock_user'):
            self.warehouse_ids = False
            self.warehouse_allow_ids = False
            return
        return

    @api.onchange('working_all_warehouse')
    def onchange_working_all_warehousey(self):
        if not self.working_all_warehouse:
            self.warehouse_ids = False
            return

    @api.onchange('follow_all_warehouse')
    def onchange_follow_all_warehouse(self):
        if not self.follow_all_warehouse:
            self.warehouse_allow_ids = False
            return

