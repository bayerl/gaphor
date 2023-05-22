import os.path
from pathlib import Path

import pytest
from gi.repository import Gio, Gtk

from gaphor.ui.filedialog import save_file_dialog


class FileDialogMock(Gtk.FileDialog):
    def __init__(self):
        super().__init__()
        self._save_response = Gio.File.parse_name("/unset")

    def save(self, parent, cancellable, callback):
        self.save_callback = callback
        callback(self, "mock result")

    def save_finish(self, result):
        return self._save_response

    def define_response(self, response):
        self._save_response = Gio.File.parse_name(response)


@pytest.fixture
def file_dialog(monkeypatch):
    stub = FileDialogMock()

    def new_file_dialog():
        return stub

    monkeypatch.setattr("gi.repository.Gtk.FileDialog.new", new_file_dialog)
    return stub


def test_save_dialog(file_dialog):
    file_dialog.define_response("/test/path/model.gaphor")
    selected_file = None

    def save_handler(f):
        nonlocal selected_file
        selected_file = f

    save_file_dialog(
        "title",
        save_handler,
        filename=None,
        extension=".gaphor",
        filters=[],
    )

    assert selected_file.parts == (os.path.sep, "test", "path", "model.gaphor")


def test_save_dialog_with_full_file_name(file_dialog):
    selected_file = None

    def save_handler(f):
        nonlocal selected_file
        selected_file = f

    filename = Path("/test/path/model.gaphor")
    save_file_dialog(
        "title",
        save_handler,
        filename=filename,
        extension=".gaphor",
        filters=[],
    )

    assert file_dialog.get_initial_name() == filename.name


def test_save_dialog_filename_without_extension(file_dialog):
    file_dialog.define_response("/test/path/model")
    selected_file = None

    def save_handler(f):
        nonlocal selected_file
        selected_file = f

    save_file_dialog(
        "title",
        save_handler,
        filename=None,
        extension=".gaphor",
        filters=[],
    )

    assert selected_file.parts == (os.path.sep, "test", "path", "model.gaphor")
