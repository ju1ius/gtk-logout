import pygtk
pygtk.require('2.0')
import gtk
import gobject

try:
    import cairo
    HAS_CAIRO = True
except ImportError:
    HAS_CAIRO = False

try:
    import PIL, PIL.Image, StringIO
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class LogoutWindow(gtk.Window):

    def __init__(self, config, actions):
        super(LogoutWindow, self).__init__(gtk.WINDOW_TOPLEVEL)
        self.config = config
        self.actions = actions

        self.set_urgency_hint(True)
        self.set_skip_pager_hint(True)
        self.set_skip_taskbar_hint(True)

        self.set_decorated(False)
        self.set_position(gtk.WIN_POS_CENTER)

        if self.config['effects']:
            self.supports_alpha = False
            if HAS_CAIRO:
                # Cairo is here so check for RGBA support
                screen = gtk.gdk.screen_get_default()
                rgba = screen.get_rgba_colormap()
                if rgba:
                    self.supports_alpha = True
                    self.set_colormap(rgba)
                    self.connect("expose-event",
                        self.on_expose,
                        self.config['opacity']/100
                    )
            if not self.supports_alpha and not HAS_PIL:
                # No RGBA, no PIL, no effects
                self.config['effects'] = False
        

        # Create the button box
        buttonbox = gtk.HButtonBox()
        buttonbox.set_spacing(10)

        # Create the containers
        mainpanel = gtk.HBox()
        centercolumn = gtk.VBox()
        centerrow = gtk.VBox()

        if self.config['logo']:
            # Logo
            logo = gtk.Image()
            logo.set_from_file(self.config['logo'])
            logo.set_padding(0,25)
            centerrow.pack_start(logo, True, True, 0)
        centerrow.pack_end(buttonbox, True, True, 0)

        centercolumn.pack_start(gtk.HBox(), True, True, 0)
        centercolumn.pack_start(centerrow, False, False, 0)
        centercolumn.pack_start(gtk.HBox(), True, True, 0)

        mainpanel.pack_start(gtk.VBox(), True, True, 0)
        mainpanel.pack_start(centercolumn, False, False, 0)
        mainpanel.pack_start(gtk.VBox(), True, True, 0)

        # Add the main panel to the window
        self.add(mainpanel)

        # Add the buttons
        for button in self.config['buttons']:
            self.add_button(button, buttonbox)
        if 'cancel' not in self.config['buttons']:
            self.add_button('cancel', buttonbox)
        
        if self.config['effects']:
            self.set_app_paintable(True)    
            self.move(0,0)
            self.resize(gtk.gdk.screen_width(), gtk.gdk.screen_height())
            if not self.supports_alpha:
                # Create pseudo transparent background
                self.create_pil_background(self.config['opacity'])            
        else:
            self.set_resizable(False)
            self.set_border_width(20)

    #------------------#
    # SIGNALS HANDLERS #
    #------------------#

    def on_expose(self, widget, event, opacity):
        print "Exposed"
        cr = widget.window.cairo_create()
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.rectangle(0.0, 0.0, *widget.get_size())
        cr.fill()
        cr.set_operator(cairo.OPERATOR_OVER) 
        cr.set_source_rgba(0.0,0.0,0.0,0.75)
        cr.rectangle(0.0, 0.0, *widget.get_size())
        cr.fill()
        return False

    def on_button_pressed(self, widget, event, action=None):
        self.emit("logout-action", action)
        return False
    

    #----------------#
    # CREATE BUTTONS #
    #----------------#

    def add_button(self, name, widget):
        """ Add a button to the panel """
        if self.config['effects']:
            self.add_fancy_button(name, widget)
        else:
            self.add_simple_button(name, widget)


    def add_simple_button(self, name, widget):
        box = gtk.HBox()

        img = gtk.Image()
        img.set_from_icon_name(self.actions[name]['icon'], gtk.ICON_SIZE_DND)

        lbl = gtk.Label()
        lbl.set_text(str(_(self.actions[name]['text'])))

        button = gtk.Button()
        #button.connect("clicked", self.on_button_clicked, name)
        button.connect("button-press-event", self.on_button_pressed, name)
        button.set_border_width(5)

        box.pack_start(img, True, True, 0)
        box.pack_end(lbl, True, True, 0)
        button.add(box)
        widget.pack_start(button, True, True, 0)


    def add_fancy_button(self, name, widget):
        box = gtk.VBox()

        image = gtk.Image()
        image.set_from_icon_name(self.actions[name]['icon'], gtk.ICON_SIZE_DIALOG)
        box.pack_start(image, False, False, 0)

        label = gtk.Label()
        label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
        label.set_use_markup(True)
        label.set_markup(str(
            '<span weight="bold" size="larger">%s</span>' %
            _( self.actions[name]['text'] )
        ))
        box.pack_end(label, False, False, 0)

        e = gtk.EventBox()
        e.set_visible_window(False)
        e.connect("button-press-event", self.on_button_pressed, name)
        e.add(box)

        widget.pack_start(e, False, False, 0)



#------------------#
# REGISTER SIGNALS #
#------------------#

gobject.type_register(LogoutWindow)
gobject.signal_new(
    "logout-action", LogoutWindow,
    gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
    [gobject.TYPE_STRING]
) 
