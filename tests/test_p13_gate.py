"""P13-T9 batch gate: D49 checklist, history intact, no order code, suite green.

Covers AC-D49.7 and the W8 close-out. Reads the P13-T5 probe artifact and
the requirements text; never re-probes and never re-derives (no live TWS
contact).

Suite-green is verified by running the full offscreen suite itself (this
task's test_command), not by a case in this file — a gate case that shells
out to the whole suite would recurse and double the runtime. The
skip/xfail and order-token scans below are static text matching, so they
are safe to keep in-file.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS = REPO_ROOT / "docs" / "requirements" / "requirements.md"
PROBE_RECORD = REPO_ROOT / "docs" / "p13_hold_probe_record.md"

MARKER_SENTENCE = "This is an existing repository."

# P13 suite files mapped to the AC each one pins (T91). Every P13 wave
# T1-T8 lands one of these; the gate fails on any missing suite.
EXPECTED_SUITES = {
    "test_p13_restore.py": "D49.1",
    "test_p13_attach.py": "D49.2",
    "test_p13_host_error.py": "D49.3",
    "test_p13_fanout.py": "D49.4",
    "test_p13_hold_probe.py": "D49.5",
    "test_p13_hold_fix.py": "D49.5",
    "test_p13_tz_create.py": "D49.6",
    "test_p13_tz_restore.py": "D49.6",
}

# Production files the P13 batch owns (W1-W7, existing modules in place).
P13_PRODUCTION_FILES = [
    "ui/main_window.py",
    "ui/popout_window.py",
    "ui/ticker_session.py",
    "data/popout_store.py",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# P13-T9-T91 — D49 checklist green: every suite present with its AC pinned,
# and D49.5 resolved exactly one way (fix on confirmed effect, else the
# probe record's verified-close verdict cited).
class TestChecklist:
    def test_p13_suites_exist_with_ac_assertions(self):
        missing = []
        unpinned = []
        for name, ac in EXPECTED_SUITES.items():
            path = REPO_ROOT / "tests" / name
            if not path.is_file():
                missing.append(name)
                continue
            if ac not in _read(path):
                unpinned.append(f"{name} (no {ac})")
        assert not missing, f"missing P13 suites: {missing}"
        assert not unpinned, f"suites without AC assertions: {unpinned}"

    def test_ac_d49_1_through_d49_6_present_in_requirements(self):
        text = _read(REQUIREMENTS)
        missing = [f"AC-D49.{n}" for n in range(1, 7)
                   if f"AC-D49.{n}" not in text]
        assert not missing, f"missing ACs: {missing}"

    def test_d49_5_resolves_exactly_one_way(self):
        assert PROBE_RECORD.is_file(), "docs/p13_hold_probe_record.md missing"
        record = _read(PROBE_RECORD)
        lasting = "lasting effect confirmed" in record
        no_effect = "no lasting effect" in record
        assert lasting != no_effect, (
            "D49.5 must resolve exactly one way: either a confirmed lasting "
            "effect (fix branch) or a no-lasting-effect verdict "
            f"(verified-close branch); lasting={lasting} no_effect={no_effect}"
        )
        fix_text = _read(REPO_ROOT / "tests" / "test_p13_hold_fix.py")
        if lasting:
            assert "per-owner" in fix_text, (
                "lasting effect confirmed but the hold-fix suite does not "
                "pin the per-owner fix"
            )
        else:
            # Verified-close branch (P13-T5 verdict): the T6 suite cites the
            # record's verdict and closes D49.5 with no production change.
            assert "verified" in fix_text.lower(), (
                "no lasting effect but the hold-fix suite does not cite "
                "the verified-close verdict"
            )
            assert "p13_hold_probe_record" in fix_text, (
                "verified-close must cite the probe record"
            )


# P13-T9-T92 — requirements history intact (AC-D49.7).
class TestHistoryIntact:
    def test_marker_sentence_present(self):
        assert MARKER_SENTENCE in _read(REQUIREMENTS)

    def test_d41_through_d48_sections_present(self):
        text = _read(REQUIREMENTS)
        missing = [f"### D{n}" for n in range(41, 49) if f"### D{n}" not in text]
        assert not missing, f"missing sections: {missing}"

    def test_current_tech_stack_present(self):
        assert "Current Tech Stack" in _read(REQUIREMENTS)

    def test_reversals_present(self):
        text = _read(REQUIREMENTS)
        for token in ("REVERSED BY D45", "SUPERSEDED BY D41",
                      "REVERSAL of the 2026-10-16 decline",
                      "D48.7", "D49.7"):
            assert token in text, f"reversal/history token missing: {token}"

    def test_ac_d49_7_history_guard_present(self):
        text = _read(REQUIREMENTS)
        assert "AC-D49.7" in text, "AC-D49.7 missing"
        anchor = text.index("AC-D49.7 (history intact")
        window = text[anchor:anchor + 600]
        assert "### D41" in window and "marker sentence" in window, (
            "AC-D49.7 does not guard the D41-D48 sections + marker"
        )

    def test_pre_d49_guards_untouched(self):
        # The recorded history guards of the two previous batches still read
        # intact: D46.7/D47.13/D48.7 each keep their marker + tech-stack line.
        text = _read(REQUIREMENTS)
        for token in ("AC-D46.7", "AC-D47.9", "AC-D48.7"):
            assert token in text, f"pre-D49 guard touched: {token}"


# P13-T9-T93 — no skips/xfails, no order code, no new dependency
# (suite-green verified by the full-suite run).
class TestNoSkipsNoOrders:
    def _p13_test_files(self):
        return sorted(REPO_ROOT.glob("tests/test_p13_*.py"))

    def test_no_skip_or_xfail_markers_in_p13_tests(self):
        # Marker fragments are built indirectly so this file's own source
        # does not literally contain them (it is itself a test_p13_* file).
        skip_mark = "pytest.mark." + "skip"
        xfail_mark = "pytest.mark." + "xfail"
        unittest_skip = "@unittest." + "skip"
        offenders = []
        for path in self._p13_test_files():
            text = path.read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), start=1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if (skip_mark in line or xfail_mark in line
                        or unittest_skip in line):
                    # Ignore this file's own indirect marker definitions above.
                    if path.name == "test_p13_gate.py" and (
                            "skip_mark" in line or "xfail_mark" in line
                            or "unittest_skip" in line):
                        continue
                    offenders.append(f"{path.name}:{lineno}")
        assert not offenders, f"skip/xfail markers found: {offenders}"

    def test_no_order_code_tokens_in_p13_tests(self):
        # Token fragments are built indirectly so this file's own source
        # does not literally contain them (it is itself a test_p13_* file).
        tokens = ["place" + "Order", "cancel" + "Order",
                  "reqGlobal" + "Cancel", "ibkr" + ".orders",
                  "User" + "Order"]
        offenders = []
        for path in self._p13_test_files():
            text = path.read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), start=1):
                if line.strip().startswith("#"):
                    continue
                if path.name == "test_p13_gate.py" and "tokens" in line:
                    continue
                for token in tokens:
                    if token in line:
                        offenders.append(f"{path.name}:{lineno}:{token}")
        assert not offenders, f"order-code tokens found: {offenders}"

    def test_no_order_code_in_p13_production_files(self):
        tokens = ["place" + "Order", "cancel" + "Order",
                  "reqGlobal" + "Cancel"]
        offenders = []
        for rel in P13_PRODUCTION_FILES:
            text = _read(REPO_ROOT / rel)
            for lineno, line in enumerate(text.splitlines(), start=1):
                for token in tokens:
                    if token in line:
                        offenders.append(f"{rel}:{lineno}:{token}")
        assert not offenders, f"order-code tokens found: {offenders}"
        assert not (REPO_ROOT / "ibkr" / "orders.py").exists(), (
            "ibkr/orders module reintroduced"
        )

    def test_no_new_dependency(self):
        # P13 lands in existing files in place: no new top-level production
        # module and no requirements change ride with this batch.
        new_modules = [p for p in REPO_ROOT.glob("ui/*.py")
                       if p.name not in (
                           "__init__.py", "active_portfolio_panel.py",
                           "add_symbol_dialog.py", "alarm_dialog.py",
                           "alarm_edit_dialog.py", "chart_controls.py",
                           "chart_mouse_router.py", "chart_view.py",
                           "dock_layout.py", "drawing_groups_dialog.py",
                           "drawing_settings_common.py", "drawing_tools.py",
                           "horizontal_line_settings_dialog.py",
                           "lwc_bridge.py", "lwc_host.py", "lwc_view.py",
                           "main_window.py", "popout_window.py",
                           "studies_dialog.py", "ticker_session.py",
                           "toast.py", "visual_conventions.py",
                           "watchlist_panel.py",
                           "zone_settings_dialog.py")]
        assert not new_modules, f"new modules: {[p.name for p in new_modules]}"
