/** @odoo-module **/

import { ListRenderer } from "@web/views/list/list_renderer";

export class NoDeleteListRenderer extends ListRenderer {
    freezeColumnWidths() {
        const table = this.tableRef.el;
        const virtualTable = table.parentElement.querySelector("#virtualTable");

        if (!virtualTable) return;

        if (!virtualTable.classList.contains("o_virtual_table")) {
            virtualTable.classList.add("o_virtual_table");
        }

        const columnCounts = [...table.querySelectorAll("thead th")];
        const headers = [...table.querySelectorAll("thead th:not(.o_list_actions_header)")];
        const cw = this.columnWidths;
        if (!cw || !cw.length || columnCounts.length != cw.length) {
            table.style.tableLayout = "auto";
            headers.forEach((th) => {
                th.style.width = null;
                th.style.maxWidth = null;
            });

            this.setDefaultColumnWidths();
            this.columnWidths = this.computeColumnWidthsFromContent();
            table.style.tableLayout = "fixed";
        }

        headers.forEach((th, index) => {
            if (!th.style.width) {
                th.style.width = `${Math.floor(this.columnWidths[index])}px`;
            }
        });

        const poundElement = headers.shift();
        const poundChildElement = poundElement.firstChild;

        if (!poundChildElement?.classList?.contains("pound")) return;

        poundElement.style.width = "36px";
        poundElement.style.padding = "10px";
    }
}

NoDeleteListRenderer.recordRowTemplate = "NoDeleteRecordRow";
