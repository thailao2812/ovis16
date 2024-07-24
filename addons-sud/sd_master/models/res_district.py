# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class ResCountry(models.Model):
    _inherit = "res.country"
    _description = 'Res Country'
    
    def name_get(self):
        result = []
        for pro in self:
            result.append((pro.id, pro.code))
        return result


class ResDistrict(models.Model):
    _name = "res.district"
    _description = 'Res District'

    name = fields.Char('Name', required=True)
    state_id = fields.Many2one('res.country.state', 'Province')
    active =fields.Boolean("Active", default=True)
        
    # def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
    #     if context is None:
    #         context = {}
    #
    #     if context.get('state_id'):
    #         arg = ('state_id', '=', context.get('state_id'))
    #         args.append(arg)
    #     return super(res_district, self).search(cr, uid, args, offset, limit, order, context=context, count=count) 
    
#     def init(self, cr):
#         cr.execute('select district_imported from res_company where district_imported=True limit 1')
#         res = cr.fetchone()
#         district_imported = False
#         if res and res[0]:
#             district_imported = True
#         
#         if not district_imported:
#             state_obj = self.pool.get('res.country.state')
#             wb = open_workbook(base_path + '/general_base/data/QuanHuyen.xls')
#             for s in wb.sheets():
#                 if (s.name =='Sheet1'):
#                     for row in range(1,s.nrows):
#                         val0 = s.cell(row,0).value
#                         val1 = s.cell(row,1).value
#                         state_ids = state_obj.search(cr, 1, [('name','=',val1)])
#                         if state_ids:
#                             print 'State 1 ' + str(state_ids)
#                             quan_huyen_ids = self.search(cr, 1, [('name','=',val0),('state_id','in',state_ids)])
#                             if not quan_huyen_ids:
#                                 print 'State 2 ' + str(state_ids)
#                                 self.create(cr, 1, {'name': val0,'state_id':state_ids[0]})
#             cr.execute('update res_company set district_imported=True')
            
                            
class CountryState(models.Model):
    _inherit = 'res.country.state'

    districts = fields.One2many('res.district', 'state_id', string='Districts'),

    