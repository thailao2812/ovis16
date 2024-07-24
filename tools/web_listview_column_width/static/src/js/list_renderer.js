odoo.define('web_listview_column_width.ListRenderer', function (require) {
    "use strict";

    const ListRenderer = require('web.ListRenderer');

    ListRenderer.include({

        _freezeColumnWidths: function () {
            if (!this.columnWidths && this.el.offsetParent === null) {
                // there is no record nor widths to restore or the list is not visible
                // -> don't force column's widths w.r.t. their label
                return;
            }
            const thElements = [...this.el.querySelectorAll('table thead th')];
            if (!thElements.length) {
                return;
            }
            const table = this.el.getElementsByTagName('table')[0];
            let columnWidths = this.columnWidths;

            if (!columnWidths || !columnWidths.length) { // no column widths to restore
                // Set table layout auto and remove inline style to make sure that css
                // rules apply (e.g. fixed width of record selector)
                table.style.tableLayout = 'auto';
                thElements.forEach(th => {
                    th.style.width = null;
                    th.style.maxWidth = null;
                });

                // Resets the default widths computation now that the table is visible.
                this._computeDefaultWidths();

                // Squeeze the table by applying a max-width on largest columns to
                // ensure that it doesn't overflow
                columnWidths = this._squeezeTable();
            }

            thElements.forEach((th, index) => {
                // Width already set by default relative width computation
                if (!th.style.width) {
                    th.style.width = `${columnWidths[index]}px`;
                    if (th.style.minWidth && !th.style.width) {
                        th.style.width = th.style.minWidth;
                    }
                }
            });

            // Set the table layout to fixed
            table.style.tableLayout = 'fixed';
        },

        _squeezeTable: function () {
            const columnWidths = this._super.apply(this, arguments);
            // if (!this.isCustomResizing) {
            //     return columnWidths;
            // }
            const table = this.el.getElementsByTagName('table')[0];
            const thead = table.getElementsByTagName('thead')[0];
            const thElements = [...thead.getElementsByTagName('th')];
            for (const column of this.columns) {
                let name, width;
                ({name, width} = column.attrs);
                const columnIndex = thElements.findIndex(ele => {
                    return ele.dataset.name === name;
                })
                if (width){
                    width = parseInt(width.replace('px', ''));
                }
                if (width && width >= columnWidths[columnIndex]) {
                    columnWidths[columnIndex] = width;
                }
                // width = width ? parseFloat(width) : this._getColumnWidth(column);
                // if (width !== '1') {
                //     columnWidths[columnIndex] = width;
                // }
            }
            // this.isCustomResizing = false;
            return columnWidths;
        },

        _getColumnWidth: function (column) {
            if (column.attrs.width) {
                return column.attrs.width;
            }
            const fieldsInfo = this.state.fieldsInfo.list;
            const name = column.attrs.name;
            if (!fieldsInfo[name]) {
                // Unnamed columns get default value
                return '1';
            }
            const widget = fieldsInfo[name].Widget.prototype;
            if ('widthInList' in widget) {
                return widget.widthInList;
            }
            const field = this.state.fields[name];
            if (!field) {
                // this is not a field. Probably a button or something of unknown
                // width.
                return '1';
            }
            const fixedWidths = {
                binary: '92px',
                boolean: '50px',
                char: '92px',
                date: '92px',
                datetime: '146px',
                float: '92px',
                integer: '74px',
                many2one: '92px',
                many2many: '92px',
                monetary: '104px',
                one2many: '92px',
                selection: '92px',
                text: '92px',
            };
            let type = field.type;
            if (fieldsInfo[name].widget in fixedWidths) {
                type = fieldsInfo[name].widget;
            }
            return fixedWidths[type] || '1';
        },
    })

});
