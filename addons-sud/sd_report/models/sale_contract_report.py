# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
import re
DATE_FORMAT = "%Y-%m-%d"
import datetime, time

from datetime import datetime
# 
class KcsSalesReport(models.Model):
	_name = 'v.kcs.sales.contract'
	_description = 'Report of Sales Contract for KCS'
	_auto = False

	p_contract=fields.Char(string='P Contract')
	s_no=fields.Char(string='S Contract')
	nvs_no=fields.Char(string='NVS Number')
	end_buyer=fields.Char(string='End Buyer')

	# def init(self, cr):
	# 	tools.drop_view_if_exists(cr, 'v_kcs_sales_contract')
	# 	cr.execute("""
	# 		CREATE OR REPLACE VIEW public.v_kcs_sales_contract AS
	# 			SELECT 
	# 				row_number() OVER () AS id,
	# 				nvs.name AS nvs_no,
	# 				nvs.p_contract,
	# 				sc.name AS s_no,
	# 				rp.name AS end_buyer
	# 			FROM sale_contract nvs
	# 				JOIN shipping_instruction si ON nvs.shipping_id = si.id
	# 				JOIN s_contract sc ON si.contract_id = sc.id
	# 				JOIN res_partner rp ON nvs.partner_id = rp.id;
	# 	""")