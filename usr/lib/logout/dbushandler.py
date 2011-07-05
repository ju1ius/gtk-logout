#!/usr/bin/python
# coding=utf-8

import os, dbus

class DbusController(object):
    """ DbusController handles all DBus actions required by logout and acts
        as a middle layer between the application and Dbus"""

    @property
    def consolekit(self):
        """ConsoleKit controller object"""
        if not hasattr (DbusController, "_consolekit"):
            DbusController._consolekit  = ConsoleKit()
        return DbusController._consolekit

    @property
    def upower (self):
        """UPower controller object"""
        if not hasattr (DbusController, "_upower"):
            DbusController._upower  = UPower()
        return DbusController._upower

    def restart(self):
        """Restart the system via ConsoleKit"""
        self.consolekit.restart()

    def shutdown(self):
        """Shutdown the system via ConsoleKit"""
        self.consolekit.shutdown()

    def suspend(self):
        """Suspend the system via UPower"""
        self.upower.suspend()

    def hibernate(self):
        """Hibernate the system via UPower"""
        self.upower.hibernate()

    def check_ability(self, action):
        """Check if Service can complete action type requests, for example, suspend, hiberate, and safesuspend"""
        method_name = 'can_' + action
        try:
            if action in ['suspend', 'hibernate']:
                return getattr(self.upower, method_name)
            elif action in ['shutdown', 'restart']:
                return getattr(self.consolekit, method_name)
        except dbus.DBusException:
            return False
        return True




class PolicyKit(object):
    """Wrapper for PolicyKit which hides some of the differences between
        different PolicyKit versions."""

    valid_versions = ["1", "0"]
    _version = None

    @property
    def systembus(self):
        if not hasattr(PolicyKit, "_systembus"):
            PolicyKit._systembus = dbus.SystemBus()
        return PolicyKit._systembus

    @property
    def sessionbus(self):
        """Session DBus"""
        if not hasattr(PolicyKit, "_sessionbus"):
            PolicyKit._sessionbus = dbus.SessionBus()
        return PolicyKit._sessionbus

    @property
    def version(self):
        if not hasattr(PolicyKit, '_version') or PolicyKit._version == None:
            self._check_version()
        return PolicyKit._version

    @property
    def auth_interface(self):
        if not hasattr(PolicyKit, '_auth_interface'):
            self._check_version()
        return PolicyKit._auth_interface

    @property
    def interface(self):
        if not hasattr(PolicyKit, '_interface'):
            self._check_version()
        return PolicyKit._interface


    def is_authorized(self, action_id):
        """ Check if we have permissions for a action """
        try:
            if self.version == "1":
                (is_auth, _, details) = self.interface.CheckAuthorization(
                    ('unix-process', {
                        'pid': dbus.UInt32(os.getpid(), variant_level=1),
                        'start-time':dbus.UInt64(0,variant_level=1)
                    }),
                    action_id, {}, dbus.UInt32(0), '', timeout=600
                )
                return bool(is_auth)
            elif self.version == "0":
                pass
        except dbus.DBusException:
            return False


    def obtain_authorization(self, action_id):
        try:
            if self.version == "1":
                (granted, _, details) = self.interface.CheckAuthorization(
                    ('unix-process', {
                        'pid': dbus.UInt32(os.getpid(), variant_level=1),
                        'start-time':dbus.UInt64(0, variant_level=1)
                    }),
                    action_id, {}, dbus.UInt32(1), '', timeout=600
                )
                print "Obtained:", granted
                return bool(granted)
            elif self.version == "0":
                pass
        except dbus.DBusException:
            return False


    def get_permissions(self, action_id):
        """ Check if we have permissions for a action, if not, try to obtain them via PolicyKit """
        if self.is_authorized(action_id):
            return True
        else:
            return self.obtain_authorization(action_id)


    def _check_version(self):
        if not self._version:
            params = {
                "0": (
                  "org.freedesktop.PolicyKit",  # name
                  "/",                          # path
                  "org.freedesktop.PolicyKit"   # interface
                ),
                "1": (
                  "org.freedesktop.PolicyKit1",
                  "/org/freedesktop/PolicyKit1/Authority",
                  "org.freedesktop.PolicyKit1.Authority"
                )
            }
            available = {}
            for (version, version_params) in params.iteritems():
                (name, path, interface) = version_params
                try:
                    available[version] = dbus.Interface(
                      self.systembus.get_object(name, path),
                      interface
                    )
                except dbus.DBusException:
                    pass
            if "1" in self.valid_versions and "1" in available:
                PolicyKit._version = "1"
                PolicyKit._auth_interface = None
                PolicyKit._interface = available["1"]
            elif "0" in self.valid_versions and "0" in available:
                PolicyKit._version = "0"
                PolicyKit._auth_interface = dbus.Interface(
                  self.sessionbus.get_object(
                    "org.freedesktop.PolicyKit.AuthenticationAgent", "/"
                  ),
                  "org.freedesktop.PolicyKit.AuthenticationAgent"
                )
                PolicyKit._interface = available["0"]
            else:
                raise OSError("Cannot determine valid PolicyKit version.")




class DBusService(object):

    @property
    def systembus(self):
        """System DBus"""
        if not hasattr (DBusService, "_systembus"):
            DBusService._systembus = dbus.SystemBus()
        return DBusService._systembus

    @property
    def sessionbus (self):
        """Session DBus"""
        if not hasattr (DBusService, "_sessionbus"):
            DBusService._sessionbus = dbus.SessionBus()
        return DBusService._sessionbus

    @property
    def policykit (self):
        """PolicyKit object"""
        if not hasattr (DBusService, "_policykit"):
            DBusService._policykit = PolicyKit()
        return DBusService._policykit




class ConsoleKit(DBusService):

    @property
    def can_restart(self):
        return self.interface.CanRestart()

    @property
    def can_shutdown(self):
        return self.interface.CanStop()

    @property
    def interface(self):
        if not hasattr(ConsoleKit, '_interface'):
            ConsoleKit._interface  = dbus.Interface(
                self.systembus.get_object(
                    "org.freedesktop.ConsoleKit", "/org/freedesktop/ConsoleKit/Manager"
                ),
                "org.freedesktop.ConsoleKit.Manager"
            )
        return ConsoleKit._interface

    def restart(self):
        """Restart the system via ConsoleKit"""
        if self.count_sessions() > 1:
            if not self.policykit.get_permissions("org.freedesktop.consolekit.system.restart-multiple-users"):
                return False
        else:
            if not self.policykit.get_permissions("org.freedesktop.consolekit.system.restart"):
                return False
        self.interface.Restart()

    def shutdown(self):
        """Shutdown the system via ConsoleKit"""
        if self.count_sessions() > 1:
            if not self.policykit.get_permissions("org.freedesktop.consolekit.system.stop-multiple-users"):
                return False
        else:
            if not self.policykit.get_permissions("org.freedesktop.consolekit.system.stop"):
                return False
        self.interface.Stop()

    def count_sessions(self):
        """ Using DBus and ConsoleKit, get the number of sessions. This is used by PolicyKit to dictate the
            multiple sessions permissions for the various reboot/shutdown commands """
        # Check the number of active sessions
        cnt = 0
        seats = self.interface.GetSeats ()
        for sid in seats:
            seat_obj = self.systembus.get_object('org.freedesktop.ConsoleKit', sid)
            seat = dbus.Interface (seat_obj, 'org.freedesktop.ConsoleKit.Seat')
            cnt += len(seat.GetSessions())
        return cnt





class UPower(DBusService):

    @property
    def can_suspend(self):
        return self.interface.SuspendAllowed()

    @property
    def can_hibernate(self):
        return self.interface.HibernateAllowed()

    @property
    def interface(self):
        if not hasattr(UPower, '_interface'):
            UPower._interface  = dbus.Interface(
                self.systembus.get_object(
                    "org.freedesktop.UPower", "/org/freedesktop/UPower"
                ),
                "org.freedesktop.UPower"
            )
        return ConsoleKit._interface

    def suspend(self):
        """Suspend the system via UPower"""
        if not self.policykit.get_permissions("org.freedesktop.upower.suspend"):
            return False
        self.interface.Suspend(ignore_reply=True)

    def hibernate(self):
        """Hibernate the system via UPower"""
        if not self.policykit.get_permissions("org.freedesktop.upower.hibernate"):
            return False
        self.interface.Hibernate(ignore_reply=True)

