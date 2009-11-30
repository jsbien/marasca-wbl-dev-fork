function update_sort_widgets(event)
{
    $('.sort-options input').attr('disabled', !$('#id_sort').attr('checked'));
}

function update_random_sample_widgets(event)
{
    $('#id_random_sample_size').attr('disabled', !$('#id_random_sample').attr('checked'));
}

$(document).ready(function() {
    $('a[rel]').cluetip({showTitle: false});
    $('span[title]').cluetip({showTitle: false, width: '200', splitTitle: '|', cursor: 'auto'});
    $('#id_sort').click(update_sort_widgets);
    $('#id_random_sample').click(update_random_sample_widgets);
    update_sort_widgets(null);
    update_random_sample_widgets(null);
})

/* vim:set ts=4 sw=4 et: */
