from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
from datetime import datetime, timedelta, timezone
from collections import defaultdict

class IoTThinksToken(models.Model):
    _name = "iotthinks.token"
    _description = "IoTThinks API Token"

    token = fields.Char(string="Token", required=True)
    refresh_token = fields.Char(string="Refresh Token")
    expired_at = fields.Datetime(string="Expired At")

    @api.model
    def get_valid_token(self):
        token_record = self.search([], order="id desc", limit=1)
        # Nếu token còn hạn 2 phút, dùng lại token cũ
        if token_record and token_record.expired_at and \
                token_record.expired_at > fields.Datetime.now() + timedelta(minutes=2):
            return token_record.token
        # Hết hạn hoặc chưa có thì sinh mới
        return self.create_token_and_save()

    @api.model
    def create_token_and_save(self):
        url = "https://uipe.easylorawan.com/api/auth/login"
        payload = {
            "username": "easylorawan@sucden.com",
            "password": "sucden2023"
        }
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        if resp.status_code != 200:
            raise UserError(_("Lỗi lấy token: %s") % resp.text)
        data = resp.json()
        # Token thường có hiệu lực 1h (3600s), nếu API trả về thông tin thời gian hết hạn, bạn nên dùng nó:
        expire = datetime.now() + timedelta(seconds=3600)
        # Nếu API trả về field exp, decode rồi lấy thời gian thực tế!
        existing = self.search([], order="id desc", limit=1)
        vals = {
            "token": data.get("token"),
            "refresh_token": data.get("refreshToken"),
            "expired_at": expire
        }

        # Nếu có token cũ và còn hiệu lực thì update lại
        if existing:
            existing.write(vals)
            return existing.token
        # Nếu có token cũ nhưng không còn hiệu lực thì xóa
        else:
            # Nếu không có token nào thì tạo mới
            rec = self.create(vals)
            return rec.token
    
class DeviceProfile(models.Model):
    _name = "iotthinks.device.profile"
    _description = "Device Profile (Thông tin thiết bị Telemetry)"

    name = fields.Char(string="Name", required=True)
    device_id = fields.Char(string="Device ID", required=True, index=True)
    key = fields.Char(string="Telemetry Key", required=True)
    description = fields.Text(string="Description")
    latest_download = fields.Datetime(string="Latest Download", required=True)
    active = fields.Boolean(string="Active", default=True)
    country_id = fields.Many2one('res.country', string="Country", required=True, ondelete='restrict')

    @api.model
    def fetch_all_telemetry(self):
        """
        Gọi API lấy dữ liệu telemetry cho từng thiết bị theo từng ngày, lưu vào DeviceTelemetry,
        tự lấy lại token nếu hết hạn. from_date, to_date là datetime
        """
        from collections import defaultdict

        # Gom theo device_id
        devices = self.search([('active', '=', True)])
        device_map = defaultdict(list)  # {device_id: [profile, ...]}
        for device in devices:
            device_map[device.device_id].append(device)

        for device_id, profiles in device_map.items():
            # Xác định all keys của group này
            keys = [p.key for p in profiles if p.key]
            # Lấy thời gian start_ts (có thể lấy nhỏ nhất của nhóm, để không bỏ sót dữ liệu)
            start_date_min = min(int(p.latest_download.timestamp() * 1000) for p in profiles)
            start_date = datetime.fromtimestamp(start_date_min / 1000.0, tz=timezone(timedelta(hours=7))).date()

        # Chia các ngày
        num_days = (datetime.now().date() - start_date).days + 1
        for device_id, profiles in device_map.items():
            keys = [p.key for p in profiles if p.key]
            for i in range(num_days):
                start_day = start_date + timedelta(days=i)
                end_day = start_day + timedelta(days=1)

                # Convert to timestamp ms
                start_ts = int(datetime.combine(start_day, datetime.min.time()).timestamp() * 1000)
                # endTs là 23:59:59.999 của ngày end_day-1
                end_ts = int(datetime.combine(end_day, datetime.min.time()).timestamp() * 1000) - 1

                # Kiểm tra và lấy token hợp lệ mỗi lần gọi
                Token = self.env['iotthinks.token']
                token = Token.get_valid_token()

                # Gọi hàm lưu dữ liệu, truyền token
                self.env['iotthinks.device.telemetry'].fetch_and_store_telemetry_for_device_id(
                    profiles, device_id, keys, start_ts, end_ts, token
                )

            # Sau khi chạy xong hết, cập nhật hết latest_download về to_date cho tất cả profiles nhóm này
            for profile in profiles:
                profile.latest_download = datetime.now()


class DeviceTelemetry(models.Model):
    _name = "iotthinks.device.telemetry"
    _description = "Device Telemetry Timeseries"

    device_profile_id = fields.Many2one('iotthinks.device.profile', string="Device Name", ondelete="cascade")
    timestamp = fields.Float(string="Timestamp", required=True, index=True)
    datetime_device = fields.Datetime(string="Datetime", required=True, index=True)
    value = fields.Float(string="Value")
    datetime_display = fields.Char(string="Timestamp (Date & Time)",)
    country_id = fields.Many2one('res.country', string="Country", related='device_profile_id.country_id', store=True, readonly=True, ondelete='restrict')
    description = fields.Text(string="Description", related='device_profile_id.description', store=True, readonly=True)

    @api.model
    def fetch_and_store_telemetry_for_device_id(self, device_profiles, device_id, keys, start_ts, end_ts, token=None):
        """
        Gọi API timeseries theo device_id, keys, khoảng start_ts->end_ts, kiểm tra và refresh token nếu hết hạn (401)
        """
        key_str = ",".join(keys)
        url = (
            f"https://uipe.easylorawan.com/api/plugins/telemetry/DEVICE/"
            f"{device_id}/values/timeseries"
            f"?startTs={start_ts}&endTs={end_ts}&useStrictDataTypes=true&keys={key_str}"
        )
        TokenModel = self.env['iotthinks.token']

        attempt = 0
        max_attempts = 2 # thử 2 lần: token hiện tại và token mới
        while attempt < max_attempts:
            if not token:
                # Lần đầu tiên hoặc khi muốn làm mới token
                token = TokenModel.get_valid_token()
            headers = {
                'accept': 'application/json',
                'Authorization': f'Bearer {token}'
            }
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.status_code == 401:
                # Token hết hạn, làm mới
                if attempt == 0:
                    token = TokenModel.create_token_and_save()
                    attempt += 1
                    continue
                else:
                    # Đã cố lấy lại 1 lần nhưng vẫn fail -> raise lỗi
                    raise UserError(_("Token OAuth2 hết hạn và không lấy lại được!"))
            elif resp.status_code != 200:
                raise UserError(_(f"Lỗi lấy telemetry device {device_id}: {resp.text}"))
            else:
                # Thành công
                data = resp.json()
                # Map key -> device_profile
                key_to_profile = {profile.key: profile for profile in device_profiles}
                for key, points in data.items():
                    device_profile = key_to_profile.get(key)
                    if not device_profile:
                        continue
                    for entry in points:
                        ts = entry.get("ts")
                        value = entry.get("value")
                        dt = datetime.fromtimestamp(ts / 1000.0,tz=timezone(timedelta(hours=7)))
                        self.update_or_create_entry(device_profile, ts, dt, value)
                break
            attempt += 1

    @api.model
    def update_or_create_entry(self, device_profile, timestamp, datetime, value):
        domain = [
            ('device_profile_id', '=', device_profile.id),
            ('timestamp', '=', timestamp),
        ]
        rec = self.search(domain, limit=1)
        vals = {'value': value}
        if rec:
            rec.write(vals)
        else:
            vals.update({'device_profile_id': device_profile.id, 'timestamp': timestamp, 'datetime_device': datetime.replace(tzinfo=None), 
                         'datetime_display': datetime.strftime('%Y-%m-%d %H:%M:%S')})
            self.create(vals)
