#! /usr/bin/python

import os, sys, stat, string, StringIO
import gettext
import ConfigParser, logging, logging.handlers
import subprocess, shlex
from subprocess import PIPE

import pygtk
pygtk.require('2.0')
import gtk



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
            'command': 'shutdown -h now',
            'icon': 'system-shutdown',
            'text': 'Shut Down'
        },
        'restart': {
            'command': 'reboot',
            'icon': 'system-restart',
            'text': 'Restart'
        },
        'suspend': {
            'command': "pm-suspend",
            'icon': 'system-suspend',
            'text': 'Suspend'
        },
        'hibernate': {
            'command': "pm-hibernate",
            'icon': 'system-hibernate',
            'text': 'Hibernate'
        },
        'lock': {
            'command': "xscreensaver-command -lock",
            'icon': 'system-lock-screen',
            'text': 'Lock Screen'
        },
        'switch': {
            'command': "gdmflexiserver",
            'icon':'system-log-out',
            'text': 'Switch User'
        },
        'logout': {
            'command': "fluxbox-remote exit",
            'icon':'system-log-out',
            'text': 'Log Out'
        },
        'cancel': {
            'command': "exit 0",
            'icon':'application-exit',
            'text': 'Cancel'
        }
    }


    def __init__(self):
        super(LogoutMenu, self).__init__(gtk.WINDOW_TOPLEVEL)
        # Logging
        self.init_logging()
        # Initialize i18n
        gettext.install(
            "gtk-logout",
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "locale"),
            unicode=1
        )
        # Load configuration file
        self.load_config()
        # Bootstrap GUI
        self.init_gui()
        self.connect("destroy", self.quit)

    #--------------#
    # MAIN ACTIONS #
    #--------------#

    def on_button_pressed(self, widget, event, action=None):
        self.action(action)
        return False
    
    def action(self, action=None):
        if action == 'cancel':
            self.quit()
            return
        elif action in self.dbus_actions and self.config['usedbus']:
            method = getattr(self.dbus, action)
            try:
                r = method()
            except Exception, e:
                r = False
                self.error_dialog(str(e))
        else:
            r = self.exec_cmd(self.actions[action]['command'])
        if r:
            self.quit()

    def exec_cmd(self, cmdline):
        try:
            args = shlex.split(cmdline)
            p = subprocess.Popen(args, stdout=PIPE, stderr=PIPE)
            r = p.communicate()
            if r[1]:
                error = 'Command "%s" returned:\n%s' % (cmdline, r[1])
                self.error_dialog(error)
                return False
            else:
                self.logger.info('Command "%s" returned:\n%s', cmdline, r[0])
                return True
        except OSError:
            error = 'Command "%s" was not found' % cmdline
            self.error_dialog(error)
            return False
            

    def quit(self, widget=None, data=None):
        gtk.main_quit()

    def run(self):
        self.show_all()
        gtk.main()

    #---------------#
    # CONFIGURATION #
    #---------------#

    def load_config(self):
        """ Load and parse the configuration file,
            falling back to safe defaults when encountering a issue."""
        self.config = {}
        
        # ----- DEFAULTS

        valid_actions = self.actions.keys()
        self.config['buttons'] = ['logout','restart','shutdown']

        defaults = StringIO.StringIO("""
[Settings]
logo: distributor-logo.png
usedbus: yes
effects: yes
force_pseudo_transparency: no
opacity: 50
buttons: lock,suspend,logout,restart,shutdown
""")
        config_parser = ConfigParser.RawConfigParser()
        config_parser.readfp(defaults)
        config_parser.read([
            '/etc/gtk-logout/logout.conf',
            os.path.expanduser('~/.config/gtk-logout/logout.conf')
        ])
        defaults.close()

        # ----- DBUS

        self.config['usedbus'] = config_parser.getboolean("Settings","usedbus")
        # Instanciate the DBusController
        if self.config['usedbus']:
            try:
                import dbus
                from dbushandler import DbusController
                self.dbus = DbusController()
            except:
                self.config['usedbus'] = False
                cmds = ""
                for a in self.dbus_actions:
                    cmds += "%s: %s\n" % (a, self.actions[a]['command'])
                self.logger.warning(
                    "Could not import python-dbus. Falling back to:\n%s" % cmds
                )

        # ----- ACTIONS

        # Parse in commands section of the configuration file. Check for valid keys and set the attribs on self
        if config_parser.has_section('Commands'):
            for key in config_parser.items("Commands"):
                if key[0] in valid_actions:
                    if key[1]: self.actions[key[0]]['command'] = key[1]

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


        # ----- LOGO
        try:
            self.config['logo'] = config_parser.getboolean("Settings", "logo")
        except ValueError:
            self.config['logo'] = config_parser.get("Settings", "logo")
            if not os.path.isabs(self.config['logo']):
                self.config['logo'] = os.path.abspath(os.path.join(
                    os.path.dirname(__file__), self.config['logo']
                ))

        # ----- EFFECTS

        self.config['effects'] = config_parser.getboolean("Settings","effects")
        self.config['force_pseudo_transparency'] = config_parser.getboolean("Settings","force_pseudo_transparency")
        opacity = config_parser.getfloat("Settings","opacity")
        if opacity > 100 or opacity <= 0:
            opacity = 75
        self.config['opacity'] = opacity

        # ----- ICONS

        if config_parser.has_section('Icons'):
            for key in config_parser.items('Icons'):
                if key[0] in valid_actions:
                    if key[1]: self.actions[key[0]]['icon'] = key[1]

    #-----#
    # GUI #
    #-----#
    
    def init_gui(self):
        """Sets up the gui components"""
        self.set_urgency_hint(True)
        #self.set_skip_pager_hint(True)
        self.set_skip_taskbar_hint(True)

        self.set_decorated(False)
        self.set_position(gtk.WIN_POS_CENTER)

        if self.config['effects']:
            self.supports_alpha = False
            if HAS_CAIRO and not self.config['force_pseudo_transparency']:
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
                self.logger.warning(
                    "No support for transparency. Please install python-imaging OR python-cairo with a compositing manager"
                )       

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
        """Draws a semi-transparent background"""
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
        icon = self.actions[name]['icon']
        if os.path.isabs(icon):
            img.set_from_file(icon)
        else:
            img.set_from_icon_name(icon, gtk.ICON_SIZE_DIALOG)

        lbl = gtk.Label()
        lbl.set_text(str(_(self.actions[name]['text'])))

        button = gtk.Button()
        button.connect("button-press-event", self.on_button_pressed, name)
        button.set_border_width(5)

        box.pack_start(img, True, True, 0)
        box.pack_end(lbl, True, True, 0)
        button.add(box)
        widget.pack_start(button, True, True, 0)


    def add_fancy_button(self, name, widget):
        box = gtk.VBox()

        image = gtk.Image()
        icon = self.actions[name]['icon']
        if os.path.isabs(icon):
            image.set_from_file(icon)
        else:
            image.set_from_icon_name(icon, gtk.ICON_SIZE_DIALOG)
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


    def error_dialog(self, message):
        self.logger.error(message)
        error_dlg = gtk.MessageDialog(
            type=gtk.MESSAGE_ERROR, flags=gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
            message_format="Error:", buttons=gtk.BUTTONS_OK
        )
        error_dlg.format_secondary_text(message)
        error_dlg.run()
        error_dlg.destroy()

    #---------#
    # LOGGING #
    #---------#

    def init_logging(self):
        """Sets up logging along with requires paths"""
        wdir = os.path.expanduser('~/.config/gtk-logout')
        logfile = os.path.expanduser(os.path.join(wdir, 'logout.log'))

        if not os.path.isdir(wdir):
            os.makedirs(wdir)
        if not os.path.isfile(logfile):
            os.mknod(logfile, 0644|stat.S_IFREG)

        self.logger = logging.getLogger('gtk-logout')
        self.logger.setLevel(logging.DEBUG)
        handler = logging.handlers.RotatingFileHandler(
            logfile, maxBytes=500*1024, backupCount=2
        )
        handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s'"))
        self.logger.addHandler(handler)

    #---------------------#
    # Pseudo transparency #
    #---------------------#

    def create_pil_background(self,opacity):
        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))

        # Create pseudo transparent background
        w = gtk.gdk.get_default_root_window()
        sz = w.get_size()
        pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,False,8,sz[0],sz[1])
        pb = pb.get_from_drawable(w,w.get_colormap(),0,0,0,0,sz[0],sz[1])

        # Convert Pixbuf to PIL Image
        wh = (pb.get_width(),pb.get_height())
        pilimg = PIL.Image.fromstring("RGB", wh, pb.get_pixels())
        pilimg = pilimg.point(lambda p: (p * (100-opacity)) / 255 )

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
        
        # Apply background
        pixmap, mask = pixbuf.render_pixmap_and_mask()
        self.realize()
        self.window.set_back_pixmap(pixmap, False)




#######################################################
# MAIN
#######################################################
if __name__ == "__main__":
    logout_menu = LogoutMenu()
    logout_menu.run()
