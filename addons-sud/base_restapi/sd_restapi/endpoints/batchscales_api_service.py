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
from dateutil.relativedelta import relativedelta

###========= Datamodel INPUT =========###
class PalletSearchParam(Datamodel):
    _name = "pallet.search.param"
    _inherit = "masterdata.search.param"
    
    warehouse_id = fields.String(load_default="1,22")

class MRPProductionSearchParam(Datamodel):
    _name = "mrp.production.search.param"
    _inherit = "pallet.search.param"

class OperationResultSearchParam(Datamodel):
    _name = "mrp.operation.result.produced.product.search.param"
    
    id = fields.Integer(required=False, allow_none=False)
    pending_grn = fields.String(required=False, allow_none=False)
    warehouse_id = fields.String(load_default="1,22")
    
class OperationResultScaleLineSearchParam(Datamodel):
    _name = "mrp.operation.result.scale.search.param"
    
    id = fields.Integer(required=False, allow_none=False)
    scale_no = fields.String(required=False, allow_none=False)

class RequestMaterialsLineSearchParam(Datamodel):
    _name = "request_materials_line.search.param"
    
    rml_id = fields.Integer(required=False, allow_none=False)
    pmr_name = fields.String(required=False, allow_none=False)
    warehouse_id = fields.String(load_default="1,22")

class StockMoveLineSearchParam(Datamodel):
    _name = "stock_move_line.search.param"
    
    sp_id = fields.Integer(required=False, allow_none=False)
    name = fields.String(required=False, allow_none=False)
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

class MRPProductionShortInfo(Datamodel):
    _name = "mrp.production.short.info"
    _inherit = "masterdata.short.info"

    bom_name = fields.String()
    grade_name = fields.String()
    batch_type = fields.String()
    date_planned_start = fields.DateTime()
    product_issued = fields.Integer()
    product_received = fields.Integer()
    product_balance = fields.Integer()
    state = fields.String()
    warehouse_id = fields.Integer()

class OperationResultShortInfo(Datamodel):
    _name = "mrp.operation.result.produced.product.short.info"

    pending_grn = fields.String()
    sp_name = fields.String()
    state = fields.String()
    product_qty = fields.Float()
    production_weight = fields.Float()
    state_kcs = fields.String()
    production_id = fields.Integer()
    mrp_result_id = fields.Integer()
    product_id = fields.Integer()
    packing_id = fields.Integer()
    zone_id = fields.Integer()
    qty_bags = fields.Integer()
    notes = fields.String()
    tare_weight = fields.Float()
    operation_result_id = fields.Integer()
    scale_grp_id = fields.Integer()
    create_date = fields.DateTime()

class OperationResultScaleLineShortInfo(Datamodel):
    _name = "mrp.operation.result.scale.short.info"

    id = fields.Integer()
    create_date = fields.DateTime()
    usr_api_create = fields.Integer()
    product_id = fields.Integer()
    packing_id = fields.Integer()
    weight_scale = fields.Float()
    bag_no = fields.Integer()
    tare_weight = fields.Float()
    net_weight = fields.Float()
    operation_result_id = fields.Integer()
    shift_name = fields.String()
    packing_branch_id = fields.Integer()
    pallet_weight = fields.Float()
    lining_bag = fields.String()
    scale_grp_id = fields.Integer()
    scale_grp_line_id = fields.Integer()
    picking_scale_id = fields.Integer()
    scale_gip_id = fields.Integer()
    scale_gip_line_id = fields.Integer()
    old_weight = fields.Float()
    bag_code = fields.String()
    state_scale = fields.String()
    scale_no = fields.String()

class RequestMaterialsLineShortInfo(Datamodel):
    _name = "request_materials_line.short.info"

    rml_id = fields.Integer()
    production_id = fields.Integer()
    mrp_name = fields.String()
    product_id = fields.Integer()
    default_code = fields.String()
    stack_id = fields.Integer()
    stack_name = fields.String()
    packing_id = fields.Integer()
    bag_no = fields.Integer()
    qty_stack = fields.Float(load_default=0.0)
    product_qty = fields.Float(load_default=0.0)
    issue_qty = fields.Float(load_default=0.0)
    to_be_issue = fields.Float(load_default=0.0)
    pmr_id = fields.Integer()
    pmr_name = fields.String()
    zone_id = fields.Integer()
    zone_name = fields.String()
    rml_state = fields.String()
    create_date = fields.DateTime()

class StockMoveLineShortInfo(Datamodel):
    _name = "stock_move_line.short.info"

    sp_id = fields.Integer()
    name = fields.String()
    lot_id = fields.Integer()
    stack_name = fields.String()
    production_id = fields.Integer()
    mrp_name = fields.String()
    init_qty = fields.Float(load_default=0.0)
    bag_no = fields.Integer()
    packing_id = fields.Integer()
    state_kcs = fields.String()
    rml_id = fields.Integer()
    rm_id = fields.Integer()
    rm_name = fields.String()
    sp_state = fields.String()
    tare_weight = fields.Float(load_default=0.0)
    gross_weight = fields.Float(load_default=0.0)
    product_id = fields.Integer()
    scale_gip_id = fields.Integer()

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
    def packing_branch_list(self, packing_branch_param):
        """
        Search for Pallet
        @param: Input ID or Name or Warehouse ID
        @return: Return a list of Pallet-follow parameters
        """
        domain = []
        if packing_branch_param.name:
            domain.append(("name", "like", packing_branch_param.name))
        if packing_branch_param.id:
            domain.append(("id", "=", packing_branch_param.id))
        if packing_branch_param.warehouse_id and isinstance(packing_branch_param.warehouse_id, str):
            array = [int(x) for x in packing_branch_param.warehouse_id.split(",")]
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
        tare_weight_old = float(params.get('tare_weight_old'))
        tare_weight_new = float(params.get('tare_weight_new'))

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
                return mess

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
                return mess
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
                return mess

### MRP PRODUCTION ###
    @restapi.method(
        [(["/mrp_production/<int:id>"], "GET")],
        output_param=restapi.CerberusValidator("_get_mrp_production_schema"),
        auth="api_key",
    )

    def get_mrp_production(self, _id):
        return {"id": self.env["mrp.production"].browse(_id).id,
                "name": self.env["mrp.production"].browse(_id).name,
                "batch_type": self.env["mrp.production"].browse(_id).batch_type,
                "date_planned_start": self.env["mrp.production"].browse(_id).date_planned_start,
                "product_issued": self.env["mrp.production"].browse(_id).product_issued,
                "product_received": self.env["mrp.production"].browse(_id).product_received,
                "product_balance": self.env["mrp.production"].browse(_id).product_balance,
                "state": self.env["mrp.production"].browse(_id).state,
                }

    def _get_mrp_production_schema(self):
        return {"id": {"type": "integer"},
                "name": {"type": "string"},
                "batch_type": {"type": "string"},
                "date_planned_start": {"type": "datetime"},
                "product_issued": {},
                "product_received": {},
                "product_balance": {},
                "state": {"type": "string"}
                }

    @restapi.method(
        [(["/mrp_production/list"], "GET")],
        input_param=restapi.Datamodel("mrp.production.search.param"),
        output_param=restapi.Datamodel("mrp.production.short.info", is_list=True),
        auth="api_key",
    )
    def mrp_production_list(self, mrp_production_param):
        """
        Search for MRP Production List
        @param: Input ID or Name or Warehouse ID
        @return: Return a list of MRP Production follow parameters
        """
        domain = [('create_date','>=',((dtime.today()-relativedelta(months=1)).strftime('%Y-%m-%d')))]
        if mrp_production_param.name:
            domain.append(("name", "like", mrp_production_param.name))
        if mrp_production_param.id:
            domain.append(("id", "=", mrp_production_param.id))
        if mrp_production_param.warehouse_id and isinstance(mrp_production_param.warehouse_id, str):
            array = [int(x) for x in mrp_production_param.warehouse_id.split(",")]
            domain.append(("warehouse_id", "in", array))
        res = []
        MRPProductionShortInfo = self.env.datamodels["mrp.production.short.info"]
        for p in self.env["mrp.production"].search(domain):
            res.append(MRPProductionShortInfo(id=p.id, name=p.name, bom_name=p.bom_id.code, grade_name=p.grade_id.name,
                                              batch_type=p.batch_type, date_planned_start=str(p['date_planned_start']), 
                                              product_issued=p.product_issued, product_received=p.product_received, 
                                              product_balance=p.product_balance, state=p.state, warehouse_id=p.warehouse_id))
        return res
    
### Operation Result ###
    @restapi.method(
        [(["/mrp_operation_result_produced_product/<int:id>"], "GET")],
        output_param=restapi.CerberusValidator("_get_mrp_operation_result_produced_product_schema"),
        auth="api_key",
    )

    def get_mrp_operation_result_produced_product(self, _id):
        return {"id": self.env["mrp.operation.result.produced.product"].browse(_id).id,
                "pending_grn": self.env["mrp.operation.result.produced.product"].browse(_id).pending_grn,
                "state": self.env["mrp.operation.result.produced.product"].browse(_id).state,
                "product_qty": self.env["mrp.operation.result.produced.product"].browse(_id).product_qty,
                "production_weight": self.env["mrp.operation.result.produced.product"].browse(_id).production_weight,
                "production_id": self.env["mrp.operation.result.produced.product"].browse(_id).production_id,
                "product_id": self.env["mrp.operation.result.produced.product"].browse(_id).product_id,
                "packing_id": self.env["mrp.operation.result.produced.product"].browse(_id).packing_id,
                "zone_id": self.env["mrp.operation.result.produced.product"].browse(_id).zone_id,
                "qty_bags": self.env["mrp.operation.result.produced.product"].browse(_id).qty_bags,
                "notes": self.env["mrp.operation.result.produced.product"].browse(_id).notes,
                "tare_weight": self.env["mrp.operation.result.produced.product"].browse(_id).tare_weight,
                "operation_result_id": self.env["mrp.operation.result.produced.product"].browse(_id).operation_result_id,
                "scale_grp_id": self.env["mrp.operation.result.produced.product"].browse(_id).scale_grp_id,
                "create_date": self.env["mrp.operation.result.produced.product"].browse(_id).create_date,
                }

    def _get_mrp_operation_result_produced_product_schema(self):
        return {"id": {"type": "integer"},
                "pending_grn": {"type": "string"},
                "state": {"type": "string"},
                "product_qty": {},
                "production_weight": {},
                "production_id": {},
                "product_id": {},
                "packing_id": {},
                "zone_id": {},
                "qty_bags": {},
                "notes": {},
                "tare_weight": {},
                "operation_result_id": {},
                "scale_grp_id": {},
                "create_date": {"type": "datetime"}
                }
        
    @restapi.method(
        [(["/mrp_operation_result_produced_product/list"], "GET")],
        input_param=restapi.Datamodel("mrp.operation.result.produced.product.search.param"),
        output_param=restapi.Datamodel("mrp.operation.result.produced.product.short.info", is_list=True),
        auth="api_key",
    )
    def mrp_operation_result_produced_product_list(self, mrp_operation_result_produced_product_param):
        """
        Search for mrp_operation_result_produced_product List
        @param: Input ID or Name or Warehouse ID
        @return: Return a list of mrp_operation_result_produced_product follow parameters
        """
        domain = [('picking_id.create_date','>=',((dtime.today()-relativedelta(months=1)).strftime('%Y-%m-%d')))]
        if mrp_operation_result_produced_product_param.pending_grn:
            domain.append(("pending_grn", "like", mrp_operation_result_produced_product_param.pending_grn))
        if mrp_operation_result_produced_product_param.id:
            domain.append(("id", "=", mrp_operation_result_produced_product_param.id))
        if mrp_operation_result_produced_product_param.warehouse_id and isinstance(mrp_operation_result_produced_product_param.warehouse_id, str):
            array = [int(x) for x in mrp_operation_result_produced_product_param.warehouse_id.split(",")]
            domain.append(("production_id.warehouse_id", "in", array))
        res = []
        OperationResultShortInfo = self.env.datamodels["mrp.operation.result.produced.product.short.info"]
        for p in self.env["mrp.operation.result.produced.product"].search(domain):
            res.append(OperationResultShortInfo(pending_grn=str(p['pending_grn']), sp_name=p.picking_id.name, state=p.state, 
                                              product_qty=p.product_qty, production_weight=p.production_weight,
                                              state_kcs=p.picking_id.state_kcs, production_id=p.production_id, 
                                              mrp_result_id=p.id, product_id=p.product_id, packing_id=p.packing_id,
                                              zone_id=p.zone_id, qty_bags=p.qty_bags, notes=str(p['notes']), tare_weight=p.tare_weight,
                                              operation_result_id=p.operation_result_id, scale_grp_id=p.scale_grp_id,
                                              create_date=str(p['create_date'])))
        return res

### GET Weight Scale Line ###
    @restapi.method(
        [(["/mrp_operation_result_scale/<int:id>"], "GET")],
        output_param=restapi.CerberusValidator("_get_mrp_operation_result_scale_schema"),
        auth="api_key",
    )

    def get_mrp_operation_result_scale(self, _id):
        return {"id": self.env["mrp.operation.result.scale"].browse(_id).id,
                "create_date": self.env["mrp.operation.result.scale"].browse(_id).create_date,
                "usr_api_create": self.env["mrp.operation.result.scale"].browse(_id).usr_api_create,
                "product_id": self.env["mrp.operation.result.scale"].browse(_id).product_id,
                "packing_id": self.env["mrp.operation.result.scale"].browse(_id).packing_id,
                "weight_scale": self.env["mrp.operation.result.scale"].browse(_id).weight_scale,
                "bag_no": self.env["mrp.operation.result.scale"].browse(_id).bag_no,
                "tare_weight": self.env["mrp.operation.result.scale"].browse(_id).tare_weight,
                "net_weight": self.env["mrp.operation.result.scale"].browse(_id).net_weight,
                "operation_result_id": self.env["mrp.operation.result.scale"].browse(_id).operation_result_id,
                "shift_name": self.env["mrp.operation.result.scale"].browse(_id).shift_name,
                "packing_branch_id": self.env["mrp.operation.result.scale"].browse(_id).packing_branch_id,
                "pallet_weight": self.env["mrp.operation.result.scale"].browse(_id).pallet_weight,
                "lining_bag": self.env["mrp.operation.result.scale"].browse(_id).lining_bag,
                "scale_grp_id": self.env["mrp.operation.result.scale"].browse(_id).scale_grp_id,
                "scale_grp_line_id": self.env["mrp.operation.result.scale"].browse(_id).scale_grp_line_id,
                "picking_scale_id": self.env["mrp.operation.result.scale"].browse(_id).picking_scale_id,
                "scale_gip_id": self.env["mrp.operation.result.scale"].browse(_id).scale_gip_id,
                "scale_gip_line_id": self.env["mrp.operation.result.scale"].browse(_id).scale_gip_line_id,
                "old_weight": self.env["mrp.operation.result.scale"].browse(_id).old_weight,
                "bag_code": self.env["mrp.operation.result.scale"].browse(_id).bag_code,
                "state_scale": self.env["mrp.operation.result.scale"].browse(_id).state_scale,
                "scale_no": self.env["mrp.operation.result.scale"].browse(_id).scale_no,
                }

    def _get_mrp_operation_result_scale_schema(self):
        return {"id": {"type": "integer"},
                "create_date": {"type": "datetime"},
                "usr_api_create": {},
                "product_id": {},
                "packing_id": {},
                "weight_scale": {"type": "float"},
                "bag_no": {},
                "tare_weight": {"type": "float"},
                "net_weight": {"type": "float"},
                "operation_result_id": {},
                "shift_name": {"type": "string"},
                "packing_branch_id": {},
                "pallet_weight": {"type": "float"},
                "lining_bag": {"type": "string"},
                "scale_grp_id": {},
                "scale_grp_line_id": {},
                "picking_scale_id": {},
                "scale_gip_id": {},
                "scale_gip_line_id": {},
                "old_weight": {"type": "float"},
                "bag_code": {},
                "state_scale": {"type": "string"},
                "scale_no": {"type": "string"},
                }
        
    @restapi.method(
        [(["/mrp_operation_result_scale/list"], "GET")],
        input_param=restapi.Datamodel("mrp.operation.result.scale.search.param"),
        output_param=restapi.Datamodel("mrp.operation.result.scale.short.info", is_list=True),
        auth="api_key",
    )
    def mrp_operation_result_scale_list(self, mrp_operation_result_scale_param):
        """
        Search for mrp_operation_result_scale List
        @param: Input ID or Name or scale_no (scalex)
        @return: Return a list of mrp_operation_result_scale follow parameters
        """
        domain = [('create_date','>=',((dtime.today()-relativedelta(months=1)).strftime('%Y-%m-%d')))]
        if mrp_operation_result_scale_param.scale_no:
            domain.append(("scale_no", "like", mrp_operation_result_scale_param.scale_no))
        if mrp_operation_result_scale_param.id:
            domain.append(("id", "=", mrp_operation_result_scale_param.id))

        res = []
        OperationResultScaleLineShortInfo = self.env.datamodels["mrp.operation.result.scale.short.info"]
        for p in self.env["mrp.operation.result.scale"].search(domain):
            res.append(OperationResultScaleLineShortInfo(id=p.id, create_date=str(p['create_date']), usr_api_create=p.usr_api_create, 
                                                         product_id=p.product_id, packing_id=p.packing_id, weight_scale=p.weight_scale, 
                                                         bag_no=p.bag_no, tare_weight=p.tare_weight, net_weight=p.net_weight, operation_result_id=p.operation_result_id,
                                                         shift_name=str(p['shift_name']), packing_branch_id=p.packing_branch_id, pallet_weight=p.pallet_weight,
                                                         lining_bag=p.lining_bag, scale_grp_id=p.scale_grp_id, scale_grp_line_id=p.scale_grp_line_id,
                                                         picking_scale_id=p.picking_scale_id, scale_gip_id=p.scale_gip_id, scale_gip_line_id=p.scale_gip_line_id,
                                                         old_weight=p.old_weight, bag_code=str(p['bag_code']), state_scale=p.state_scale, scale_no=str(p['scale_no'])
                                                        ))
        return res

### CREATE UPDATE MRP Operation Result Weight Scale Line ###
    def _input_scale_line_schema(self):
        return {"warehouse_id": {"type": "integer"},
                "production_id": {"type": "integer"},
                "product_id": {"type": "integer"},
                "packing_id": {"type": "integer"},
                "pending_grp_name": {"type": "string"},
                "zone_id": {"type": "integer"},
                "contract": {"type": "string"},
                "notes": {"type": "string"},
                "production_shift": {"type": "string"},
                "user_import_id": {"type": "integer"},
                "shift_name": {"type": "string"},
                "scale_packing_id": {"type": "integer"},
                "scale_tare_weight": {"type": "float"},
                "scale_basis_weight": {"type": "float"},
                "scale_net_weight": {"type": "float"},
                "flag": {"type": "string"},
                "scale_grp_id": {"type": "integer"},
                "scale_grp_line_id": {"type": "integer"},
                "packing_branch_id": {"type": "string"},
                "pallet_weight": {"type": "float"},
                "lining_bag": {"type": "string"},
                "bag_no": {"type": "integer"},
                "scale_no": {"type": "string"},
                }
        
    def _output_scale_line_schema(self):
        return {
                'status_code': {"type": "string"},
                'message': {"type": "string"},
                'mor_name': {"type": "string"},
                'operation_result_id': {"type": "integer"},
                'mrp_result_id': {"type": "integer"},
                'odoo_scale_line_id': {"type": "integer"},
                'produced_product_state': {"type": "string"},
                }

    @restapi.method(
        [(["/mrp_operation_result_scale/create_update_scale_line"], "POST")],
        input_param=restapi.CerberusValidator("_input_scale_line_schema"),
        output_param=restapi.CerberusValidator("_output_scale_line_schema"),
        auth="api_key",
    )

    def create_update_scale_line(self, **params):
        flag = params.get('flag')
        scale_no = params.get('scale_no')
        warehouse_id = params.get('warehouse_id')
        if warehouse_id and isinstance(warehouse_id, str):
            warehouse_id = int(params.get('warehouse_id'))
        production_id = params.get('production_id')
        if production_id and isinstance(production_id, str):
            production_id = int(params.get('production_id'))        
        product_id = params.get('product_id')
        if product_id and isinstance(product_id, str):
            product_id = int(params.get('product_id'))
        packing_id = params.get('packing_id')
        if packing_id and isinstance(packing_id, str):
            packing_id = int(params.get('packing_id'))
        pending_grp_name = params.get(u'pending_grp_name')
        zone_id = params.get('zone_id')
        if zone_id and isinstance(zone_id, str):
            zone_id = int(params.get('zone_id'))

        contract = params.get(u'contract')
        notes = params.get(u'notes')

        scale_grp_id = params.get('scale_grp_id')
        if scale_grp_id and isinstance(scale_grp_id, str):
            scale_grp_id = int(params.get('scale_grp_id'))
        scale_grp_line_id = params.get('scale_grp_line_id')
        if scale_grp_line_id and isinstance(scale_grp_line_id, str):
            scale_grp_line_id = int(params.get('scale_grp_line_id'))
        # print(scale_grp_line_id)

        scale_packing_id = params.get('scale_packing_id')
        if scale_packing_id and isinstance(scale_packing_id, str):
            scale_packing_id = int(params.get('scale_packing_id'))
        scale_tare_weight = float(params.get('scale_tare_weight'))
        scale_basis_weight = float(params.get('scale_basis_weight'))
        scale_net_weight = float(params.get('scale_net_weight'))

        production_shift = params.get('production_shift')
        shift_name = params.get('shift_name')

        user_import_id = params.get('user_import_id')
        if user_import_id and isinstance(user_import_id, str):
            user_import_id = int(params.get('user_import_id'))

        packing_branch_id = params.get('packing_branch_id')
        if packing_branch_id and isinstance(packing_branch_id, str):
            packing_branch_id = int(params.get('packing_branch_id'))

        pallet_weight = float(params.get('pallet_weight'))
        # print(scale_tare_weight, pallet_weight)
        
        lining_bag = str(params.get('lining_bag'))
        if lining_bag == 'True':
            lining_bag = 1
        else:
            lining_bag = 0

        bag_no = params.get('bag_no')
        if bag_no and isinstance(bag_no, str):
            bag_no = int(params.get('bag_no'))

        # product_obj = request.env['product.product'].sudo().search([('id','=', product_id)])
        product_id = request.env['product.product'].sudo().browse(product_id)
        contract_obj = request.env['shipping.instruction'].sudo().search([('name','=', contract)])
        production_obj = request.env['mrp.production'].sudo().search([('id','=',production_id)])
        pending_grp_obj = request.env['mrp.operation.result.produced.product'].sudo().search([('scale_grp_id','=',scale_grp_id)])
        mrp_operation_obj = request.env['mrp.operation.result'].sudo().search([('id','=', pending_grp_obj.operation_result_id.id)])

        if not mrp_operation_obj: # and flag == u'Create'
            vals = {'end_date': dtime.now(),
                    'start_date': dtime.now(),
                    'production_shift': production_shift,
                    'create_uid': user_import_id,
                    'user_import_id': user_import_id,
                    'date_result': dtime.now(),
                    'production_id': production_id,
                    'warehouse_id': warehouse_id}
            result_id = request.env['mrp.operation.result'].with_user(182).create(vals)

            if result_id:
                scale_line = {'product_id': product_id.id,
                            'operation_result_id': result_id.id,
                            'packing_id': scale_packing_id,
                            'weight_scale': scale_basis_weight,
                            'bag_no': bag_no,
                            'tare_weight': scale_tare_weight,
                            'net_weight': scale_net_weight,
                            'scale_grp_id': scale_grp_id,
                            'scale_grp_line_id': scale_grp_line_id,
                            'usr_api_create': user_import_id,
                            'create_date': dtime.now(),
                            'shift_name': shift_name,
                            'packing_branch_id': packing_branch_id,
                            'pallet_weight': pallet_weight,
                            'lining_bag': lining_bag,
                            'scale_no': scale_no,
                            }
                odoo_scale_id = request.env['mrp.operation.result.scale'].with_user(182).create(scale_line)

                tmp = { 'product_id': product_id.id,
                        'zone_id': zone_id,
                        'packing_id': packing_id,
                        'qty_bags': bag_no,
                        'tare_weight': scale_tare_weight + pallet_weight,
                        'product_uom': product_id.uom_id.id,
                        'product_qty': scale_net_weight,
                        'production_weight': scale_basis_weight,
                        'si_id': contract_obj.id,
                        'notes':notes,
                        'production_id':production_id,
                        'pending_grn': pending_grp_name,
                        'operation_result_id': result_id.id,
                        'scale_grp_id': scale_grp_id,
                        'create_uid': user_import_id,
                        }
                result_produced_product_id = request.env['mrp.operation.result.produced.product'].with_user(182).create(tmp)

                result_produced_product_id.create_update_stack_wip()

                mess = {
                    'status_code': "SUD23-200",
                    'message': "Create new item completed!",
                    'mor_name': result_id.name,
                    'operation_result_id': result_id.id,
                    'mrp_result_id': result_produced_product_id.id,
                    'odoo_scale_line_id': odoo_scale_id.id,
                    'produced_product_state': result_produced_product_id.state
                    }
                return mess

        else:
            # Neu co phieu mrp.operation.result thi update thong tin GRP tam
            if flag == u'EditGRP':
                pending_grp_obj.with_user(user_import_id).update({'product_id': product_id.id,
                                        'packing_id': packing_id,
                                        'zone_id': zone_id,
                                        'si_id': contract_obj.id,
                                        'notes':notes,
                                        })
                mess = {
                    'status_code': "SUD23-200",
                    'message': "Update MOR info successfully!",
                    }
            else:
                # TH co phieu MOR va them dong can moi
                get_scale_id = 0
                if not mrp_operation_obj.scale_ids.filtered(lambda x: x.scale_grp_line_id == scale_grp_line_id):
                    scale_line = {'product_id': product_id.id,
                        'operation_result_id': mrp_operation_obj.id,
                        'packing_id': scale_packing_id,
                        'weight_scale': scale_basis_weight,
                        'bag_no': bag_no,
                        'tare_weight': scale_tare_weight,
                        'net_weight': scale_net_weight,
                        'packing_branch_id': packing_branch_id,
                        'pallet_weight': pallet_weight,
                        'lining_bag': lining_bag,
                        'scale_grp_id': scale_grp_id,
                        'scale_grp_line_id': scale_grp_line_id,
                        'usr_api_create': user_import_id,
                        'create_date': dtime.now(),
                        'shift_name': shift_name,
                        'scale_no': scale_no,
                        }
                    odoo_scale_id = request.env['mrp.operation.result.scale'].with_user(182).create(scale_line)
                    get_scale_id = odoo_scale_id.id
                
                else:   # TH co phieu MOR va can lai Bao/Pallet
                    for move in mrp_operation_obj.scale_ids.filtered(lambda x: x.scale_grp_line_id == scale_grp_line_id):
                        move.sudo().update({
                            'packing_id': scale_packing_id,
                            'weight_scale': scale_basis_weight,
                            'bag_no': bag_no,
                            'tare_weight': scale_tare_weight,
                            'net_weight': scale_net_weight,
                            'packing_branch_id': packing_branch_id,
                            'pallet_weight': pallet_weight,
                            'lining_bag': lining_bag,
                            'scale_no': scale_no,
                            })
                        get_scale_id = move.id

                # Cap nhat trong luong tong cho phieu MOR
                grp_gross_weight = grp_net_weight = total_tare_weight = 0.0
                total_qty_bag = 0
                for line in mrp_operation_obj.scale_ids:
                    if line.state_scale in ('cancel'):
                        continue
                    grp_gross_weight += line.weight_scale or 0.0
                    total_qty_bag += line.bag_no or 0
                    total_tare_weight += line.tare_weight + line.pallet_weight or 0.0
                    grp_net_weight += line.weight_scale - (line.tare_weight + line.pallet_weight) or 0.0

                for move in mrp_operation_obj.produced_products.filtered(lambda x: x.product_id == product_id and x.scale_grp_id == scale_grp_id):
                    move.with_user(182).update({
                        'product_id': product_id.id,
                        'zone_id': zone_id,
                        'packing_id': packing_id,
                        'qty_bags': total_qty_bag,
                        'tare_weight': total_tare_weight,
                        'product_uom': product_id.uom_id.id,
                        'product_qty': grp_net_weight,
                        'production_weight': grp_gross_weight,
                        'si_id': contract_obj.id,
                        'notes':notes,
                        })
                mess = {
                    'status_code': "SUD23-200",
                    'message': "Update MOR info successfully!",
                    'mor_name': mrp_operation_obj.name,
                    'operation_result_id': mrp_operation_obj.id,
                    'mrp_result_id': mrp_operation_obj.produced_products.id,
                    'odoo_scale_line_id': get_scale_id,
                    'produced_product_state': mrp_operation_obj.produced_products.state
                    }
                return mess

### POST GRP - ROUTE TO QC ###
    def _input_mrp_production_post_grp_schema(self):
        return {"scale_grp_id": {"type": "integer"},
                "user_import_id": {"type": "integer"},
                "total_row": {"type": "integer"},
                "operation_result_id": {"type": "integer"},
                }
        
    def _output_mrp_production_post_grp_schema(self):
        return {
                'status_code': {"type": "string"},
                'message': {"type": "string"},
                'stock_picking_name': {"type": "string"},
                'stock_picking_state_kcs': {"type": "string"},
                }

    @restapi.method(
        [(["/mrp_operation_result_produced_product/mrp_production_post_grp"], "POST")],
        input_param=restapi.CerberusValidator("_input_mrp_production_post_grp_schema"),
        output_param=restapi.CerberusValidator("_output_mrp_production_post_grp_schema"),
        auth="api_key",
    )

    def mrp_production_post_grp(self, **params):
        user_import_id = params.get('user_import_id')
        if user_import_id and isinstance(user_import_id, str):
            user_import_id = int(params.get('user_import_id'))

        scale_grp_id = params.get('scale_grp_id')
        if scale_grp_id and isinstance(scale_grp_id, str):
            scale_grp_id = int(params.get('scale_grp_id'))
      
        total_row = params.get('total_row')
        if total_row and isinstance(total_row, str):
            total_row = int(params.get('total_row'))

        operation_result_id = params.get('operation_result_id')
        if operation_result_id and isinstance(operation_result_id, str):
            operation_result_id = int(params.get('operation_result_id'))

        operation_result_obj = request.env['mrp.operation.result'].sudo().search([('id','=',operation_result_id)])
        produced_product = request.env['mrp.operation.result.produced.product'].sudo().search([('scale_grp_id','=',scale_grp_id)])
        
        total_odoo_row = 0
        for line in operation_result_obj.scale_ids:
            total_odoo_row += 1

        if total_row == total_odoo_row:
            produced_product.with_user(user_import_id).create_kcs()

            mess = {
                    'status_code': "SUD23-200",
                    'message': 'Post MOR to KCS successfully!',
                    'stock_picking_name': produced_product.picking_id.name,
                    'stock_picking_state_kcs': produced_product.picking_id.state_kcs
                    }
            return mess
        else:
            mess = {
                    'status_code': "SUD23-200",
                    'message': 'Total line of weight scale different Odoo scale line!',
                    }
            return mess
        
### CANCEL GRP TEMP ###
    def _input_cancel_grp_temp_schema(self):
        return {"mrp_result_id": {"type": "integer"}}
        
    def _output_cancel_grp_temp_schema(self):
        return {
                'status_code': {"type": "string"},
                'message': {"type": "string"},
                'mrp_state': {"type": "string"},
                'mrp_result_id': {"type": "integer"},
                }

    @restapi.method(
        [(["/mrp_operation_result_produced_product/cancel_grp_temp"], "POST")],
        input_param=restapi.CerberusValidator("_input_cancel_grp_temp_schema"),
        output_param=restapi.CerberusValidator("_output_cancel_grp_temp_schema"),
        auth="api_key",
    )

    def cancel_grp_temp(self, **params):
        mrp_result_id = params.get('mrp_result_id')
        if mrp_result_id and isinstance(mrp_result_id, str):
            mrp_result_id = int(params.get('mrp_result_id'))

        pending_grp_obj = request.env['mrp.operation.result.produced.product'].sudo().search([('id','=',mrp_result_id)])
        if pending_grp_obj:
            pending_grp_obj.button_cancel()

            mess = {
                    'status_code': "SUD23-200",
                    'message': 'MOR cancel successfully!',
                    'mrp_state': pending_grp_obj.state,
                    'mrp_result_id': pending_grp_obj.id
                    }
            return mess
        
### GET Request Materials Line List ###
    @restapi.method(
        [(["/request_materials_line/list"], "GET")],
        input_param=restapi.Datamodel("request_materials_line.search.param"),
        output_param=restapi.Datamodel("request_materials_line.short.info", is_list=True),
        auth="api_key",
    )
    def request_materials_line_list(self, request_materials_line_param):
        """
        Search for request_materials_line List
        @param: Input ID or Name or Warehouse ID
        @return: Return a list of request_materials_line follow parameters
        """
        domain = [('create_date','>=',((dtime.today()-relativedelta(months=1)).strftime('%Y-%m-%d'))),
                  ('request_id.production_id.state','=','confirmed'),('stack_id.zone_id.name','!=','Hopper')]
        if request_materials_line_param.pmr_name:
            domain.append(("request_id.name", "like", request_materials_line_param.pmr_name))
        if request_materials_line_param.rml_id:
            domain.append(("id", "=", request_materials_line_param.rml_id))
        if request_materials_line_param.warehouse_id and isinstance(request_materials_line_param.warehouse_id, str):
            array = [int(x) for x in request_materials_line_param.warehouse_id.split(",")]
            domain.append(("request_id.production_id.warehouse_id", "in", array))
        res = []
        RequestMaterialsLineShortInfo = self.env.datamodels["request_materials_line.short.info"]
        for p in self.env["request.materials.line"].search(domain):
            res.append(RequestMaterialsLineShortInfo(production_id=p.request_id.production_id.id, mrp_name=p.request_id.production_id.name, rml_id=p.id, 
                                              product_id=p.product_id, default_code=p.product_id.default_code, stack_id=p.stack_id, 
                                              stack_name=p.stack_id.name, packing_id=p.packing_id, bag_no=p.bag_no, qty_stack=p.stack_id.init_qty,
                                              product_qty=p.product_qty, issue_qty=p.basis_qty, to_be_issue=p.product_qty-p.basis_qty, pmr_id=p.request_id.id, pmr_name=p.request_id.name,
                                              zone_id=p.stack_id.zone_id, zone_name=p.stack_id.zone_id.name, rml_state=p.state,
                                              create_date=str(p['create_date'])))
        return res

### GET GIP List ###
    @restapi.method(
        [(["/stock_move_line/get_gip_list"], "GET")],
        input_param=restapi.Datamodel("stock_move_line.search.param"),
        output_param=restapi.Datamodel("stock_move_line.short.info", is_list=True),
        auth="api_key",
    )
    def stock_move_line_list(self, stock_move_line_param):
        """
        Search for stock_move_line List
        @param: Input ID or Name or Warehouse ID
        @return: Return a list of stock_move_line follow parameters
        """
        wh_array = ''
        sp_name = ''
        sp_id = ''
        if stock_move_line_param.warehouse_id and isinstance(stock_move_line_param.warehouse_id, str):
            wh_array = '= ' + str(stock_move_line_param.warehouse_id) if len(stock_move_line_param.warehouse_id.split(",")) == 1 else 'in ' + str(tuple([int(x) for x in stock_move_line_param.warehouse_id.split(",")]))
        if stock_move_line_param.name and isinstance(stock_move_line_param.name, str):
            sp_name = ' and sp.name = %s '%(stock_move_line_param.name)
        if stock_move_line_param.sp_id and isinstance(stock_move_line_param.sp_id, str):
            sp_id = ' and sp.id = %s '%(stock_move_line_param.sp_id)
                        
        sql = '''SELECT sp.id sp_id, sp.name, sp.lot_id, sl.name stack_name, sp.production_id, mrp.name mrp_name, sml.init_qty, sml.bag_no, 
                sp.packing_id, sp.state_kcs, rml.id rml_id, rm.id rm_id, rm.name rm_name, sp.state sp_state, sml.tare_weight,
                sml.gross_weight, sml.product_id, sml.scale_gip_id
                FROM stock_move_line sml
                JOIN stock_picking sp ON sp.id = sml.picking_id
                JOIN picking_request_move_ref refs on sp.id = refs.request_id 
                JOIN request_materials_line rml on rml.id = refs.picking_id
                JOIN request_materials rm on rm.id = rml.request_id
                JOIN mrp_production mrp on mrp.id = rm.production_id
                JOIN stock_lot sl on sl.id = sml.lot_id
                WHERE sp.picking_type_code='production_out' AND sml.scale_gip_id > 0 AND
                sml.warehouse_id %s %s %s
                AND mrp.create_date >= date_trunc('month', CURRENT_DATE - INTERVAL '1 month'); 
                '''%(wh_array,sp_name,sp_id)
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        # print(result)
        res = []
        StackShortInfo = self.env.datamodels["stock_move_line.short.info"]
        for p in result:
            res.append(StackShortInfo(sp_id=p['sp_id'], name=p['name'], lot_id=p['lot_id'], stack_name=p['stack_name'], 
                                      production_id=p['production_id'], mrp_name=p['mrp_name'], init_qty=p['init_qty'],
                                      bag_no=p['bag_no'], packing_id=str(p['packing_id']), state_kcs=p['state_kcs'],
                                      rml_id=p['rml_id'], rm_id=p['rm_id'], rm_name=p['rm_name'], 
                                      sp_state=p['sp_state'], tare_weight=p['tare_weight'], gross_weight=p['gross_weight'], 
                                      product_id=p['product_id'], scale_gip_id=p['scale_gip_id']))
        return res
    # def stock_move_line_list(self, stock_move_line_param):
    #     """
    #     Search for stock_move_line List
    #     @param: Input ID or Name or Warehouse ID
    #     @return: Return a list of stock_move_line follow parameters
    #     """
    #     domain = [('request_id.production_id.create_date','>=',((dtime.today()-relativedelta(months=1)).strftime('%Y-%m-%d'))),
    #               ('picking_ids.picking_type_code','=','production_out')]
    #     if stock_move_line_param.name:
    #         domain.append(("picking_ids.name", "like", stock_move_line_param.name))
    #     if stock_move_line_param.sp_id:
    #         domain.append(("picking_ids.id", "=", stock_move_line_param.sp_id))
    #     if stock_move_line_param.warehouse_id and isinstance(stock_move_line_param.warehouse_id, str):
    #         array = [int(x) for x in stock_move_line_param.warehouse_id.split(",")]
    #         domain.append(("warehouse_id", "in", array))
    #     res = []
    #     StockMoveLineShortInfo = self.env.datamodels["stock_move_line.short.info"]
    #     for p in self.env["request.materials.line"].search(domain):
    #         res.append(StockMoveLineShortInfo(sp_id=p.picking_ids.id, name=p.picking_ids.name, lot_id=p.stack_id, stack_name=p.stack_id.name,
    #                                                 production_id=p.request_id.production_id, mrp_name=p.request_id.production_id.name, init_qty=p.basis_qty, bag_no=p.bag_no,
    #                                                 packing_id=p.packing_id, state_kcs=p.picking_ids.state_kcs, rml_id=p.id
    #                                                 ))
    #     # for p in self.env["stock.move.line"].search(domain):
    #     #     res.append(StockMoveLineShortInfo(sp_id=p.picking_id, name=p.picking_id.name, lot_id=p.picking_id.lot_id, stack_name=p.lot_id.name,
    #     #                                             production_id=p.production_id, mrp_name=p.production_id.name, init_qty=p.init_qty, bag_no=p.bag_no,
    #     #                                             packing_id=p.packing_id, state_kcs=p.picking_id.state_kcs, rml_id=p.picking_id.request_line_ids
    #     #                                             ))
    #     return res

### CREATE GIP PICKING ###
    def _input_create_update_gip_schema(self):
        return {"request_materials_line_id": {"type": "integer"},
                "product_id": {"type": "integer"},
                "scale_packing_id": {"type": "integer"},
                "scale_basis_weight": {"type": "float"},
                "bag_no": {"type": "integer"},
                "scale_tare_weight": {"type": "float"},
                "scale_net_weight": {"type": "float"},
                "scale_gip_id": {"type": "integer"},
                "scale_gip_line_id": {"type": "integer"},
                "user_import_id": {"type": "integer"},
                "shift_name": {"type": "string"},
                "packing_branch_id": {"type": "string"},
                "pallet_weight": {"type": "float"},
                "lining_bag": {"type": "string"},
                "picking_id": {"type": "integer"},
                "warehouse_id": {"type": "integer"},
                "old_weight": {"type": "float"},
                "bag_code": {"type": "string"},
                "scale_no": {"type": "string"},
                }
        
    def _output_create_update_gip_schema(self):
        return {
                'status_code': {"type": "string"},
                'message': {"type": "string"},
                'stock_picking_name': {"type": "string"},
                'stock_picking_id': {"type": "integer"},
                'stock_picking_state': {"type": "string"},
                'stock_move_line_id': {"type": "integer"},
                'odoo_scale_line_id': {"type": "integer"},
                }

    @restapi.method(
        [(["/mrp_operation_result_scale/create_update_gip"], "POST")],
        input_param=restapi.CerberusValidator("_input_create_update_gip_schema"),
        output_param=restapi.CerberusValidator("_output_create_update_gip_schema"),
        auth="api_key",
    )

    def create_update_gip(self, **params):
        scale_no = params.get('scale_no')
        warehouse_id = params.get('warehouse_id')
        if warehouse_id and isinstance(warehouse_id, str):
            warehouse_id = int(params.get('warehouse_id'))

        request_materials_line_id = params.get('request_materials_line_id')
        if request_materials_line_id and isinstance(request_materials_line_id, str):
            request_materials_line_id = int(params.get('request_materials_line_id'))
        
        product_id = params.get('product_id')
        if product_id and isinstance(product_id, str):
            product_id = int(params.get('product_id'))
        scale_packing_id = params.get('scale_packing_id')
        if scale_packing_id and isinstance(scale_packing_id, str):
            scale_packing_id = int(params.get('scale_packing_id'))
       
        scale_basis_weight = float(params.get('scale_basis_weight'))
       
        bag_no = params.get('bag_no')
        if bag_no and isinstance(bag_no, str):
            bag_no = int(params.get('bag_no'))
        
        scale_tare_weight = float(params.get('scale_tare_weight'))
        scale_net_weight = float(params.get('scale_net_weight'))

        scale_gip_id = params.get('scale_gip_id')
        if scale_gip_id and isinstance(scale_gip_id, str):
            scale_gip_id = int(params.get('scale_gip_id'))
        scale_gip_line_id = params.get('scale_gip_line_id')
        if scale_gip_line_id and isinstance(scale_gip_line_id, str):
            scale_gip_line_id = int(params.get('scale_gip_line_id'))

        user_import_id = params.get('user_import_id')
        if user_import_id and isinstance(user_import_id, str):
            user_import_id = int(params.get('user_import_id'))

        shift_name = params.get('shift_name')

        packing_branch_id = params.get('packing_branch_id')
        if packing_branch_id and isinstance(packing_branch_id, str):
            packing_branch_id = int(params.get('packing_branch_id'))

        pallet_weight = float(params.get('pallet_weight'))
        
        old_weight = float(params.get('old_weight'))
        bag_code = params.get('bag_code')
        
        lining_bag = str(params.get('lining_bag'))
        if lining_bag == 'True':
            lining_bag = 1
        else:
            lining_bag = 0

        picking_id = params.get('picking_id')
        if picking_id and isinstance(picking_id, str):
            picking_id = int(params.get('picking_id'))

        product_id = request.env['product.product'].sudo().browse(product_id)

        stock_picking_obj = request.env['stock.picking'].sudo().search([('id','=',picking_id)])
        if not stock_picking_obj:
            result_obj = request.env['request.materials.line'].sudo().browse(request_materials_line_id)
            # Check MRP state before get weight_scale
            if result_obj.request_id.production_id.state == 'done':
                mess = {
                    'status_code': 'SUD23-204',
                    'message': '''%s has been Done, can't create!''' %(result_obj.request_id.production_id.name),
                    }
                return mess

            warehouse_id = result_obj.request_id.warehouse_id or request.env['stock.warehouse'].sudo().search([('id', '=', warehouse_id)], limit=1)
            
            location_id = False
            if result_obj and result_obj.stack_id:
                location_id =  warehouse_id.wh_raw_material_loc_id
            crop_id = request.env['ned.crop'].sudo().search([('state', '=', 'current')], limit=1)
            
            vals = {
                'name': '/', 
                'picking_type_id': warehouse_id.production_out_type_id.id, 
                'date_done': dtime.now(), 
                'partner_id': False, 
                'crop_id':crop_id.id,
                'location_id': location_id and location_id.id or False, 
                'production_id': result_obj.request_id.production_id.id or False,  
                'location_dest_id': warehouse_id.production_out_type_id.default_location_dest_id.id or False,
                'request_materials_id':result_obj.request_id.id,
                'warehouse_id':warehouse_id.id,
                'state':'draft',
                'state_kcs': 'waiting',
                }  
            create_picking = request.env['stock.picking'].with_user(182).create(vals)
            result_obj.sudo().write({'picking_ids': [(4, create_picking.id)]})
            product_uom_qty = scale_net_weight - (scale_net_weight * abs(result_obj.stack_id.avg_deduction/100)) or 0.0
            spl_val ={
                'picking_id': create_picking.id or False, 
                'product_uom_id': result_obj.product_id.uom_id.id or False,
                'init_qty':scale_net_weight or 0.0,
                'gross_weight': scale_basis_weight,
                'qty_done': product_uom_qty or 0.0, 
                'reserved_uom_qty':product_uom_qty or 0.0,
                'price_unit': 0.0,
                'picking_type_id': create_picking.picking_type_id.id or False,
                'location_id': create_picking.location_id.id or False,
                'location_dest_id': create_picking.location_dest_id.id or False,
                'company_id': request.env.user.company_id.id, 
                'zone_id': result_obj.stack_id.zone_id.id or False, 
                'product_id': result_obj.product_id.id or False,
                'date': create_picking.date_done or False, 
                'currency_id': False,
                'state':'draft', 
                'warehouse_id': create_picking.warehouse_id.id or False,
                'lot_id':result_obj.stack_id.id,
                'production_id': create_picking.production_id.id or False,
                'packing_id':result_obj.stack_id and result_obj.stack_id.packing_id and result_obj.stack_id.packing_id.id or False,
                'bag_no':bag_no,
                'tare_weight': scale_tare_weight + pallet_weight,
                'scale_gip_id': scale_gip_id,
                'material_id': result_obj.request_id.production_id.id or False,
                }
            move_id = request.env['stock.move.line'].with_user(182).create(spl_val)

            scale_line = {'product_id': product_id.id,
                'picking_scale_id': create_picking.id,
                'packing_id': scale_packing_id,
                'weight_scale': scale_basis_weight,
                'bag_no': bag_no,
                'tare_weight': scale_tare_weight,
                'net_weight': scale_net_weight,
                'old_weight': old_weight,
                'bag_code': bag_code,
                'scale_gip_id': scale_gip_id,
                'scale_gip_line_id': scale_gip_line_id,
                'usr_api_create': user_import_id,
                'create_date': dtime.now(),
                'shift_name': shift_name,
                'packing_branch_id': packing_branch_id,
                'pallet_weight': pallet_weight,
                'lining_bag': lining_bag,
                'scale_no': scale_no,
                }
            odoo_scale_id = request.env['mrp.operation.result.scale'].with_user(182).create(scale_line)

            mess = {
                'status_code': 'SUD23-200',
                'message': '%s created successfully!' %(create_picking.name),
                'stock_picking_name': create_picking.name,
                'stock_picking_id': create_picking.id,
                'stock_picking_state': create_picking.state,
                'stock_move_line_id': create_picking.move_line_ids_without_package.id,
                'odoo_scale_line_id': odoo_scale_id.id,
                }
            return mess

        else:
            # Check MRP state before get weight_scale
            if stock_picking_obj.production_id.state == 'done':
                mess = {
                    'status_code': 'SUD23-204',
                    'message': '''%s has been Done, can't add new scale_line!''' %(stock_picking_obj.production_id.name),
                    }
                return mess

            odoo_scale_line_id = 0
            # TH co phieu GIP va them dong can moi
            if not stock_picking_obj.scale_ids.filtered(lambda x: x.scale_gip_line_id == scale_gip_line_id):
                scale_line = {'product_id': product_id.id,
                    'picking_scale_id': stock_picking_obj.id,
                    'packing_id': scale_packing_id,
                    'weight_scale': scale_basis_weight,
                    'bag_no': bag_no,
                    'tare_weight': scale_tare_weight,
                    'net_weight': scale_net_weight,
                    'old_weight': old_weight,
                    'bag_code': bag_code,
                    'scale_gip_id': scale_gip_id,
                    'scale_gip_line_id': scale_gip_line_id,
                    'usr_api_create': user_import_id,
                    'create_date': dtime.now(),
                    'shift_name': shift_name,
                    'packing_branch_id': packing_branch_id,
                    'pallet_weight': pallet_weight,
                    'lining_bag': lining_bag,
                    'scale_no': scale_no,
                    }
                odoo_scale_id = request.env['mrp.operation.result.scale'].with_user(182).create(scale_line)
                odoo_scale_line_id = odoo_scale_id.id
            # TH co phieu GIP va can lai Bao/Pallet
            else:
                for move in stock_picking_obj.scale_ids.filtered(lambda x: x.scale_gip_line_id == scale_gip_line_id):
                    move.sudo().update({
                        'packing_id': scale_packing_id,
                        'weight_scale': scale_basis_weight,
                        'bag_no': bag_no,
                        'tare_weight': scale_tare_weight,
                        'net_weight': scale_net_weight,
                        'old_weight': old_weight,
                        'bag_code': bag_code,
                        'packing_branch_id': packing_branch_id,
                        'pallet_weight': pallet_weight,
                        'lining_bag': lining_bag,
                        'scale_no': scale_no,
                        })
                    odoo_scale_line_id = move.id

            # Cap nhat trong luong tong cho phieu GIP
            gip_gross_weight = gip_net_weight = total_tare_weight = product_uom_qty = 0.0
            total_qty_bag = 0
            for line in stock_picking_obj.scale_ids:
                if line.state_scale in ('cancel'):
                    continue
                gip_gross_weight += line.weight_scale or 0.0
                total_qty_bag += line.bag_no or 0
                total_tare_weight += line.tare_weight + line.pallet_weight or 0.0
                gip_net_weight += line.weight_scale - (line.tare_weight + line.pallet_weight) or 0.0
                
            for move in stock_picking_obj.move_line_ids_without_package.filtered(lambda x: x.product_id == product_id and x.scale_gip_id == scale_gip_id):
                product_uom_qty = gip_net_weight - (gip_net_weight * abs(move.lot_id.avg_deduction/100)) or 0.0
                move.with_user(182).update({
                                    'gross_weight': gip_gross_weight,
                                    'init_qty': gip_net_weight,
                                    'bag_no': total_qty_bag,
                                    'tare_weight': total_tare_weight,
                                    'qty_done': product_uom_qty or 0.0, 
                                    'reserved_uom_qty':product_uom_qty or 0.0,
                              })
            mess = {
                'status_code': 'SUD23-200',
                'message': '%s add new scale_line successfully!' %(stock_picking_obj.name),
                'stock_picking_name': stock_picking_obj.name,
                'stock_picking_id': stock_picking_obj.id,
                'stock_picking_state': stock_picking_obj.state,
                'stock_move_line_id': stock_picking_obj.move_line_ids_without_package.id,
                'odoo_scale_line_id': odoo_scale_line_id,
                }
            return mess
        
### POST GIP - ROUTE TO QC ###
    def _input_gip_picking_route_qc_schema(self):
        return {"picking_id": {"type": "integer"},
                "user_import_id": {"type": "integer"},
                "total_row": {"type": "integer"},
                }
        
    def _output_gip_picking_route_qc_schema(self):
        return {
                'status_code': {"type": "string"},
                'message': {"type": "string"},
                'stock_picking_state': {"type": "string"},
                'stock_picking_state_kcs': {"type": "string"},
                }

    @restapi.method(
        [(["/stock_picking/gip_picking_route_qc"], "POST")],
        input_param=restapi.CerberusValidator("_input_gip_picking_route_qc_schema"),
        output_param=restapi.CerberusValidator("_output_gip_picking_route_qc_schema"),
        auth="api_key",
    )

    def gip_picking_route_qc(self, **params):
        user_import_id = params.get('user_import_id')
        if user_import_id and isinstance(user_import_id, str):
            user_import_id = int(params.get('user_import_id'))

        picking_id = params.get('picking_id')
        if picking_id and isinstance(picking_id, str):
            picking_id = int(params.get('picking_id'))

        total_row = params.get('total_row')
        if total_row and isinstance(total_row, str):
            total_row = int(params.get('total_row'))

        stock_picking_obj = request.env['stock.picking'].sudo().search([('id','=',picking_id)])

        total_odoo_row = 0
        for line in stock_picking_obj.scale_ids:
            total_odoo_row += 1

        if total_row == total_odoo_row:
            stock_picking_obj.button_qc_assigned()
            stock_picking_obj.button_sd_validate()
            stock_picking_obj.with_user(182).update({'state_kcs': 'draft'})
            mess = {
                'status_code': 'SUD23-200',
                'message': 'Route GIP receipt to KCS successfully!',
                'stock_picking_state': stock_picking_obj.state,
                'stock_picking_state_kcs': stock_picking_obj.state_kcs
                }
            return mess
        else:
            mess = {
                'status_code': 'SUD23-204',
                'message': 'Total line of weight scale different Odoo scale line!',
                }
            return mess

### CANCEL GIP DRAFT ###
    def _input_cancel_gip_draft_schema(self):
        return {"picking_id": {"type": "integer"}}
        
    def _output_cancel_gip_draft_schema(self):
        return {
                'status_code': {"type": "string"},
                'message': {"type": "string"},
                'picking_gip_state': {"type": "string"},
                'picking_gip_id': {"type": "integer"},
                }

    @restapi.method(
        [(["/stock_picking/cancel_gip_draft"], "POST")],
        input_param=restapi.CerberusValidator("_input_cancel_gip_draft_schema"),
        output_param=restapi.CerberusValidator("_output_cancel_gip_draft_schema"),
        auth="api_key",
    )

    def cancel_gip_draft(self, **params):
        picking_id = params.get('picking_id')
        if picking_id and isinstance(picking_id, str):
            picking_id = int(params.get('picking_id'))

        stock_picking_obj = request.env['stock.picking'].sudo().search([('id','=',picking_id)])
        if stock_picking_obj:
            stock_picking_obj.action_cancel()

            mess = {
                    'status_code': "SUD23-200",
                    'message': 'GIP cancel successfully!',
                    'picking_gip_state': stock_picking_obj.state,
                    'picking_gip_id': stock_picking_obj.id
                    }
            return mess
        
### CANCEL GIP & GRP SCALE LINE ###
    def _input_cancel_scale_line_schema(self):
        return {"user_import_id": {"type": "integer"},
                "scale_line_id": {"type": "integer"},
                "picking_id": {"type": "integer"},
                "operation_result_id": {"type": "integer"}}
        
    def _output_cancel_scale_line_schema(self):
        return {
                'status_code': {"type": "string"},
                'message': {"type": "string"},
                }

    @restapi.method(
        [(["/mrp_operation_result_scale/cancel_scale_line"], "POST")],
        input_param=restapi.CerberusValidator("_input_cancel_scale_line_schema"),
        output_param=restapi.CerberusValidator("_output_cancel_scale_line_schema"),
        auth="api_key",
    )

    def cancel_scale_line(self, **params):
        user_import_id = params.get('user_import_id')
        if user_import_id and isinstance(user_import_id, str):
            user_import_id = int(params.get('user_import_id'))

        scale_line_id = params.get('scale_line_id')
        if scale_line_id and isinstance(scale_line_id, str):
            scale_line_id = int(params.get('scale_line_id'))

        picking_id = params.get('picking_id')
        if picking_id and isinstance(picking_id, str):
            picking_id = int(params.get('picking_id'))

        stock_picking_obj = request.env['stock.picking'].sudo().search([('id','=',picking_id)])
        # print(stock_picking_obj.id)

        operation_result_id = params.get('operation_result_id')
        if operation_result_id and isinstance(operation_result_id, str):
            operation_result_id = int(params.get('operation_result_id'))

        mrp_operation_obj = request.env['mrp.operation.result'].sudo().search([('id','=', operation_result_id)])
        # print(mrp_operation_obj.id)

        if stock_picking_obj:
            scale_line_obj = request.env['mrp.operation.result.scale'].sudo().search([('scale_gip_line_id','=',scale_line_id)])
            scale_line_obj.with_user(user_import_id).update({'state_scale': 'cancel',})

            # Cap nhat trong luong tong cho phieu GIP
            gip_gross_weight = gip_net_weight = total_tare_weight = product_uom_qty = 0.0
            total_qty_bag = 0
            for line in stock_picking_obj.scale_ids:
                if line.state_scale in ('cancel'):
                    continue
                gip_gross_weight += line.weight_scale or 0.0
                total_qty_bag += line.bag_no or 0
                total_tare_weight += line.tare_weight + line.pallet_weight or 0.0
                gip_net_weight += line.weight_scale - (line.tare_weight + line.pallet_weight) or 0.0
                
            for move in stock_picking_obj.move_line_ids_without_package.filtered(lambda x: x.scale_gip_id == scale_line_obj.scale_gip_id):
                product_uom_qty = gip_net_weight - (gip_net_weight * abs(move.lot_id.avg_deduction/100)) or 0.0
                move.with_user(user_import_id).update({
                                    'gross_weight': gip_gross_weight,
                                    'init_qty': gip_net_weight,
                                    'bag_no': total_qty_bag,
                                    'tare_weight': total_tare_weight,
                                    'qty_done': product_uom_qty or 0.0, 
                                    'reserved_uom_qty':product_uom_qty or 0.0,
                              })

                mess = {
                        'status_code': 'SUD23-200',
                        'message': 'Cancel GIP scale line successfully!',
                        }
                return mess

        if mrp_operation_obj:
            scale_line_obj = request.env['mrp.operation.result.scale'].sudo().search([('scale_grp_line_id','=',scale_line_id)])
            scale_line_obj.with_user(user_import_id).update({'state_scale': 'cancel',})

            # Cap nhat trong luong tong cho phieu GRP
            grp_gross_weight = grp_net_weight = total_tare_weight = 0.0
            total_qty_bag = 0
            for line in mrp_operation_obj.scale_ids:
                if line.state_scale in ('cancel'):
                    continue
                grp_gross_weight += line.weight_scale or 0.0
                total_qty_bag += line.bag_no or 0
                total_tare_weight += line.tare_weight + line.pallet_weight or 0.0
                grp_net_weight += line.weight_scale - (line.tare_weight + line.pallet_weight) or 0.0
            # print(grp_gross_weight, total_qty_bag, total_tare_weight, grp_net_weight)
            # print(mrp_operation_obj.produced_products.id)
            for move in mrp_operation_obj.produced_products.filtered(lambda x: x.scale_grp_id == scale_line_obj.scale_grp_id):
                # print(move.stack_wip_id)
                move.with_user(user_import_id).update({
                    'qty_bags': total_qty_bag,
                    'tare_weight': total_tare_weight,
                    'product_qty': grp_net_weight,
                    'production_weight': grp_gross_weight,
                    })                

                mess = {
                        'status_code': 'SUD23-200',
                        'message': 'Cancel GRP scale line successfully!',
                        }
                return mess
