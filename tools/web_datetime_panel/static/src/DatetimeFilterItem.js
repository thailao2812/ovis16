/** @odoo-module **/

import { CustomFilterItem } from "@web/search/filter_menu/custom_filter_item";
import { _lt } from "@web/core/l10n/translation";
import { useState, useRef, onWillUnmount } from "@odoo/owl";
import { serializeDate, serializeDateTime } from "@web/core/l10n/dates";
const { DateTime } = luxon;

const FIELD_TYPES = {
    date: "date",
    datetime: "datetime",
};

const DATE_TYPE_SELECTION = {
    day: "day",
    week: "week",
    month: "month",
};

const DEFAULT_DATE_TIME_SETTING = {
    date_type: DATE_TYPE_SELECTION.day,
    dateTimeDomain: [],
    isSearchingByDateTimePanel: false,
    value: [false, false],
    field_index: 0
};

export class DatetimeFilterItem extends CustomFilterItem {
    setup() {
        this.dateFilterRef = useRef("date-filter-ref");
        const searchViewFields = this.env.searchModel?.searchViewFields;
        if (!searchViewFields) return;

        this.filteredDateTimeFields = []
        const context = this.env.searchModel?._context
        if('search_by_field_date' in context) {
            this.filteredDateTimeFields.push(...context['search_by_field_date'])
        }

        this.fields = Object.values(searchViewFields)
            .filter((field) => this._isDatetimeFields(field))
            .sort(({ string: a }, { string: b }) => (a > b ? 1 : a < b ? -1 : 0));
        this.FIELD_TYPES = FIELD_TYPES;
        //THINH - add fields checking for some specific layout that don't need date time filter
        if (!this.fields?.length) return;

        this.addDateTimeSetting();
    }

    addDateTimeSetting() {
        if (!this.env.searchModel.dateTimeSetting) {
            this.env.searchModel.dateTimeSetting = { ...DEFAULT_DATE_TIME_SETTING };
        }

        const { dateTimeSetting } = this.env.searchModel;
        dateTimeSetting.value[0] = this.processLuxonDateTime(dateTimeSetting.value[0]);
        dateTimeSetting.value[1] = this.processLuxonDateTime(dateTimeSetting.value[1]);
        this.state = useState({ dateTimeSetting });
    }

    onFieldSelect(ev) {
        this.state.dateTimeSetting.field_index = ev.target.selectedIndex;
        // this.setDefaultValue();
        this.resetDomain()
    }

    _isDatetimeFields(field) {
        const isManualSetting = this.filteredDateTimeFields?.length
        const isInContext = this.filteredDateTimeFields?.includes(field.name)
        const allowFieldDisplay = isManualSetting && isInContext || !isManualSetting
        return (!field.deprecated && allowFieldDisplay && field.searchable && (field.type === "datetime" || field.type === "date"));
    }

    performOperationOnDate(operation = "minus", value = 1) {
        if (!this._validateDateTimeValue()) return;

        const dateTimeValue = [...this.state.dateTimeSetting.value]
        const [start_date, end_date] = dateTimeValue;
        switch (this.state.dateTimeSetting.date_type) {
            case DATE_TYPE_SELECTION.week:
                const week_date = operation === "minus" ? start_date.minus({ weeks: value }) : start_date.plus({ weeks: value });
                dateTimeValue[0] = week_date.startOf("week");
                dateTimeValue[1] = end_date ? week_date.endOf("week") : undefined;
                break;
            case DATE_TYPE_SELECTION.month:
                const month_date = operation === "minus" ? start_date.minus({ months: value }) : start_date.plus({ months: value });
                dateTimeValue[0] = month_date.startOf("month");
                dateTimeValue[1] = end_date ? month_date.endOf("month"): undefined;
                break;
            default:
                dateTimeValue[0] = operation === "minus" ? start_date.minus({ days: value }) : start_date.plus({ days: value });
                if(end_date) dateTimeValue[1] = operation === "minus" ? end_date.minus({ days: value }) : end_date.plus({ days: value });
        }

        this.state.dateTimeSetting.value = dateTimeValue
    }

    onDateTimeChanged(valueIndex, date) {
        const value = [...this.state.dateTimeSetting.value];
        value[valueIndex] = date;
        this.state.dateTimeSetting.value = value;
    }

    _validateDateTimeValue() {
        const [start_date, _] = this.state.dateTimeSetting.value;
        if (!start_date) return false;

        return true;
    }

    onErase() {
        this.clearDateTimeSetting();
        this.resetDomain();
    }

    clearDateTimeSetting() {
        const dateFilterElement = this.dateFilterRef.el;
        if (!dateFilterElement) return;
        const inputElements = dateFilterElement.querySelectorAll("input");
        inputElements.forEach((input) => (input.value = ""));
    }

    moveLeft() {
        this.performOperationOnDate();
        this.onApply();
    }

    moveRight() {
        this.performOperationOnDate("plus");
        this.onApply();
    }

    filterOnDay() {
        this.state.dateTimeSetting.date_type = DATE_TYPE_SELECTION.day;
        this.setDefaultValue();
        this.performOperationOnDate("minus", 0);
        this.onApply();
    }

    processLuxonDateTime(date) {
        if(typeof date === "string") {
            return DateTime.fromISO(date)
        }

        return date
    }

    filterOnWeek() {
        this.state.dateTimeSetting.date_type = DATE_TYPE_SELECTION.week;
        if (!this.state.dateTimeSetting.value[0]) this.setDefaultValue();

        this.performOperationOnDate("minus", 0);
        this.onApply();
    }

    filterOnMonth() {
        this.state.dateTimeSetting.date_type = DATE_TYPE_SELECTION.month;
        if (!this.state.dateTimeSetting.value[0]) this.setDefaultValue();

        this.performOperationOnDate("minus", 0);
        this.onApply();
    }

    isShowing() {
        return !!this.fields?.length;
    }

    onApply() {
        const domainArray = [];
        const field = this.fields[this.state.dateTimeSetting.field_index];
        const genericType = this.FIELD_TYPES[field.type];
        let domainValue;
        const serialize = genericType === "date" ? serializeDate : serializeDateTime;
        if (this.state.dateTimeSetting.value.some((value) => !value)) return;
        domainValue = this.state.dateTimeSetting.value.map(serialize);
        domainArray.push([field.name, ">=", domainValue[0]], [field.name, "<=", domainValue[1]]);

        this.state.dateTimeSetting.dateTimeDomain = domainArray;
        this.state.dateTimeSetting.isSearchingByDateTimePanel = true
        this.env.searchModel.searchPanelInfo.shouldReload = true;
        this.env.searchModel.trigger("update");
    }

    get isSearching() {
        return this.state.dateTimeSetting?.dateTimeDomain.length
    }

    resetDomain() {
        this.env.searchModel.dateTimeSetting = {
            ...DEFAULT_DATE_TIME_SETTING,
            isSearchingByDateTimePanel: true,
            field_index: this.state.dateTimeSetting.field_index
        };

        this.state.dateTimeSetting = this.env.searchModel.dateTimeSetting
        this.env.searchModel.searchPanelInfo.shouldReload = true;
        this.env.searchModel.trigger("update");
    }

    setDefaultValue() {
        const localDate = DateTime.local();
        this.state.dateTimeSetting.value = [localDate, localDate];
        const field = this.fields[ this.state.dateTimeSetting.field_index];
        if (FIELD_TYPES[field.type] === "date") return;
        const dateTimeValue = [...this.state.dateTimeSetting.value]
        dateTimeValue[0] = this.state.dateTimeSetting.value[0].set({ hour: 0, minute: 0, second: 0 });
        dateTimeValue[1] = this.state.dateTimeSetting.value[1].set({ hour: 23, minute: 59, second: 59 });
        this.state.dateTimeSetting.value = dateTimeValue
    }
}

DatetimeFilterItem.template = "web_datetime_panel.DatetimeFilterItem";
DatetimeFilterItem.components = { ...CustomFilterItem.components };
