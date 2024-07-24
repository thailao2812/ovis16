/** @odoo-module **/
import { ListRenderer } from "@web/views/list/list_renderer";

function setDefaultColumnWidths() {
    const dragWidget = this.tableRef.el.querySelector(".o_handle_cell");

    if (!dragWidget) return;

    dragWidget.style.width = "20px";
}


ListRenderer.prototype.setDefaultColumnWidths = setDefaultColumnWidths;
