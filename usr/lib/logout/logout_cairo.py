#! /usr/bin/python
import gtk
import cairo

from pprint import pprint

def on_screen_changed(widget, old_screen):
    screen = widget.get_screen()
    rgba = screen.get_rgba_colormap()
    widget.set_colormap(rgba)
    return False

def on_expose(widget, event, opacity):
    cr = widget.window.cairo_create()
    cr.set_source_rgba (0.0, 0.0, 0.0, opacity)
    cr.set_operator(cairo.OPERATOR_SOURCE)
    cr.paint()

    return False


def get_window(logout_menu):
    config = logout_menu.config
    # Create a new window
    window = gtk.Window(gtk.WINDOW_TOPLEVEL)

    window.set_title(_("<big><b>What Do you Want to do?</b></big>"))
    window.set_decorated(False)
    window.set_position(gtk.WIN_POS_CENTER)

    window.connect("destroy", logout_menu.quit)

    # Create the button box
    buttonbox = gtk.HButtonBox()
    buttonbox.set_spacing(10)

    # Create the containers
    mainpanel = gtk.HBox()
    centercolumn = gtk.VBox()
    centerrow = gtk.VBox()

    if config['logo']:
        # Logo
        logo = gtk.Image()
        logo.set_from_file(config['logo'])
        logo.set_padding(0,25)
        logo.show()
        centerrow.pack_start(logo)
    centerrow.pack_end(buttonbox, True, True)

    centercolumn.pack_start(gtk.HBox())
    centercolumn.pack_start(centerrow, False)
    centercolumn.pack_start(gtk.HBox())

    mainpanel.pack_start(gtk.VBox())
    mainpanel.pack_start(centercolumn, False)
    mainpanel.pack_start(gtk.VBox())

    # Add the main panel to the window
    window.add(mainpanel)

    # Add the buttons
    for button in config['buttons']:
        add_button(logout_menu, button, buttonbox)
    if 'cancel' not in config['buttons']:
        add_button(logout_menu, 'cancel', buttonbox)


    #window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('black'))
    window.resize(gtk.gdk.screen_width(), gtk.gdk.screen_height())
    window.move(0,0)

    window.set_app_paintable(True)
    window.connect("screen-changed", on_screen_changed)
    window.connect("expose-event", on_expose, config['opacity']/100)

    on_screen_changed(window, window.get_screen())

    window.show_all()

    return window


def add_button(logout_menu, name, widget):
    """ Add a button to the panel """
    config = logout_menu.config

    box = gtk.VBox()

    image = gtk.Image()
    image.set_from_icon_name(logout_menu._actions[name]['icon'], gtk.ICON_SIZE_DIALOG)
    image.show()

    button = gtk.Button()
    button.set_relief(gtk.RELIEF_NONE)
    button.set_focus_on_click(False)
    button.set_border_width(0)
    button.add(image)

    for state in [gtk.STATE_PRELIGHT, gtk.STATE_ACTIVE]:
        button.modify_bg(state,gtk.gdk.color_parse("black"))

    button.connect("clicked", logout_menu.on_button_clicked, name)

    button.show()
    box.pack_start(button, False, False)

    label = gtk.Label()
    label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
    label.set_use_markup(True)
    label.set_markup(
        '<span weight="bold" size="larger">%s</span>' %
        _( logout_menu._actions[name]['text'] )
    )
    box.pack_end(label, False, False)

    widget.pack_start(box, False, False)

