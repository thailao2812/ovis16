# -*- coding: utf-8 -*-

# from odoo.http import http
from odoo import SUPERUSER_ID
# from odoo.addons.website import slug, unslug
from odoo.http import route, request, json
from odoo import http
from odoo.exceptions import AccessError, UserError
# from models import JWTAuth


class API_NED_HR(http.Controller):

    @http.route('/api/hr/department', type='http', methods=['GET'], auth='none', website = True, csrf=False)
    def list_department(self):
        sql = '''SELECT id, name from hr_department'''
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)

    @http.route('/api/hr/employees', type='http', methods=['GET'], auth='none', website = True, csrf=False)
    def list_employees(self):
        sql = '''SELECT id, code, name_related, gender, department_id from hr_employee where struct_salary_id = 14 and resigned_date is null'''
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)

