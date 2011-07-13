#! /usr/bin/python

import os, sys, string, ConfigParser, StringIO
import pygtk
pygtk.require('2.0')
import gtk

try:
    import gettext
except Exception, detail:
	print detail
	sys.exit(1)

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


class LogoutMenu(gtk.Window):

    dbus_actions =   ['restart', 'shutdown', 'suspend', 'hibernate']
    actions = {
        'shutdown': {
            'command': 'gksu halt',
            'icon': 'gnome-session-halt',
            'text': 'Shutdown'
        },
        'restart': {
            'command': 'gksu reboot',
            'icon': 'gnome-session-reboot',
            'text': 'Reboot'
        },
        'suspend': {
            'command': "pmi action suspend",
            'icon': 'gnome-session-suspend',
            'text': 'Suspend'
        },
        'hibernate': {
            'command': "pmi action hibernate",
            'icon': 'gnome-session-hibernate',
            'text': 'Hibernate'
        },
        'lock': {
            'command': "xscreensaver-command -lock",
            'icon': 'system-lock-screen',
            'text': 'Lock'
        },
        'switch': {
            'command': "gdm-control --switch-user",
            'icon':'system-log-out',
            'text': 'Switch User'
        },
        'logout': {
            'command': "fluxbox-remote exit",
            'icon':'gnome-session-logout',
            'text': 'Logout'
        },
        'cancel': {
            'command': "exit 0",
            'icon':'gtk-cancel',
            'text': 'Cancel'
        }
    }


    def __init__(self, config_paths):
        super(LogoutMenu, self).__init__(gtk.WINDOW_TOPLEVEL)
        # Initialize i18n
        gettext.install(
            "messages",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "locale"),
            unicode=1
        )
        # Load configuration file
        self.load_config(config_paths)
        # Bootstrap UI
        self.init_ui()
        self.connect("destroy", self.quit)

    #--------------#
    # MAIN ACTIONS #
    #--------------#

    def on_button_pressed(self, widget, event, action=None):
        self.action(action)
        return False
    
    def action(self, action=None):
        if action in self.dbus_actions and self.config['usedbus']:
            method = getattr(self.dbus, action)
            method()
        else:
            self.exec_cmd(self.actions[action]['command'])
        self.quit()

    def exec_cmd(self, cmdline):
        os.system(cmdline)

    def quit(self, widget=None, data=None):
        gtk.main_quit()

    def run(self):
        self.show_all()
        gtk.main()

    #---------------#
    # CONFIGURATION #
    #---------------#

    def load_config(self, config_paths):
        """ Load the configuration file and parse entries, when encountering a issue
            change safe defaults """
        self.config = {}
        
        # ----- DEFAULTS

        valid_actions = self.actions.keys()
        self.config['buttons'] = ['logout','restart','shutdown']

        defaults = StringIO.StringIO("""
[Settings]
logo: distributor-logo.png
usedbus: yes
effects: yes
opacity: 50
buttons: logout,restart,shutdown

[Icons]
lock: system-lock-screen
logout: system-logout
switch: system-logout
suspend: system-suspend
hibernate: system-hibernate
restart: system-restart
shutdown: system-shutdown
cancel: gtk-cancel
""")

        config_parser = ConfigParser.RawConfigParser()
        config_parser.readfp(defaults)
        config_parser.read(config_paths)
        defaults.close()

        # ----- LOGO
        try:
            self.config['logo'] = config_parser.getboolean("Settings", "logo")
        except ValueError:
            self.config['logo'] = config_parser.get("Settings", "logo")
            if not os.path.isabs(self.config['logo']):
                self.config['logo'] = os.path.abspath(os.path.join(
                    os.path.dirname(__file__), self.config['logo']
                ))

        # ----- DBUS

        self.config['usedbus'] = config_parser.getboolean("Settings","usedbus")
        # Instanciate the DBusController
        if self.config['usedbus']:
            from dbushandler import DbusController
            self.dbus = DbusController()

        # ----- EFFECTS

        self.config['effects'] = config_parser.getboolean("Settings","effects")
        opacity = config_parser.getfloat("Settings","opacity")
        if opacity > 100 or opacity <= 0:
            opacity = 75
        self.config['opacity'] = opacity

        # ----- BUTTONS

        buttons = [btn.strip() for btn in config_parser.get('Settings', 'buttons').split(',')]
        for button in buttons:
            if not button in valid_actions:
                buttons.remove(button)
            else:
                if self.config['usedbus'] and button in self.dbus_actions:
                    if not self.dbus.check_ability(button):
                        buttons.remove(button)
        if not 'cancel' in buttons: buttons.append('cancel')
        if len(buttons) > 1: self.config['buttons'] = buttons

        # ----- ACTIONS

        # Parse in commands section of the configuration file. Check for valid keys and set the attribs on self
        if config_parser.has_section('Commands'):
            for key in config_parser.items("Commands"):
                if key[0] in valid_actions:
                    if key[1]: self.actions[key[0]]['command'] = key[1]

        # ----- ICONS

        if config_parser.has_section('Icons'):
            for key in config_parser.items('Icons'):
                if key[0] in valid_actions:
                    if key[1]: self.actions[key[0]]['icon'] = key[1]

    #----#
    # UI #
    #----#
    
    def init_ui(self):
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



#######################################################
# MAIN
#######################################################
if __name__ == "__main__":
    if len(sys.argv) > 1:
        config_paths = os.path.abspath(os.path.expanduser(sys.argv[1]))
    else:
        config_paths = [
            '/etc/logout/logout.conf',
            os.path.expanduser('~/.config/logout/logout.conf')
        ]
    logout_menu = LogoutMenu(config_paths)
    logout_menu.run()
