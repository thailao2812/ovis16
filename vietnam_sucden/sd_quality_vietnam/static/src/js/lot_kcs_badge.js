odoo.define('sd_quality_vietnam.badge_color_state', function (require) {
    "use strict";

    function colorBadge() {
        $('.my_state_badge span').each(function () {
            var val = $(this).attr('raw-value');
            // Reset styling trước
            $(this).css({
                'background-color': '',
                'color': '',
                'padding': '',
                'border-radius': '',
                'display': ''
            });
            
            // Áp dụng style mới dựa trên raw-value
            if (val === 'draft') {
                $(this).css({
                    'background-color': '#fafaad',
                    'color': '#040404',
                    'padding': '2px 8px',
                    'border-radius': '3px',
                    'display': 'inline-block'
                });
            } else if (val === 'approve') {
                $(this).css({
                    'background-color': '#28a745',
                    'color': '#fff',
                    'padding': '2px 8px',
                    'border-radius': '3px',
                    'display': 'inline-block'
                });
            } else if (val === 'cancel') {
                $(this).css({
                    'background-color': '#636262',
                    'color': '#fff',
                    'padding': '2px 8px',
                    'border-radius': '3px',
                    'display': 'inline-block'
                });
            } else if (val === 'ready') {
                $(this).css({
                    'background-color': '#17a2b8',
                    'color': '#fff',
                    'padding': '2px 8px',
                    'border-radius': '3px',
                    'display': 'inline-block'
                });
            }
        });
        
        console.log('Badge colors applied!');
    }

    // Chạy khi trang load xong
    $(document).ready(function () {
        setTimeout(colorBadge, 500); // Trễ một chút để đảm bảo DOM đã sẵn sàng
    });

    // Chạy khi view được cập nhật
    var core = require('web.core');
    core.bus.on('DOM_updated', null, colorBadge);
    
    // Bắt sự kiện click và tương tác UI để cập nhật màu
    $(document).on('click', '.o_list_button_add, .o_list_button_save, .o_list_button_discard', function() {
        setTimeout(colorBadge, 500);
    });
    
    console.log('Badge JS loaded successfully!');
});