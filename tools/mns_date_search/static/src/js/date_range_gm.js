odoo.define('mns_date_search.DateRangeGM', function (require) {
    "use strict";

    const { useModel } = require('web.Model');
    const { Component } =  owl;
    const { LegacyComponent } = require("@web/legacy/legacy_component");
    const ControlPanel = require('web.ControlPanel');
    var rpc = require('web.rpc');

    class DateRangeGM extends Component {
        setup() {
            this.dateFields = []
        }

        _onClickChangeFieldSelection(){
//            $("#all_field_date").empty();
            var self = this;
            var current_url = window.location.href;
            var modelRegex = /model=([^&]+)/;
            var match = current_url.match(modelRegex);
            return rpc.query({
                model: match[1],
                method: 'fields_get'
            }).then(function (fields) {
                console.log(fields)
                var x = document.getElementById("all_field_date").length;
                let flag = [];
                if (x <= flag.length){
                    for (var fieldName in fields) {
                        if (fields.hasOwnProperty(fieldName)) {
                            var field = fields[fieldName];
                            if (field.type === 'date' || field.type === 'datetime') {
                                flag.push(fieldName)
                                $('#all_field_date')
                                .append($('<option>', {
                                    value: fieldName,
                                    text : field.string
                                }));
                            }
                        }
                    }
                }
            });
        }

        _onClickDateRangePicker(){

            var self = this;
            $('.btn-apply-daterange').css('display', 'unset');

            let start;
            let end;

            if($('#daterange-input').data('daterangepicker') === undefined){
                start = moment();
                end = moment();
            }
            else{
                start = $('#daterange-input').data('daterangepicker').startDate;
                end = $('#daterange-input').data('daterangepicker').endDate;
            }

            function cb(start, end, label) {
//                $('.result-date-statistic').html(start.format('YYYY-MM-DD') + ' to ' + end.format('YYYY-MM-DD'))
                console.log(start.format('YYYY-MM-DD') + ' to ' + end.format('YYYY-MM-DD'))
            }

            $('#daterange-input').daterangepicker({
                startDate: start,
                endDate: end,
                opens: 'left',
                drops: 'down'
              }, cb);
              cb(start, end);

            $('#daterange-input').data('daterangepicker').show();
            $('#daterange-input').on('apply.daterangepicker', function(ev, picker) {
              self._onApplyData();
            });
        }
        _onApplyData(){
           var startDate = $('#daterange-input').data('daterangepicker').startDate;
           var endDate = $('#daterange-input').data('daterangepicker').endDate;
           var nameField = $('#all_field_date').val()
           let flagArr = [{
                description: `${$('#all_field_date option:selected').text()} "${startDate.format('DD-MM-YYYY')} and ${endDate.format('DD-MM-YYYY')}"`,
                domain: `[['${nameField}','>=','${startDate.format('YYYY-MM-DD')} 00:00:00'],['${nameField}','<=','${endDate.format('YYYY-MM-DD')} 23:59:59']]`,
                type: 'filter',
            }]
           this.env.searchModel.createNewFilters(flagArr);
        }
    }

    DateRangeGM.template = 'mns_date_search.DateRangeGM';

    return DateRangeGM;
});
