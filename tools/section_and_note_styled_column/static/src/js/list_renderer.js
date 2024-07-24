

/** @odoo-module */
import { patch } from "@web/core/utils/patch";

import { ListRenderer } from "@web/views/list/list_renderer";

patch(ListRenderer.prototype, "section_and_note_styled_column", {

    freezeColumnWidths() {
        if (!this.keepColumnWidths) {
            this.columnWidths = null;
        }

        const table = this.tableRef.el;
        const headers = [...table.querySelectorAll("thead th:not(.o_list_actions_header)")];
        const rows = [...table.querySelectorAll("tbody tr")];

        if (!this.columnWidths || !this.columnWidths.length) {
            // no column widths to restore
            // Set table layout auto and remove inline style to make sure that CSS
            // rules apply (e.g. fixed width of record selector)
            table.style.tableLayout = "auto";
            headers.forEach((th) => {
                th.style.width = null;
                th.style.maxWidth = null;
            });

            this.setDefaultColumnWidths();

            // Squeeze the table by applying a max-width on the largest columns to
            // ensure that it doesn't overflow
            this.columnWidths = this.computeColumnWidthsFromContent();
            table.style.tableLayout = "fixed";
        }

        const columnWidths = Array.from({ length: headers.length }, (_, index) => 0);

        rows.forEach((row) => {
            const tds = [...row.querySelectorAll("td")];

            tds.forEach((td, index) => {
                const cellWidth = td.scrollWidth;
                columnWidths[index] = Math.max(columnWidths[index], cellWidth);
            });
        });

        headers.forEach((header, index) => {
            const td = rows[0].querySelectorAll("td")[index];
            if (!header.style.width) {
                if (td !== undefined && td.classList.contains("o_many2many_tags_cell")) {
                    header.style.width = `${Math.floor(this.columnWidths[index])}px`;
                    header.style.maxWidth = `${Math.floor(this.columnWidths[index])}px`;
                } else {
                    if (this.columnWidths[index] < columnWidths[index]) {
                        if (index !== 0) {
                            if (columnWidths[index] < 120) {
                                header.style.width = `${columnWidths[index] + 10}px`;
                                header.style.maxWidth = `${columnWidths[index] + 10}px`;
                            }
                            if (120 < columnWidths[index] < 400) {
                                header.style.width = `120px`;
                                header.style.maxWidth = `120px`;
                            }
                            if (columnWidths[index] > 400) {
                                header.style.width = `200px`;
                                header.style.maxWidth = `200px`;
                            }
                        }
                        else {
                            header.style.width = `${Math.floor(this.columnWidths[index])}px`;
                        }
                    }
                    else {
                        if (columnWidths[index] > 300) {
                                header.style.width = `200px`;
                        }
                        else {
                            header.style.width = `${Math.floor(this.columnWidths[index])}px`;
                        }
                    }
                }
            }
            if (!header.classList.length) {
                header.style.width = "10px";
                header.style.maxWidth = "10px";
            }
        });

        // Set white-space property to allow content to wrap
        rows.forEach((row) => {
            const tds = [...row.querySelectorAll("td")];
            tds.forEach((td) => {
                td.style.overflow = 'unset';
                td.style.whiteSpace = "normal";
                td.style.wordWrap = "break-word";
            });
        });
    }


});

