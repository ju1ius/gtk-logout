package="gtk-logout"
version="1.0-dev"

export prefix=/usr/local
export sysconfdir=/etc

install:
	install -d ${prefix}/lib/gtk-logout
	install -m 0755 usr/lib/gtk-logout/* ${prefix}/lib/gtk-logout
	install -d ${sysconfdir}/gtk-logout
	install -m 0755 etc/gtk-logout/* ${sysconfdir}/gtk-logout
	install -d ${prefix}/bin
	ln -sf -T ${prefix}/lib/gtk-logout/logout.py ${prefix}/bin/gtk-logout

uninstall:
	rm -rf ${prefix}/lib/gtk-logout
	rm -rf ${sysconfdir}/gtk-logout
	rm -f ${prefix}/bin/gtk_logout
