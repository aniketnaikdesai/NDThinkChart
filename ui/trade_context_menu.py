"""
trade_context_menu.py
Context menu for active portfolio positions (Phase 7).
"""

from PyQt6.QtWidgets import QMenu


class TradeContextMenu(QMenu):
    """Context menu for position-level actions."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setTitle("Trade Actions")

        # Position-level actions
        self.set_sltp_action = self.addAction("Set Stop-Loss / Take-Profit")
        self.close_position_action = self.addAction("Close Position")
        self.close_group_action = self.addAction("Close Group")
        self.ungroup_action = self.addAction("Ungroup")

        self.addSeparator()

        self.flatten_all_action = self.addAction("Close All Positions")

        # Disabled by default; enabled by the panel based on selection
        for action in (
            self.set_sltp_action,
            self.close_position_action,
            self.close_group_action,
            self.ungroup_action,
        ):
            action.setEnabled(False)

    def set_actions_enabled(self, enabled: bool) -> None:
        """Enable/disable position-level actions."""
        for action in (
            self.set_sltp_action,
            self.close_position_action,
            self.close_group_action,
            self.ungroup_action,
        ):
            action.setEnabled(enabled)
