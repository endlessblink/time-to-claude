"""Settings dialog for Claude Usage Monitor."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QCheckBox
)
from PySide6.QtCore import Qt

from . import credentials


class SettingsDialog(QDialog):
    """Settings dialog for configuring credentials."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.dark_mode = credentials.is_dark_mode()

        self.setWindowTitle("Claude Usage Monitor - Settings")
        self.setFixedSize(500, 520)

        if self.dark_mode:
            self.setStyleSheet("""
                QDialog {
                    background-color: #1F2937;
                }
                QLabel {
                    color: #E5E7EB;
                }
                QLineEdit {
                    padding: 8px 12px;
                    border: 1px solid #4B5563;
                    border-radius: 6px;
                    background-color: #374151;
                    color: #F9FAFB;
                    font-size: 13px;
                }
                QLineEdit:focus {
                    border-color: #3B82F6;
                    background-color: #4B5563;
                    color: #F9FAFB;
                }
                QPushButton {
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: 500;
                }
                QCheckBox {
                    color: #E5E7EB;
                    font-size: 13px;
                    spacing: 8px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border: 2px solid #4B5563;
                    border-radius: 4px;
                    background-color: #374151;
                }
                QCheckBox::indicator:checked {
                    background-color: #3B82F6;
                    border-color: #3B82F6;
                }
                QCheckBox::indicator:hover {
                    border-color: #3B82F6;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog {
                    background-color: #FFFFFF;
                }
                QLabel {
                    color: #374151;
                }
                QLineEdit {
                    padding: 8px 12px;
                    border: 1px solid #D1D5DB;
                    border-radius: 6px;
                    background-color: #F9FAFB;
                    color: #1F2937;
                    font-size: 13px;
                }
                QLineEdit:focus {
                    border-color: #3B82F6;
                    background-color: #FFFFFF;
                    color: #1F2937;
                }
                QPushButton {
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: 500;
                }
                QCheckBox {
                    color: #374151;
                    font-size: 13px;
                    spacing: 8px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border: 2px solid #D1D5DB;
                    border-radius: 4px;
                    background-color: #FFFFFF;
                }
                QCheckBox::indicator:checked {
                    background-color: #3B82F6;
                    border-color: #3B82F6;
                }
                QCheckBox::indicator:hover {
                    border-color: #3B82F6;
                }
            """)

        # Theme-specific colors
        if self.dark_mode:
            title_color = "#F9FAFB"
            instructions_color = "#9CA3AF"
            sep_color = "#4B5563"
            btn_bg = "#374151"
            btn_border = "#4B5563"
            btn_text = "#E5E7EB"
            btn_hover_bg = "#4B5563"
            btn_checked_bg = "#1E3A5F"
            self.error_color = "#FCA5A5"
        else:
            title_color = "#1F2937"
            instructions_color = "#6B7280"
            sep_color = "#E5E7EB"
            btn_bg = "#F3F4F6"
            btn_border = "#D1D5DB"
            btn_text = "#374151"
            btn_hover_bg = "#E5E7EB"
            btn_checked_bg = "#DBEAFE"
            self.error_color = "#DC2626"

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        title = QLabel("Settings")
        title.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {title_color};")
        layout.addWidget(title)

        # Instructions
        instructions = QLabel(
            "<b>How to get your session key:</b><br><br>"
            "1. Open <a href='https://claude.ai'>claude.ai</a> and log in<br>"
            "2. Press <b>F12</b> to open Developer Tools<br>"
            "3. Find the Cookies:<br>"
            "&nbsp;&nbsp;&nbsp;<b>Firefox:</b> Storage tab → Cookies → claude.ai<br>"
            "&nbsp;&nbsp;&nbsp;<b>Chrome:</b> Application tab → Cookies → claude.ai<br>"
            "4. Find <b>sessionKey</b> and copy its Value<br>"
            "5. Paste it in the field below<br><br>"
            "<b>Organization ID</b> (optional):<br>"
            "Go to claude.ai/settings → copy UUID from URL after /organization/"
        )
        instructions.setWordWrap(True)
        instructions.setOpenExternalLinks(True)
        instructions.setStyleSheet(f"color: {instructions_color}; font-size: 12px; line-height: 1.5;")
        layout.addWidget(instructions)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {sep_color};")
        layout.addWidget(sep)

        # Session Key
        session_layout = QVBoxLayout()
        session_layout.setSpacing(6)

        session_label = QLabel("Session Key")
        session_layout.addWidget(session_label)

        session_row = QHBoxLayout()
        self.session_entry = QLineEdit()
        self.session_entry.setPlaceholderText("sk-ant-sid01-...")
        self.session_entry.setEchoMode(QLineEdit.EchoMode.Password)
        session_row.addWidget(self.session_entry)

        self.show_btn = QPushButton("Show")
        self.show_btn.setCheckable(True)
        self.show_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_bg};
                border: 1px solid {btn_border};
                color: {btn_text};
            }}
            QPushButton:hover {{
                background-color: {btn_hover_bg};
            }}
            QPushButton:checked {{
                background-color: {btn_checked_bg};
                border-color: #3B82F6;
                color: #3B82F6;
            }}
        """)
        self.show_btn.toggled.connect(self._toggle_visibility)
        session_row.addWidget(self.show_btn)

        session_layout.addLayout(session_row)
        layout.addLayout(session_layout)

        # Organization ID
        org_layout = QVBoxLayout()
        org_layout.setSpacing(6)

        org_label = QLabel("Organization ID (optional)")
        org_layout.addWidget(org_label)

        self.org_entry = QLineEdit()
        self.org_entry.setPlaceholderText("xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
        org_layout.addWidget(self.org_entry)

        layout.addLayout(org_layout)

        # Dark mode toggle
        self.dark_mode_check = QCheckBox("Dark mode")
        self.dark_mode_check.setChecked(credentials.is_dark_mode())
        self.dark_mode_check.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.dark_mode_check)

        # Load existing credentials
        manual_creds = credentials.get_manual_credentials()
        if manual_creds:
            self.session_entry.setText(manual_creds[0])
            if manual_creds[1]:
                self.org_entry.setText(manual_creds[1])

        # Status
        creds = credentials.get_credentials()
        if creds:
            status_text = f"Current source: {creds.source}"
        else:
            status_text = "No credentials configured"

        self.status_label = QLabel(status_text)
        self.status_label.setStyleSheet(f"color: {instructions_color}; font-size: 12px;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()

        clear_btn = QPushButton("Clear Credentials")
        if self.dark_mode:
            clear_btn.setStyleSheet("""
                QPushButton {
                    background-color: #7F1D1D;
                    border: 1px solid #991B1B;
                    color: #FCA5A5;
                }
                QPushButton:hover {
                    background-color: #991B1B;
                }
            """)
        else:
            clear_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FEE2E2;
                    border: 1px solid #FECACA;
                    color: #DC2626;
                }
                QPushButton:hover {
                    background-color: #FECACA;
                }
            """)
        clear_btn.clicked.connect(self._clear_credentials)
        btn_layout.addWidget(clear_btn)

        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_bg};
                border: 1px solid {btn_border};
                color: {btn_text};
            }}
            QPushButton:hover {{
                background-color: {btn_hover_bg};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                border: none;
                color: white;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _toggle_visibility(self, checked):
        """Toggle password visibility."""
        if checked:
            self.session_entry.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_btn.setText("Hide")
        else:
            self.session_entry.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_btn.setText("Show")

    def _clear_credentials(self):
        """Clear saved credentials."""
        credentials.clear_manual_credentials()
        self.session_entry.clear()
        self.org_entry.clear()
        self.status_label.setText("Credentials cleared")

    def _save(self):
        """Save credentials and settings, then close."""
        session_key = self.session_entry.text().strip()
        org_id = self.org_entry.text().strip()

        # Save dark mode setting
        credentials.set_dark_mode(self.dark_mode_check.isChecked())

        if session_key:
            credentials.save_manual_credentials(session_key, org_id)
            self.accept()
        else:
            self.status_label.setText("Session key is required")
            self.status_label.setStyleSheet(f"color: {self.error_color}; font-size: 12px;")
