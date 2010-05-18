function update_sort_widgets(event)
{
    $('.sort-options input').attr('disabled', !$('#id_sort').attr('checked'));
}

function update_random_sample_widgets(event)
{
    $('#id_random_sample_size').attr('disabled', !$('#id_random_sample').attr('checked'));
}

$(document).ready(function() {
    $("a[rel]").tooltip({ 
        bodyHandler: function() { 
            r = $("<div/>").load(this.rel);
            r.css('max-width', '20em');
            return r;
        }, 
        showURL: false 
    });
    $('span[title]').tooltip();
    $('#id_sort').click(update_sort_widgets);
    $('#id_random_sample').click(update_random_sample_widgets);
    update_sort_widgets(null);
    update_random_sample_widgets(null);
})

/* vim:set ts=4 sw=4 et: */
