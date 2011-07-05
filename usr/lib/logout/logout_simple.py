#! /usr/bin/python

import pygtk
pygtk.require('2.0')


def get_window(logout_menu):
    config = logout_menu.config
    # Create a new window
    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    window.set_title(_("<big><b>What Do you Want to do?</b></big>"))
    window.set_resizable(False)
    window.set_decorated(False)
    window.set_position(gtk.WIN_POS_CENTER)
    window.set_border_width(20)


    # Create a box to pack widgets into
    container = gtk.VBox()
    window.add(container)

    # Logo
    logo = gtk.Image()
    logo.set_from_file(config['logo'])
    logo.set_padding(0,25)

    box = gtk.HButtonBox()

    for button in config['buttons']:
        add_button(logout_menu, button, box)
    if 'cancel' not in config['buttons']:
        add_button(logout_menu, 'cancel', box)

    container.pack_start(logo)
    container.pack_end(box)
    return window

def add_button(logout_menu, action, widget):
    """ Add a button to the panel """
    box = gtk.HBox()

    img = gtk.Image()
    img.set_from_icon_name(logout_menu._actions[action]['icon'], gtk.ICON_SIZE_DND)

    lbl = gtk.Label()
    lbl.set_text(_(logout_menu._actions[action]['text']))

    button = gtk.Button()
    button.connect("clicked", logout_menu.on_button_clicked, action)
    button.set_border_width(5)

    box.pack_start(img)
    box.pack_end(lbl)
    button.add(box)
    widget.pack_start(button, True, True)
