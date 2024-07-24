from odoo.addons.base_rest.controllers import main
    
class MasterDataRestApi(main.RestController):
    _root_path = '/v1/'
    _collection_name = "sucden.restapi.services"
    _default_auth = "api_key"
    
# class WeighbridgeRestApi(main.RestController):
#     _root_path = '/v1/weighbridge/'
#     _collection_name = "weighbridge.restapi.services"
#     _default_auth = "api_key"