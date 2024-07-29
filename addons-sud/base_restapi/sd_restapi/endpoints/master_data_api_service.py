# -*- coding: utf-8 -*-

from marshmallow import fields
from werkzeug.exceptions import BadRequest

from odoo.addons.base_rest import restapi
from odoo.addons.component.core import Component
from odoo.addons.datamodel.core import Datamodel

from odoo.http import request

# Datamodel INPUT
class MasterSearchParam(Datamodel):
    _name = "masterdata.search.param"

    id = fields.Integer(required=False, allow_none=False)
    name = fields.String(required=False, allow_none=False)
    
class PartnerSearchParam(Datamodel):
    _name = "partner.search.param"
    _inherit = "masterdata.search.param"

class ProductSearchParam(Datamodel):
    _name = "product.search.param"
    
    id = fields.Integer(required=False, allow_none=False)
    # default_code = fields.String(required=False, allow_none=False)
    display_wb = fields.String(required=False, allow_none=False)
    
class PackingSearchParam(Datamodel):
    _name = "packing.search.param"
    _inherit = "masterdata.search.param"
    
class ZoneSearchParam(Datamodel):
    _name = "zone.search.param"
    _inherit = "masterdata.search.param"
    
    warehouse_id = fields.String(load_default="1,22")   #fields.Int(load_default=1)
    # warehouse_id_list = fields.String(load_default="1,22")

class StackSearchParam(Datamodel):
    _name = "stack.search.param"
    _inherit = "masterdata.search.param"
    
    warehouse_id = fields.String(load_default="1,22")
    zone_id = fields.String()

class UserSearchParam(Datamodel):
    _name = "user.search.param"
    # _inherit = "masterdata.search.param"
    
    id = fields.Integer(required=False, allow_none=False)
    name = fields.String()
    email = fields.String(load_default="all")

    
###========= Datamodel OUTPUT =========###
class MasterShortInfo(Datamodel):
    _name = "masterdata.short.info"

    id = fields.Integer(required=True, allow_none=False)
    name = fields.String(required=True, allow_none=False)

class PartnerShortInfo(Datamodel):
    _name = "partner.short.info"
    _inherit = "masterdata.short.info"

    short_name = fields.String()

class ProductShortInfo(Datamodel):
    _name = "product.short.info"

    id = fields.Integer(required=True, allow_none=False)
    default_code = fields.String()
    display_wb = fields.String()
    
class PackingShortInfo(Datamodel):
    _name = "packing.short.info"
    _inherit = "masterdata.short.info"

    tare_weight = fields.Float(load_default=0.0)

class ZoneShortInfo(Datamodel):
    _name = "zone.short.info"
    _inherit = "masterdata.short.info"

    warehouse_id = fields.Integer(load_default=1)

class StackShortInfo(Datamodel):
    _name = "stack.short.info"
    _inherit = "masterdata.short.info"

    warehouse_id = fields.Integer()
    init_qty = fields.Float(load_default=0.0)
    zone_id = fields.Integer()
    zone_name = fields.String()
    create_date = fields.DateTime()
    product_id = fields.Int()

class UserShortInfo(Datamodel):
    _name = "user.short.info"
    _inherit = "masterdata.short.info"

    email = fields.String()

### ========================================================= ###
class MasterDataApiService(Component):
    _inherit = "base.rest.service"
    _name = "masterdata.api.service"
    _usage = "masterdata"
    _collection = "sucden.restapi.services"
    _description = """
        Master Data New API Services
        Services developed with the new api provided by IT Team - SUCDEN VN
    """
    ### Partner ###
    @restapi.method(
        [(["/res_partner/<int:id>"], "GET")],
        output_param=restapi.CerberusValidator("_get_partners_schema"),
        auth="api_key",
    )
    def get_partners(self, _id):
        return {"id": self.env["res.partner"].browse(_id).id,
                "name": self.env["res.partner"].browse(_id).name,
                "short_name": self.env["res.partner"].browse(_id).shortname}

    def _get_partners_schema(self):
        return {"id": {"type": "integer", "required": True},
                "name": {"type": "string", "required": True},
                "short_name": {}}

    @restapi.method(
        [(["/res_partner/list"], "GET")],
        output_param=restapi.CerberusListValidator("_get_partners_schema"),
        auth="api_key",
    )
    def partners_list(self):
        partners = self.env["res.partner"].search([("is_supplier_coffee", "=", "True"),("is_customer_coffee", "=", "True"),("shortname", "!=", False)])
        return [{"id": p.id, "name": p.name, "short_name": p.shortname} for p in partners]

    @restapi.method(
        [(["/res_partner/search"], "GET")],
        input_param=restapi.Datamodel("partner.search.param"),
        output_param=restapi.Datamodel("partner.short.info", is_list=True),
        auth="api_key",
    )
    def partners_search(self, partner_search_param):
        """
        Search for partners
        @param: Input ID or Word in Name
        @return: Return a list of partner-follow parameters
        """
        
        domain = [("shortname", "!=", False)]
        if partner_search_param.name:
            domain.append(("name", "like", partner_search_param.name))
        if partner_search_param.id:
            domain.append(("id", "=", partner_search_param.id))
        res = []
        PartnerSearchParam = self.env.datamodels["partner.short.info"]
        for p in self.env["res.partner"].search(domain):
            res.append(PartnerSearchParam(id=p.id, name=p.name, short_name=p.shortname))
        return res
    
    ### Products ###
    @restapi.method(
        [(["/product_product/<int:id>"], "GET")],
        output_param=restapi.CerberusValidator("_get_products_schema"),
        auth="api_key",
    )
    
    def get_products(self, _id):
        return {"id": self.env["product.product"].browse(_id).id,
                "default_code": self.env["product.product"].browse(_id).default_code,
                "display_wb": self.env["product.product"].browse(_id).display_wb}

    def _get_products_schema(self):
        return {"id": {"type": "integer", "required": True},
                "default_code": {"type": "string", "required": True},
                "display_wb": {}}

    @restapi.method(
        [(["/product_product/list"], "GET")],
        output_param=restapi.CerberusListValidator("_get_products_schema"),
        auth="api_key",
    )
    def products_list(self):
        products = self.env["product.product"].search([("default_code", "!=", False)])
        return [{"id": p.id, "default_code": p.default_code, "display_wb": p.display_wb} for p in products]

    @restapi.method(
        [(["/product_product/search"], "GET")],
        input_param=restapi.Datamodel("product.search.param"),
        output_param=restapi.Datamodel("product.short.info", is_list=True),
        auth="api_key",
    )
    def producs_search(self, product_search_param):
        """
        Search for Producs
        @param: Input ID or Word in Name
        @return: Return a list of Producs-follow parameters
        """
        domain = [("default_code", "!=", False)]
        if product_search_param.display_wb:
            domain.append(("display_wb", "like", product_search_param.display_wb))
        if product_search_param.id:
            domain.append(("id", "=", product_search_param.id))
        res = []
        ProductShortInfo = self.env.datamodels["product.short.info"]
        for p in self.env["product.product"].search(domain):
            res.append(ProductShortInfo(id=p.id, default_code=p.default_code, display_wb=p.display_wb))
        return res
    
    # Packing
    @restapi.method(
        [(["/ned_packing/<int:id>"], "GET")],
        output_param=restapi.CerberusValidator("_get_packing_schema"),
        auth="api_key",
    )

    def get_packing(self, _id):
        return {"id": self.env["ned.packing"].browse(_id).id,
                "name": self.env["ned.packing"].browse(_id).name}

    def _get_packing_schema(self):
        return {"id": {"type": "integer"},
                "name": {"type": "string"},
                "tare_weight": {"type": "float"}}

    @restapi.method(
        [(["/ned_packing/list"], "GET")],
        output_param=restapi.CerberusListValidator("_get_packing_schema"),
        auth="api_key",
    )
    def packing_list(self):
        packings = self.env["ned.packing"].search([("active", "=", True)])
        return [{"id": p.id, "name": p.name, "tare_weight": p.tare_weight} for p in packings]
    
    @restapi.method(
        [(["/ned_packing/search"], "GET")],
        input_param=restapi.Datamodel("packing.search.param"),
        output_param=restapi.Datamodel("packing.short.info", is_list=True),
        auth="api_key",
    )
    def packing_search(self, packing_search_param):
        """
        Search for Packing
        @param: Input ID or Word in Name
        @return: Return a list of Packing-follow parameters
        """
        domain = []
        if packing_search_param.name:
            domain.append(("name", "like", packing_search_param.name))
        if packing_search_param.id:
            domain.append(("id", "=", packing_search_param.id))
        res = []
        PackingShortInfo = self.env.datamodels["packing.short.info"]
        for p in self.env["ned.packing"].search(domain):
            res.append(PackingShortInfo(id=p.id, name=p.name, tare_weight=p.tare_weight))
        return res

    @restapi.method(
        [(["/ned_packing/<int:id>/change_name"], "POST")],
        input_param=restapi.CerberusValidator("_get_packing_schema"),
        auth="api_key",
    )
    def update_name(self, _id, **params):
        print(params)
        if params['name']:
            packing = self.env["ned.packing"].browse(_id)
            packing.write({"name": params['name']})

            return {"id": _id,
                    "name": packing.name}
        else:
            return {"error": "new_name parameter is required"}

    # District
    @restapi.method(
        [(["/res_district/<int:id>"], "GET")],
        output_param=restapi.CerberusValidator("_get_district_schema"),
        auth="api_key",
    )

    def get_district(self, _id):
        return {"id": self.env["res.district"].browse(_id).id,
                "name": self.env["res.district"].browse(_id).name}

    def _get_district_schema(self):
        return {"id": {"type": "integer", "required": True},
                "name": {"type": "string", "required": True}}

    @restapi.method(
        [(["/res_district/list"], "GET")],
        output_param=restapi.CerberusListValidator("_get_district_schema"),
        auth="api_key",
    )
    def district_list(self):
        districts = self.env["res.district"].search([("active", "=", True)])
        return [{"id": p.id, "name": p.name} for p in districts]
    
    @restapi.method(
        [(["/res_district/search"], "GET")],
        input_param=restapi.Datamodel("masterdata.search.param"),
        output_param=restapi.Datamodel("masterdata.short.info", is_list=True),
        auth="api_key",
    )
    def district_search(self, master_search_param):
        """
        Search for district
        @param: Input ID or Word in Name
        @return: Return a list of district-follow parameters
        """
        domain = []
        if master_search_param.name:
            domain.append(("name", "like", master_search_param.name))
        if master_search_param.id:
            domain.append(("id", "=", master_search_param.id))
        res = []
        MasterShortInfo = self.env.datamodels["masterdata.short.info"]
        for p in self.env["res.district"].search(domain):
            res.append(MasterShortInfo(id=p.id, name=p.name))
        return res

    # ZONE
    @restapi.method(
        [(["/stock_zone/search"], "GET")],
        input_param=restapi.Datamodel("zone.search.param"),
        output_param=restapi.Datamodel("zone.short.info", is_list=True),
        auth="api_key",
    )
    def zone_search(self, zone_search_param):
        """
        Search for Zone
        @param: Input ID or Name or Warehouse ID
        @return: Return a list of Zone-follow parameters
        """
        domain = [("active", "=", True)]
        if zone_search_param.name:
            domain.append(("name", "like", zone_search_param.name))
        if zone_search_param.id:
            domain.append(("id", "=", zone_search_param.id))
        if zone_search_param.warehouse_id and isinstance(zone_search_param.warehouse_id, str):
            array = [int(x) for x in zone_search_param.warehouse_id.split(",")]
            domain.append(("warehouse_id", "in", array))
        res = []
        ZoneShortInfo = self.env.datamodels["zone.short.info"]
        for p in self.env["stock.zone"].search(domain):
            res.append(ZoneShortInfo(id=p.id, name=p.name, warehouse_id=p.warehouse_id))
        return res
    
    # STACK
    @restapi.method(
        [(["/stock_stack/search"], "GET")],
        input_param=restapi.Datamodel("stack.search.param"),
        output_param=restapi.Datamodel("stack.short.info", is_list=True),
        auth="api_key",
    )
    def stack_search(self, stack_search_param):
        """
        Search for Stack
        @param: Input ID or Name or Warehouse ID and Stack ID
        @return: Return a list of Stack-follow parameters
        """
        wh_array = ''
        query = ''
        if stack_search_param.warehouse_id and isinstance(stack_search_param.warehouse_id, str):
            wh_array = '= ' + str(stack_search_param.warehouse_id) if len(stack_search_param.warehouse_id.split(",")) == 1 else 'in ' + str(tuple([int(x) for x in stack_search_param.warehouse_id.split(",")]))
        if stack_search_param.zone_id and isinstance(stack_search_param.zone_id, str):
            query=' and ss.zone_id = %s '%(stack_search_param.zone_id)
            
        sql = '''SELECT ss.id, ss.name, ss.init_qty, ss.zone_id, sz.name zone_name, CAST(ss.create_date AS TEXT), ss.product_id, ss.warehouse_id,
                ss.init_qty, ss.active FROM stock_lot ss
            JOIN stock_zone sz ON sz.id = ss.zone_id
            WHERE ss.warehouse_id %s and ss.active = True AND ss.init_invetory = False %s
                and (ss.create_date >= date_trunc('month', CURRENT_DATE - INTERVAL '3 month') or ss.init_qty > 0) Order By ss.init_qty desc; 
                '''%(wh_array,query)
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        # print(result)
        res = []
        StackShortInfo = self.env.datamodels["stack.short.info"]
        for p in result:
            res.append(StackShortInfo(id=p['id'], name=p['name'], warehouse_id=p['warehouse_id'], init_qty=p['init_qty'], zone_id=p['zone_id'],
                                    zone_name=p['zone_name'], create_date=str(p['create_date']), product_id=p['product_id']))
        return res

    # BUILDING
    def _get_building_schema(self):
        return {"id": {"type": "integer", "required": True},
                "name": {"type": "string", "required": True}}

    @restapi.method(
        [(["/building_warehouse/list"], "GET")],
        output_param=restapi.CerberusListValidator("_get_building_schema"),
        auth="api_key",
    )
    def building_list(self):
        buildings = self.env["building.warehouse"].search([("active", "=", True)])
        return [{"id": p.id, "name": p.name} for p in buildings]

    @restapi.method(
        [(["/building_warehouse/search"], "GET")],
        input_param=restapi.Datamodel("masterdata.search.param"),
        output_param=restapi.Datamodel("masterdata.short.info", is_list=True),
        auth="api_key",
    )
    def building_search(self, master_search_param):
        """
        Search for building
        @param: Input ID or Word in Name
        @return: Return a list of building-follow parameters
        """
        domain = []
        if master_search_param.name:
            domain.append(("name", "like", master_search_param.name))
        if master_search_param.id:
            domain.append(("id", "=", master_search_param.id))
        res = []
        MasterShortInfo = self.env.datamodels["masterdata.short.info"]
        for p in self.env["building.warehouse"].search(domain):
            res.append(MasterShortInfo(id=p.id, name=p.name))
        return res
    
    # USERS
    def _get_users_schema(self):
        return {"id": {"type": "integer", "required": True},
                "name": {},
                "email": {}}

    @restapi.method(
        [(["/res_users/list"], "GET")],
        output_param=restapi.CerberusListValidator("_get_users_schema"),
        auth="api_key",
    )
    def users_list(self):
        users = self.env["res.users"].search([("active", "=", True),"|",("login", "=", "admin"),("partner_id.partner_code", "like", "%NED%")])
        return [{"id": p.id, "name": p.partner_id.name, "email": p.partner_id.email} for p in users]

    @restapi.method(
        [(["/res_users/search"], "GET")],
        input_param=restapi.Datamodel("user.search.param"),
        output_param=restapi.Datamodel("user.short.info", is_list=True),
        auth="api_key",
    )
    def user_search(self, user_search_param):
        """
        Search for users
        @param: Input ID or Name or Warehouse ID and user ID
        @return: Return a list of users-follow parameters
        """
        domain = [("active", "=", True),"|",("login", "=", "admin"),("partner_id.partner_code", "like", "%NED%")]
        if user_search_param.name:
            domain.append(("partner_id.name", "ilike", user_search_param.name))
        if user_search_param.id:
            domain.append(("id", "=", user_search_param.id))
        if user_search_param.email and user_search_param.email != 'all':
            domain.append(("login", "ilike", user_search_param.email))
        res = []
        UserShortInfo = self.env.datamodels["user.short.info"]
        for p in self.env["res.users"].search(domain):
            res.append(UserShortInfo(id=p.id, name=p.partner_id.name, email=p.login))
        return res

### SQL EXECUTE QUERY ###
    def _input_execute_query_schema(self):
        return {"exe_query": {"type": "string"}}
        
    def _output_execute_query_schema(self):
        return {
                'status_code': {"type": "string"},
                'message': {"type": "string"},
                }

    @restapi.method(
        [(["/execute_query"], "POST")],
        input_param=restapi.CerberusValidator("_input_execute_query_schema"),
        output_param=restapi.CerberusValidator("_output_execute_query_schema"),
        auth="api_key",
    )

    def execute_query(self, **params):
        exe_query = params.get('exe_query')
        records = request.cr.execute(exe_query)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                    'status_code': "SUD23-204",
                    'message': 'Record does not exist.',
                    }
            return mess
        else:
            return records