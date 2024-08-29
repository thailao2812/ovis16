/** @odoo-module **/
import { _lt } from '@web/core/l10n/translation';
import { sprintf } from '@web/core/utils/strings';
import { GoogleMapSidebar } from '@web_view_google_map/views/google_map/google_map_sidebar';

export class GoogleMapsDrawingSidebar extends GoogleMapSidebar {
    getData(record) {
        let extras = [];
        const title = this._getTitle(record) || record.data.gshape_name;
        const subTitle = this._getSubtitle(record) || record.data.gshape_description;
        if (record.data.gshape_type === 'circle') {
            extras = [
                sprintf(_lt('Area: %s square meter'), (record.data.gshape_area || 0).toLocaleString()),
                sprintf(_lt('Radius: %s meter'), (record.data.gshape_radius || 0).toLocaleString()),
            ];
        } else if (record.data.gshape_type === 'polygon') {
            extras = [
                sprintf(_lt('Area: %s square meter'), (record.data.gshape_area || 0).toLocaleString()),
                record.data.gshape_polygon_lines,
            ];
        } else if (record.data.gshape_type === 'rectangle') {
            extras = [
                sprintf(_lt('Area: %s square meter'), (record.data.gshape_area || 0).toLocaleString()),
                sprintf(_lt('Width: %s meter'), (record.data.gshape_width || 0).toLocaleString()),
                sprintf(_lt('Height: %s meter'), (record.data.gshape_height || 0).toLocaleString()),
            ];
        }

        return {
            title,
            subTitle,
            extras,
            hasShape: record.id in this.props.shapes || false,
            shape: this.props.shapes[record.id] || false,
        };
    }
}

GoogleMapsDrawingSidebar.template = 'web_view_google_map_drawing.GoogleMapSidebar';
GoogleMapsDrawingSidebar.props = [...GoogleMapSidebar.props, 'shapes'];
