/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";


patch(ListController.prototype, "purchase_consignment_list_view", {
    setup() {
        this._super.apply();
        this.orm = useService("orm");  // Sử dụng ORM để gọi phương thức
    },

    async wbButtonClickeEvent() {
        const response = await this.orm.call(
          'purchase.report.consignment',
          'cron_action_create_purchase_report_consignment',
        ).then(function (r) {
            location.reload();
        });
    }
});