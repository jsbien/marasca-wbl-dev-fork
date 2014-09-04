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
    if (!window.sidebar.addPanel) {
        // window.sidebar.AddPanel was removed in Firefox 23:
        // https://bugzilla.mozilla.org/show_bug.cgi?id=691647
        // Let's try HTML5's rel="sidebar" instead.
        event.target.rel = 'sidebar';
        return;
    }
    event.preventDefault();
    timestamp = (new Date()).toLocaleString();
    info = event.target.href.split('#', 2)
    title = '[' + info[1] + ']' + event.target.title + ' ' + timestamp;
    title = title.replace('  ', ' ');
    window.sidebar.addPanel(title , info[0], '');
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
    if (window.sidebar) {
        /* Mozilla-specific hack */
        $('.bookmark-result').css('display', 'inline')
        $('.bookmark-result a').click(bookmark_link)
    }
})

/* vim:set ts=4 sw=4 et: */
