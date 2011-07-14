#! /bin/bash

po_dir="./po"
localedir="./usr/lib/gtk-logout/locale"
domain="gtk-logout"

find "$po_dir" -name *.po | while read po_file
do
  language=$(basename $po_file '.po')
  domain_dir="$localedir/$language/LC_MESSAGES"
  mkdir -p "$domain_dir"
  msgfmt -o "$domain_dir/$domain.mo" "$po_file"
done
