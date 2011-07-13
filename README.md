About
=====

gtk-logout is a simple and configurable logout menu for linux systems.

Install
=======

Install dependencies:

    sudo aptitude install python-gtk

gtk-logout can optionaly use dbus to easily handle shutdown, reboot, suspend and hibernate actions:

    sudo aptitude install python-dbus consolekit upower policykit-1

If you want extra eye candy you can also install:

* python-cairo if you run a compositing manager
* python-imaging if you don't

Clone the git repository if you haven't already

    git clone git://github.com/ju1ius/gtk-logout.git
    cd gtk-logout

Install:

    sudo make install

Next
====

[Check the wiki](http://github.com/ju1ius/gtk-logout/wiki)
