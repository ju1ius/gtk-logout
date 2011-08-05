package="gtk-logout"
version="0.1-dev"

export prefix=/usr/local
export sysconfdir=/etc

install:
	install -d ${prefix}/lib/gtk-logout
	install -d ${prefix}/lib/gtk-logout/locale
	./install-locale.sh ${prefix}/lib/gtk-logout/locale
	install -m 0755 usr/lib/gtk-logout/* ${prefix}/lib/gtk-logout
	install -d ${sysconfdir}/gtk-logout
	install -m 0755 etc/gtk-logout/* ${sysconfdir}/gtk-logout
	install -m 0755 usr/share/applications/gtk-logout.desktop ${prefix}/share/applications/gtk-logout.desktop
	install -d ${prefix}/bin
	ln -sf -T ${prefix}/lib/gtk-logout/logout.py ${prefix}/bin/gtk-logout

uninstall:
	rm -rf ${prefix}/lib/gtk-logout
	rm -rf ${sysconfdir}/gtk-logout
	rm -f ${prefix}/bin/gtk_logout
