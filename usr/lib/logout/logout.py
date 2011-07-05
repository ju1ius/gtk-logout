#! /usr/bin/python

import os, sys, string, ConfigParser, StringIO
import pygtk
pygtk.require('2.0')

try:
    import gtk
except:
    print "pyGTK missing, install python-gtk2"
    sys.exit()

try:
    import gettext
except Exception, detail:
	print detail
	sys.exit(1)


class LogoutMenu(object):

    _dbus_actions =   ['restart', 'shutdown', 'suspend', 'hibernate']
    _actions = {
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
        # Initialize i18n
        gettext.install(
            "messages",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "locale"),
            unicode=1
        )
        # Load configuration file
        self.load_config(config_paths)
        # Start the window
        self.init_window()


    def load_config(self, config_paths):
        """ Load the configuration file and parse entries, when encountering a issue
            change safe defaults """
        self.config = {}
        
        valid_actions = self._actions.keys()
        self.config['buttons'] = ['logout','restart','shutdown']

        # Config Defaults
        defaults = StringIO.StringIO("""
[Settings]
theme: fancy
logo: off
usedbus: True
effects: True
opacity: 80
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

        self.config['theme'] = config_parser.get("Settings", "theme")
        
        try:
            self.config['logo'] = config_parser.getboolean("Settings", "logo")
        except ValueError:
            if not os.path.isabs(self.config['logo']):
                self.config['logo'] = os.path.abspath(os.path.join(
                    os.path.dirname(__file__), self.config['logo']
                ))

        self.config['usedbus'] = config_parser.getboolean("Settings","usedbus")
        # Instanciate the DBusController
        if self.config['usedbus']:
            from dbushandler import DbusController
            self.dbus = DbusController()

        self.config['effects'] = config_parser.getboolean("Settings","effects")
        opacity = config_parser.getfloat("Settings","opacity")
        if opacity > 100 or opacity <= 0:
            opacity = 75
        self.config['opacity'] = opacity

        buttons = [btn.strip() for btn in config_parser.get('Settings', 'buttons').split(',')]
        for button in buttons:
            if not button in valid_actions:
                buttons.remove(button)
            else:
                if self.config['usedbus'] and button in self._dbus_actions:
                    if not self.dbus.check_ability(button):
                        buttons.remove(button)
        if not 'cancel' in buttons: buttons.append('cancel')
        if len(buttons) > 1: self.config['buttons'] = buttons

        print self.config

        # Parse in commands section of the configuration file. Check for valid keys and set the attribs on self
        if config_parser.has_section('Commands'):
            for key in config_parser.items("Commands"):
                if key[0] in valid_actions:
                    if key[1]: self._actions[key[0]]['command'] = key[1]

        if config_parser.has_section('Icons'):
            for key in config_parser.items('Icons'):
                if key[0] in valid_actions:
                    if key[1]: self._actions[key[0]]['icon'] = key[1]


    def init_window(self):
        module_name = "logout_" + self.config['theme']
        module = __import__(module_name)
        self.window = module.get_window(self)
        self.window.set_urgency_hint(True)
        self.window.set_skip_pager_hint(True)
        self.window.set_skip_taskbar_hint(True)
        self.window.connect("destroy", self.quit)
        

    def on_button_clicked(self, widget, action=None):
        if action in self._dbus_actions and self.config['usedbus']:
            method = getattr(self.dbus, action)
            method()
        else:
            self.exec_cmd(self._actions[action]['command'])
        self.quit()


    def exec_cmd(self, cmdline):
        os.system(cmdline)


    def quit(self, widget=None, data=None):
        gtk.main_quit()


    def run(self):
        self.window.show_all()
        gtk.main()




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
