function update_sort_widgets(event)
{
    $('.sort-options input').attr('disabled', !$('#id_sort').attr('checked'));
}

function update_random_sample_widgets(event)
{
    $('#id_random_sample_size').attr('disabled', !$('#id_random_sample').attr('checked'));
}

function bookmark_link(event)
{
    event.preventDefault();
    timestamp = (new Date()).toLocaleString();
    title = '[Poliqarp] ' + event.target.title + ' ' + timestamp;
    title = title.replace('  ', ' ');
    window.sidebar.addPanel(title , event.target.href, '');
}

$(document).ready(function() {
    $('a[rel]').cluetip({showTitle: false});
    $('span[title]').cluetip({showTitle: false, width: '200', splitTitle: '|', cursor: 'auto'});
    $('#id_sort').click(update_sort_widgets);
    $('#id_random_sample').click(update_random_sample_widgets);
    update_sort_widgets(null);
    update_random_sample_widgets(null);
    if (window.sidebar) {
        /* Mozilla-specific hack */
        $('.bookmark-result').css('display', 'inline')
        $('.bookmark-result a').click(bookmark_link)
    }
})

/* vim:set ts=4 sw=4 et: */
