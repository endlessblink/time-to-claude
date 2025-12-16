"""Settings dialog for Claude Usage Monitor."""

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from typing import Callable, Optional

from .. import credentials


class SettingsDialog(Gtk.Dialog):
    """Settings dialog for configuring credentials."""

    def __init__(self, on_save_callback: Optional[Callable] = None):
        super().__init__(title="Claude Usage Monitor - Settings", flags=0)
        self.on_save_callback = on_save_callback

        self.set_default_size(550, 400)
        self.set_border_width(10)

        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Save", Gtk.ResponseType.OK)
        self.connect("response", self._on_response)

        content = self.get_content_area()
        content.set_spacing(10)

        # Instructions
        instructions = Gtk.Label()
        instructions.set_markup(
            "<b>How to get your session key:</b>\n\n"
            "1. Open <a href='https://claude.ai'>claude.ai</a> in your browser\n"
            "2. Log in to your account\n"
            "3. Press F12 to open Developer Tools\n"
            "4. Go to the <b>Network</b> tab\n"
            "5. Click on any request to <b>claude.ai/api/...</b>\n"
            "6. In <b>Request Headers</b>, find the <b>Cookie</b> header\n"
            "7. Copy the value after <b>sessionKey=</b> (starts with sk-ant-...)\n"
            "8. For Org ID: copy the UUID from the URL or request"
        )
        instructions.set_line_wrap(True)
        instructions.set_xalign(0)
        content.pack_start(instructions, False, False, 0)

        content.pack_start(Gtk.Separator(), False, False, 10)

        # Session Key
        session_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        session_label = Gtk.Label(label="Session Key:")
        session_label.set_width_chars(12)
        session_label.set_xalign(0)
        session_box.pack_start(session_label, False, False, 0)

        self.session_entry = Gtk.Entry()
        self.session_entry.set_placeholder_text("sk-ant-...")
        self.session_entry.set_visibility(False)

        # Load existing value
        manual_creds = credentials.get_manual_credentials()
        if manual_creds:
            self.session_entry.set_text(manual_creds[0])

        session_box.pack_start(self.session_entry, True, True, 0)

        show_btn = Gtk.ToggleButton(label="Show")
        show_btn.connect("toggled", lambda b: self.session_entry.set_visibility(b.get_active()))
        session_box.pack_start(show_btn, False, False, 0)

        content.pack_start(session_box, False, False, 0)

        # Organization ID
        org_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        org_label = Gtk.Label(label="Org ID:")
        org_label.set_width_chars(12)
        org_label.set_xalign(0)
        org_box.pack_start(org_label, False, False, 0)

        self.org_entry = Gtk.Entry()
        self.org_entry.set_placeholder_text("xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")

        if manual_creds and manual_creds[1]:
            self.org_entry.set_text(manual_creds[1])

        org_box.pack_start(self.org_entry, True, True, 0)
        content.pack_start(org_box, False, False, 0)

        # Status display
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        # Current source
        creds = credentials.get_credentials()
        if creds:
            source_text = f"Current source: {creds.source}"
        else:
            source_text = "No credentials configured"

        self.status_label = Gtk.Label(label=source_text)
        self.status_label.set_xalign(0)
        status_box.pack_start(self.status_label, True, True, 0)

        content.pack_start(status_box, False, False, 10)

        # Clear button
        clear_btn = Gtk.Button(label="Clear Manual Credentials")
        clear_btn.connect("clicked", self._on_clear)
        content.pack_start(clear_btn, False, False, 0)

        # Help link
        help_link = Gtk.LinkButton.new_with_label(
            "https://claude.ai/settings/usage",
            "Open Claude.ai Usage Page"
        )
        content.pack_start(help_link, False, False, 10)

        self.show_all()

    def _on_clear(self, button: Gtk.Button) -> None:
        """Clear manual credentials."""
        credentials.clear_manual_credentials()
        self.session_entry.set_text("")
        self.org_entry.set_text("")
        self.status_label.set_text("Manual credentials cleared")

    def _on_response(self, dialog: Gtk.Dialog, response_id: int) -> None:
        """Handle dialog response."""
        if response_id == Gtk.ResponseType.OK:
            session_key = self.session_entry.get_text().strip()
            org_id = self.org_entry.get_text().strip()

            if session_key:
                credentials.save_manual_credentials(session_key, org_id)
                if self.on_save_callback:
                    self.on_save_callback()
