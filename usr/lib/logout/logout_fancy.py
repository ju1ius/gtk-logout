#! /usr/bin/python
import gtk

def get_window(logout_menu):
    config = logout_menu.config
    # Create a new window
    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    supports_aplha = window.is_composited()

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

    if config['effects'] and not supports_aplha:
        try:
            import PIL, PIL.Image, StringIO
        except:
            config['effects'] = False

    # Add the buttons
    for button in config['buttons']:
        add_button(logout_menu, button, buttonbox)
    if 'cancel' not in config['buttons']:
        add_button(logout_menu, 'cancel', buttonbox)


    if config['effects']:
        window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
        window.set_app_paintable(True)
        window.resize(gtk.gdk.screen_width(), gtk.gdk.screen_height())
        # Create pseudo transparent background
        if not supports_aplha:
            w = gtk.gdk.get_default_root_window()
            sz = w.get_size()
            pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,False,8,sz[0],sz[1])
            pb = pb.get_from_drawable(w,w.get_colormap(),0,0,0,0,sz[0],sz[1])

            # Convert Pixbuf to PIL Image
            wh = (pb.get_width(),pb.get_height())
            pilimg = PIL.Image.fromstring("RGB", wh, pb.get_pixels())
            pilimg = pilimg.point(lambda p: (p * (100-config['opacity'])) / 255 )

            # "Convert" the PIL to Pixbuf via PixbufLoader
            buf = StringIO.StringIO()
            pilimg.save(buf, "ppm")
            del pilimg
            loader = gtk.gdk.PixbufLoader("pnm")
            loader.write(buf.getvalue())
            pixbuf = loader.get_pixbuf()

            # Cleanup IO
            buf.close()
            loader.close()
            pixmap, mask = pixbuf.render_pixmap_and_mask()
        else:
            window.set_opacity(config['opacity']/100)
        window.realize()
        if not supports_aplha:
            window.window.set_back_pixmap(pixmap, False)
        window.move(0,0)
    else:
        window.set_resizable(False)
        window.set_border_width(20)

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
    button.show()
    box.pack_start(button, False, False)
    button.connect("clicked", logout_menu.on_button_clicked, name)

    label = gtk.Label()

    if config['effects']:
        for state in [gtk.STATE_NORMAL, gtk.STATE_PRELIGHT, gtk.STATE_ACTIVE]:
            button.modify_bg(state,gtk.gdk.color_parse("black"))
        label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))

    label.set_use_markup(True)
    label.set_markup(
        '<span weight="bold" size="larger">%s</span>' %
        _( logout_menu._actions[name]['text'] )
    )
    box.pack_end(label, False, False)

    widget.pack_start(box, False, False)
