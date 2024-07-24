# -*- coding: utf-8 -*-

from marshmallow import fields
from werkzeug.exceptions import BadRequest

from odoo.addons.base_rest import restapi
from odoo.addons.component.core import Component
from odoo.addons.datamodel.core import Datamodel

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

from odoo.http import request, json
from odoo import SUPERUSER_ID
from datetime import datetime as dtime, timedelta

###========= Datamodel INPUT =========###
class PalletSearchParam(Datamodel):
    _name = "pallet.search.param"
    _inherit = "masterdata.search.param"
    
    warehouse_id = fields.String(load_default="1,22")

###========= Datamodel OUTPUT =========###
class PalletShortInfo(Datamodel):
    _name = "pallet.short.info"
    _inherit = "masterdata.short.info"

    warehouse_id = fields.Integer()
    packing_id = fields.Integer()
    description_name = fields.String()
    dimension = fields.String()
    state = fields.String()
    tare_weight = fields.Float(load_default=0.0)
    create_date = fields.DateTime()
    user_import_id = fields.Integer()
    scale_id = fields.Integer()

### ========================================================= ###
class BatchscalesApiService(Component):
    _inherit = "base.rest.service"
    _name = "batchscales.api.service"
    _usage = "batchscales"
    _collection = "sucden.restapi.services"
    _description = """
        Batchscales New API Services
        Services developed with the new api provided by IT Team - SUCDEN VN
    """
### Get Pallet ###
    @restapi.method(
        [(["/sud_packing_branch/list"], "GET")],
        input_param=restapi.Datamodel("pallet.search.param"),
        output_param=restapi.Datamodel("pallet.short.info", is_list=True),
        auth="api_key",
    )
    def packing_branch_list(self, pallet_search_param):
        """
        Search for Pallet
        @param: Input ID or Name or Warehouse ID
        @return: Return a list of Pallet-follow parameters
        """
        domain = []
        if pallet_search_param.name:
            domain.append(("name", "like", pallet_search_param.name))
        if pallet_search_param.id:
            domain.append(("id", "=", pallet_search_param.id))
        if pallet_search_param.warehouse_id and isinstance(pallet_search_param.warehouse_id, str):
            array = [int(x) for x in pallet_search_param.warehouse_id.split(",")]
            domain.append(("warehouse_id", "in", array))
        res = []
        PalletShortInfo = self.env.datamodels["pallet.short.info"]
        for p in self.env["sud.packing.branch"].search(domain):
            res.append(PalletShortInfo(id=p.id, name=p.name, warehouse_id=p.warehouse_id, packing_id=p.packing_id,
                                       description_name=p.description_name, dimension=p.dimension, state=p.state,
                                       tare_weight=p.tare_weight, create_date=str(p['create_date']), 
                                       user_import_id=p.user_import_id, scale_id=p.scale_id))
        return res
    
    # Paking Branch Line
    @restapi.method(
        [(["/sud_packing_branch_line/<int:id>"], "GET")],
        output_param=restapi.CerberusValidator("_get_pallet_history_list_schema"),
        auth="api_key",
    )

    def get_packing_branch_id(self, _id):
        return {"id": self.env["sud.packing.branch.line"].browse(_id).id}

    def _get_pallet_history_list_schema(self):
        return {"id": {"type": "integer", "required": True},
                "repair_reason": {"type": "string"},
                "tare_weight_old": {"type": "float"},
                "tare_weight_new": {"type": "float"},
                "repair_id": {},
                "scale_id": {},
                "scale_line_id": {},
                "create_date": {"type": "string"},
                "user_import_id": {},
                "uid_name": {"type": "string"}}

    @restapi.method(
        [(["/sud_packing_branch_line/pallet_history_list"], "GET")],
        output_param=restapi.CerberusListValidator("_get_pallet_history_list_schema"),
        auth="api_key",
    )
    def pallet_history_list(self):
        packing_branch_line = self.env["sud.packing.branch.line"].search([("state", "=", "done")])
        return [{"id": p.id, "repair_reason": p.repair_reason, "tare_weight_old": p.tare_weight_old,
                 "tare_weight_new": p.tare_weight_new, "repair_id": p.repair_id.id, "scale_id": p.scale_id, 
                 "scale_line_id": p.scale_line_id, "create_date": str(p.create_date), 
                 "user_import_id": p.user_import_id.id, "uid_name": p.user_import_id.partner_id.name} 
                for p in packing_branch_line]

### UPDATE PALLET ###
    @restapi.method(
        [(["/sud_packing_branch/<int:id>"], "GET")],
        output_param=restapi.CerberusValidator("_get_packing_branch_schema"),
        auth="api_key",
    )

    def get_packing_branch(self, _id):
        return {"id": self.env["sud.packing.branch"].browse(_id).id,
                "name": self.env["sud.packing.branch"].browse(_id).name}

    def _get_packing_branch_schema(self):
        return {"id": {"type": "integer"},
                "name": {"type": "string"}}
        
    def _input_packing_branch_schema(self):
        return {"warehouse_id": {"type": "integer"},
                "packing_id": {"type": "integer"},
                "dimension": {"type": "string"},
                "scale_id": {"type": "integer"},
                "repair_reason": {"type": "string"},
                "tare_weight_old": {"type": "float"},
                "tare_weight_new": {"type": "float"},
                "scale_line_id": {"type": "integer"},
                "user_import_id": {"type": "integer"}
                }
        
    def _output_packing_branch_schema(self):
        return {
                'status_code': {"type": "string"},
                'message': {"type": "string"},
                'name': {"type": "string"},
                'description_name': {"type": "string"},
                'scale_id': {"type": "integer"},
                'packing_branch_id': {"type": "integer"},
                'packing_branch_line_id': {"type": "integer"},
                'scale_line_id': {"type": "integer"},
                'tare_weight_old': {"type": "float"}
                }

    def _get_numeric(self, number):
        if number and isinstance(number, str):
            new_number = float(number) or 0.0
            return new_number

    @restapi.method(
        [(["/sud_packing_branch/create_update_pallet"], "POST")],
        input_param=restapi.CerberusValidator("_input_packing_branch_schema"),
        output_param=restapi.CerberusValidator("_output_packing_branch_schema"),
        auth="api_key",
    )

    def create_update_pallet(self, **params):
        warehouse_id = params.get('warehouse_id')
        if warehouse_id and isinstance(warehouse_id, str):
            warehouse_id = int(params.get('warehouse_id'))
        packing_id = params.get('packing_id')
        if packing_id and isinstance(packing_id, str):
            packing_id = int(params.get('packing_id'))
        dimension = params.get(u'dimension')

        scale_id = params.get('scale_id')
        if scale_id and isinstance(scale_id, str):
            scale_id = int(params.get('scale_id'))
        
        repair_reason = params.get(u'repair_reason')
        tare_weight_old = self._get_numeric(params.get('tare_weight_old'))
        tare_weight_new = self._get_numeric(params.get('tare_weight_new'))

        scale_line_id = params.get('scale_line_id')
        if scale_line_id and isinstance(scale_line_id, str):
            scale_line_id = int(params.get('scale_line_id'))

        user_import_id = params.get('user_import_id')
        if user_import_id and isinstance(user_import_id, str):
            user_import_id = int(params.get('user_import_id'))

        packing_branch_obj = request.env['sud.packing.branch'].sudo().search([('scale_id','=', scale_id)])

        if not packing_branch_obj:
            vals = {'packing_id': packing_id,
                    'description_name': 'New',
                    'dimension': dimension,
                    'warehouse_id': warehouse_id,
                    'scale_id': scale_id,
                    'user_import_id': user_import_id
                    }
            packing_branch_id = request.env['sud.packing.branch'].with_user(182).create(vals)
            if packing_branch_id:
                packing_branch_id.with_user(user_import_id).update({
                    'description_name': packing_branch_id.packing_id.name + '/' + packing_branch_id.name})

                tmp = {'repair_reason': repair_reason,
                    'tare_weight_old': tare_weight_old,
                    'tare_weight_new': tare_weight_new,
                    'scale_id': scale_id,
                    'repair_id': packing_branch_id.id,
                    'user_import_id': user_import_id,
                    'scale_line_id': scale_line_id
                    }
                packing_branch_line_id = request.env['sud.packing.branch.line'].with_user(182).create(tmp)
                packing_branch_id.button_done()

                mess = {
                    'status_code': "SUD23-200",
                    'message': "Create new item completed!",
                    'name': packing_branch_id.name,
                    'description_name': packing_branch_id.description_name,
                    'scale_id': packing_branch_id.scale_id,
                    'packing_branch_id': packing_branch_id.id,
                    'packing_branch_line_id': packing_branch_line_id.id,
                    'scale_line_id': packing_branch_line_id.scale_line_id,
                    'tare_weight_old': packing_branch_line_id.tare_weight_old
                    }
                return json.dumps(mess)

        elif packing_branch_obj: # and (flag == u'Newline' or flag == u'Update')
            packing_obj = request.env['ned.packing'].sudo().search([('id','=', packing_id)])
            packing_branch_obj.with_user(user_import_id).update({
                'description_name': packing_obj.name + '/' + packing_branch_obj.name,
                'packing_id': packing_id,
                'dimension': dimension,
                'tare_weight': packing_branch_obj.tare_weight,
                })

            packing_branch_line_obj = request.env['sud.packing.branch.line'].sudo().search([('scale_line_id','=', scale_line_id)])
            if tare_weight_new == 0 and packing_branch_line_obj:
                packing_branch_line_obj.with_user(user_import_id).update({
                    'repair_reason': repair_reason,
                    'user_import_id': user_import_id
                    })
                packing_branch_obj.button_done()

                mess = {
                    'status_code': "SUD23-200",
                    'message': "Update item completed!",
                    'name': packing_branch_obj.name,
                    'description_name': packing_branch_obj.description_name,
                    'scale_id': packing_branch_obj.scale_id,
                    'packing_branch_id': packing_branch_obj.id,
                    'packing_branch_line_id': packing_branch_line_obj.id,
                    'scale_line_id': packing_branch_line_obj.scale_line_id,
                    'tare_weight_old': packing_branch_line_obj.tare_weight_old
                    }
                return json.dumps(mess)
            else:
                tmp = {'repair_reason': repair_reason,
                    'tare_weight_old': tare_weight_old,
                    'tare_weight_new': tare_weight_new,
                    'scale_id': scale_id,
                    'repair_id': packing_branch_obj.id,
                    'user_import_id': user_import_id,
                    'scale_line_id': scale_line_id
                    }
                packing_branch_line_obj = request.env['sud.packing.branch.line'].with_user(182).create(tmp)
                packing_branch_obj.button_done()

                mess = {
                    'status_code': "SUD23-200",
                    'message': "Create new item completed!",
                    'name': packing_branch_obj.name,
                    'description_name': packing_branch_obj.description_name,
                    'scale_id': packing_branch_obj.scale_id,
                    'packing_branch_id': packing_branch_obj.id,
                    'packing_branch_line_id': packing_branch_line_obj.id,
                    'scale_line_id': packing_branch_line_obj.scale_line_id,
                    'tare_weight_old': packing_branch_line_obj.tare_weight_old
                    }
                return json.dumps(mess)

