#! /bin/bash

app_dir=$(dirname $0)
po_dir=$app_dir/po
locale_dir=$app_dir/usr/share/locale
domain="gtk-logout"

rm -rf $locale_dir/*

find "$po_dir" -name *.po | while read po_file
do
  language=$(basename $po_file '.po')
  language_dir="$locale_dir/$language/LC_MESSAGES"
  mkdir -p "$language_dir"
  msgfmt -o "$language_dir/$domain.mo" "$po_file"
done
