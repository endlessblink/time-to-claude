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

        self.setWindowTitle("Claude Usage Monitor - Settings")
        self.setFixedSize(500, 450)
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
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #3B82F6;
                background-color: #FFFFFF;
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

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 18px; font-weight: 600; color: #1F2937;")
        layout.addWidget(title)

        # Instructions
        instructions = QLabel(
            "<b>How to get your session key:</b><br><br>"
            "1. Open <a href='https://claude.ai'>claude.ai</a> in your browser<br>"
            "2. Log in to your account<br>"
            "3. Press F12 to open Developer Tools<br>"
            "4. Go to <b>Application</b> → <b>Cookies</b> → <b>claude.ai</b><br>"
            "5. Find <b>sessionKey</b> and copy its value<br>"
            "6. (Optional) Copy your Organization ID from the URL"
        )
        instructions.setWordWrap(True)
        instructions.setOpenExternalLinks(True)
        instructions.setStyleSheet("color: #6B7280; font-size: 12px; line-height: 1.5;")
        layout.addWidget(instructions)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #E5E7EB;")
        layout.addWidget(sep)

        # Session Key
        session_layout = QVBoxLayout()
        session_layout.setSpacing(6)

        session_label = QLabel("Session Key")
        session_label.setStyleSheet("font-weight: 500;")
        session_layout.addWidget(session_label)

        session_row = QHBoxLayout()
        self.session_entry = QLineEdit()
        self.session_entry.setPlaceholderText("sk-ant-sid01-...")
        self.session_entry.setEchoMode(QLineEdit.EchoMode.Password)
        session_row.addWidget(self.session_entry)

        self.show_btn = QPushButton("Show")
        self.show_btn.setCheckable(True)
        self.show_btn.setStyleSheet("""
            QPushButton {
                background-color: #F3F4F6;
                border: 1px solid #D1D5DB;
                color: #374151;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
            QPushButton:checked {
                background-color: #DBEAFE;
                border-color: #3B82F6;
                color: #1D4ED8;
            }
        """)
        self.show_btn.toggled.connect(self._toggle_visibility)
        session_row.addWidget(self.show_btn)

        session_layout.addLayout(session_row)
        layout.addLayout(session_layout)

        # Organization ID
        org_layout = QVBoxLayout()
        org_layout.setSpacing(6)

        org_label = QLabel("Organization ID (optional)")
        org_label.setStyleSheet("font-weight: 500;")
        org_layout.addWidget(org_label)

        self.org_entry = QLineEdit()
        self.org_entry.setPlaceholderText("xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
        org_layout.addWidget(self.org_entry)

        layout.addLayout(org_layout)

        # Dark mode toggle
        self.dark_mode_check = QCheckBox("Dark mode popup")
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
        self.status_label.setStyleSheet("color: #6B7280; font-size: 12px;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()

        clear_btn = QPushButton("Clear Credentials")
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
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F3F4F6;
                border: 1px solid #D1D5DB;
                color: #374151;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
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
            self.status_label.setStyleSheet("color: #DC2626; font-size: 12px;")
