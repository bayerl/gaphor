"""This module has a generic file dialog functions that are used to open or
save files."""

from __future__ import annotations

import sys
from pathlib import Path

from gi.repository import Gio, Gtk

from gaphor.i18n import gettext

GAPHOR_FILTER = [(gettext("All Gaphor Models"), "*.gaphor", "application/x-gaphor")]


def new_filter(name: str, pattern: str, mime_type: str | None = None) -> Gtk.FileFilter:
    f = Gtk.FileFilter.new()
    f.set_name(name)
    f.add_pattern(pattern)
    if mime_type and sys.platform != "win32":
        f.add_mime_type(mime_type)
    return f


def new_image_filter() -> Gtk.FileFilter:
    f = Gtk.FileFilter.new()
    f.set_name(gettext("Images"))
    f.add_pixbuf_formats()
    return f


def _file_dialog_with_filters(
    title, parent, action, filters, pixbuf_formats: bool
) -> Gtk.FileChooserNative:
    dialog = Gtk.FileChooserNative.new(title, parent, action, None, None)

    if parent:
        dialog.set_transient_for(parent)

    if sys.platform != "darwin":
        if pixbuf_formats:
            dialog.add_filter(new_image_filter())
        else:
            for name, patterns, mime_type in filters:
                dialog.add_filter(new_filter(name, patterns, mime_type))
        dialog.add_filter(new_filter(gettext("All Files"), "*"))
    return dialog


def open_file_dialog(
    title,
    handler,
    parent=None,
    dirname=None,
    filters=None,
    pixbuf_formats: bool = False,
) -> None:
    # if filters is None:
    #     filters = []
    # dialog = _file_dialog_with_filters(
    #     title, parent, Gtk.FileChooserAction.OPEN, filters, pixbuf_formats
    # )
    # dialog.set_select_multiple(True)
    dialog = Gtk.FileDialog.new()
    dialog.set_title(title)

    if dirname:
        dialog.set_initial_folder(Gio.File.parse_name(dirname))

    if filters or pixbuf_formats:
        store = Gio.ListStore.new(Gtk.FileFilter)
        if pixbuf_formats:
            store.append(new_image_filter())
        for name, pattern, mime_type in filters:
            filter = Gtk.FileFilter.new()
            filter.set_name(name)
            filter.add_pattern(pattern)
            filter.add_mime_type(mime_type)
            store.append(filter)
        dialog.set_filters(store)

    def response(dialog, result):
        files = dialog.open_multiple_finish(result)
        handler([Path(f.get_path()) for f in files])

    dialog.open_multiple(parent=parent, cancellable=None, callback=response)


def save_file_dialog(
    title,
    handler,
    parent=None,
    filename=None,
    extension=None,
    filters=None,
) -> Gtk.FileChooser:
    if filters is None:
        filters = []
    dialog = _file_dialog_with_filters(
        title, parent, Gtk.FileChooserAction.SAVE, filters, False
    )

    def get_filename() -> Path:
        return Path(dialog.get_file().get_path())

    def set_filename(filename: Path):
        dialog.set_current_name(str(filename.name))

    def overwrite_check() -> Path | None:
        filename = get_filename()
        if extension and filename.suffix != extension:
            filename = filename.with_suffix(extension)
            set_filename(filename)
            return None if filename.exists() else filename
        return filename

    def response(_dialog, answer):
        if answer == Gtk.ResponseType.ACCEPT:
            if filename := overwrite_check():
                dialog.destroy()
                handler(filename)
            else:
                dialog.show()
        else:
            dialog.destroy()

    dialog.connect("response", response)
    if filename:
        set_filename(filename)
        dialog.set_current_folder(Gio.File.parse_name(str(filename.parent)))
    dialog.set_modal(True)
    dialog.show()
    return dialog
