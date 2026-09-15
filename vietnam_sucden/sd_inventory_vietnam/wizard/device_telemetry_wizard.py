from odoo import models, fields, api

class DeviceTelemetryWizard(models.TransientModel):
    _name = 'iotthinks.device.telemetry.wizard'
    _description = 'Chọn giai đoạn lấy dữ liệu telemetry'

    start_date = fields.Datetime(string="Từ ngày", required=True)
    end_date = fields.Datetime(string="Đến ngày", required=True)

    def action_fetch_telemetry(self):
        # Convert sang timestamp mili giây
        import time
        for wizard in self:
            start_ts = int(wizard.start_date.timestamp() * 1000)
            end_ts = int(wizard.end_date.timestamp() * 1000)
            self.env['iotthinks.device.profile'].fetch_all_telemetry()
        return {'type': 'ir.actions.act_window_close'}