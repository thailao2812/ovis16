from datetime import datetime
URL_CONFIG = 'api_restful.default_api_restfull_url_config'
TOKEN_CONFIG = 'api_restful.default_api_restfull_access_token_config'
DATE_FORMAT = "%Y-%m-%d"


def default_create_value(record, type):
    return {
        'name': record.display_name,
        'model': record._name,
        'res_id': record.id,
        'type': type,
        'slc_method': 'post',
    }


def get_default_header_request(rec):
    url = rec.env.ref(URL_CONFIG, False)
    access_token = rec.env.ref(TOKEN_CONFIG, False)
    if not (url and access_token):
        return '', {}
    url = url.value + '/' + rec._name
    return url, {
        'content-type': 'application/json',
        'access-token': access_token and access_token.value or False,
    }


def format_date_format(date_value):
    _date = datetime.strptime(date_value, '%d/%m/%Y')
    return datetime.strftime(_date, DATE_FORMAT)
