"""Tests for browse TUI configuration."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

try:
    from aweshelf.tui.app import BookmarkBrowser
except ImportError:
    BookmarkBrowser = None


@unittest.skipIf(BookmarkBrowser is None, "textual is not installed")
class BrowseTests(unittest.TestCase):
    def test_help_binding_is_available(self):
        keys = {binding.key for binding in BookmarkBrowser.BINDINGS}
        self.assertIn("question_mark", keys)

    def test_empty_message_is_actionable(self):
        self.assertIn("aweshelf bookmark", BookmarkBrowser.EMPTY_MESSAGE)

    def test_filter_binding_is_available(self):
        keys = {binding.key for binding in BookmarkBrowser.BINDINGS}
        self.assertIn("slash", keys)

    def test_escape_binding_is_available(self):
        keys = {binding.key for binding in BookmarkBrowser.BINDINGS}
        self.assertIn("escape", keys)

    def test_help_text_lists_all_shortcuts(self):
        self.assertIn("/", BookmarkBrowser.HELP_TEXT)
        self.assertIn("Esc", BookmarkBrowser.HELP_TEXT)
        self.assertIn("Enter", BookmarkBrowser.HELP_TEXT)
        self.assertIn("e", BookmarkBrowser.HELP_TEXT)
        self.assertIn("r", BookmarkBrowser.HELP_TEXT)
        self.assertIn("q", BookmarkBrowser.HELP_TEXT)
        self.assertIn("y", BookmarkBrowser.HELP_TEXT)
        self.assertIn("n", BookmarkBrowser.HELP_TEXT)

    def test_resize_bindings_exist(self):
        keys = {binding.key for binding in BookmarkBrowser.BINDINGS}
        self.assertIn("[", keys)
        self.assertIn("]", keys)

    def test_drag_handle_class_exists(self):
        from aweshelf.tui.app import DragHandle
        self.assertFalse(DragHandle.can_focus)

    def test_edit_binding_is_available(self):
        keys = {binding.key for binding in BookmarkBrowser.BINDINGS}
        self.assertIn("e", keys)

    def test_remove_binding_is_available(self):
        keys = {binding.key for binding in BookmarkBrowser.BINDINGS}
        self.assertIn("r", keys)

    def test_mode_toggle_binding(self):
        keys = {binding.key for binding in BookmarkBrowser.BINDINGS}
        self.assertIn("c", keys)
        self.assertNotIn("m", keys)

    def test_sort_cycle_binding(self):
        keys = {binding.key for binding in BookmarkBrowser.BINDINGS}
        self.assertIn("s", keys)

    def test_help_text_lists_mode_and_sort(self):
        self.assertIn("c", BookmarkBrowser.HELP_TEXT)
        self.assertNotIn("m      Toggle Category", BookmarkBrowser.HELP_TEXT)
        self.assertIn("s", BookmarkBrowser.HELP_TEXT)
        self.assertIn("Category", BookmarkBrowser.HELP_TEXT)
        self.assertNotIn("mode", BookmarkBrowser.HELP_TEXT.lower())

    def test_category_colors_defined(self):
        from aweshelf.tui.app import CATEGORY_COLORS
        self.assertGreater(len(CATEGORY_COLORS), 0)

    def test_mode_order(self):
        from aweshelf.tui.app import MODE_ORDER
        self.assertEqual(MODE_ORDER, ["category", "all"])

    def test_default_mode_is_category(self):
        app = BookmarkBrowser()
        self.assertEqual(app._mode, "category")

    def test_browse_columns_align_with_list(self):
        from aweshelf.tui.app import ALL_COLUMNS, CATEGORY_COLUMNS
        self.assertEqual(ALL_COLUMNS, ["ID", "PROVIDER", "TITLE", "CATEGORY", "PROFILE", "SESSION"])
        self.assertEqual(CATEGORY_COLUMNS, ["ID", "PROVIDER", "TITLE", "PROFILE", "SESSION"])

    def test_sort_order(self):
        from aweshelf.tui.app import SORT_ORDER
        self.assertEqual(SORT_ORDER, ["cat_id", "id"])

    def test_cat_key_prefix(self):
        from aweshelf.tui.app import CAT_KEY_PREFIX
        self.assertTrue(CAT_KEY_PREFIX.startswith("__"))

    def test_is_cat_row_skips_category_headers(self):
        from aweshelf.tui.app import CAT_KEY_PREFIX
        app = BookmarkBrowser()
        self.assertTrue(app._is_cat_row(f"{CAT_KEY_PREFIX}backend"))
        self.assertFalse(app._is_cat_row("aweshelf_0001"))
        self.assertFalse(app._is_cat_row(None))

    def test_enter_binding_has_priority(self):
        enter_bindings = [b for b in BookmarkBrowser.BINDINGS if b.key == "enter"]
        self.assertFalse(enter_bindings[0].priority)
        self.assertEqual(enter_bindings[0].description, "Resume selected session")

    def test_normal_shortcuts_include_enter_resume(self):
        from aweshelf.tui.app import NORMAL_SHORTCUT_TEXT
        self.assertIn("enter Resume selected session", NORMAL_SHORTCUT_TEXT)
        self.assertIn("/ Search", NORMAL_SHORTCUT_TEXT)

    def test_edit_shortcuts_describe_inline_cell_editing(self):
        from aweshelf.tui.app import EDIT_SHORTCUT_TEXT
        self.assertIn("enter Save cell", EDIT_SHORTCUT_TEXT)
        self.assertIn("up/down Row", EDIT_SHORTCUT_TEXT)
        self.assertIn("left/right Field", EDIT_SHORTCUT_TEXT)
        self.assertIn("tab Next field", EDIT_SHORTCUT_TEXT)
        self.assertIn("esc Done", EDIT_SHORTCUT_TEXT)

    def test_mode_constants_exist(self):
        from aweshelf.tui.app import (
            MODE_CONFIRM_REMOVE,
            MODE_CONFIRM_RESUME,
            MODE_EDIT,
            MODE_NORMAL,
        )
        self.assertEqual(MODE_NORMAL, "normal")
        self.assertEqual(MODE_EDIT, "edit")
        self.assertEqual(MODE_CONFIRM_RESUME, "confirm_resume")
        self.assertEqual(MODE_CONFIRM_REMOVE, "confirm_remove")


@unittest.skipIf(BookmarkBrowser is None, "textual is not installed")
class BrowseInteractionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self._old_config = os.environ.get("AWESHELF_CONFIG")
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "bookmarks.json"
        self.path.write_text(json.dumps({
            "version": 1,
            "bookmarks": [
                {
                    "id": "aweshelf_0001",
                    "provider": "claude",
                    "session_id": "sess-001",
                    "title": "One",
                    "category": "backend",
                    "project_path": "/tmp",
                    "aweswitch_profile": "cc-glm",
                },
                {
                    "id": "aweshelf_0002",
                    "provider": "codex",
                    "session_id": "sess-002",
                    "title": "Two",
                    "category": "frontend",
                    "project_path": "/tmp",
                    "aweswitch_profile": "codex",
                },
            ],
        }))
        os.environ["AWESHELF_CONFIG"] = str(self.path)

    def tearDown(self):
        if self._old_config is None:
            os.environ.pop("AWESHELF_CONFIG", None)
        else:
            os.environ["AWESHELF_CONFIG"] = self._old_config
        self._tmp.cleanup()

    async def test_category_header_does_not_reuse_previous_selection_for_remove(self):
        from aweshelf.tui.app import MODE_NORMAL

        app = BookmarkBrowser()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("down")
            await pilot.pause()
            self.assertEqual(app._selected.id, "aweshelf_0001")

            await pilot.press("up")
            await pilot.pause()
            await pilot.press("r")
            await pilot.pause()

            self.assertIsNone(app._selected)
            self.assertEqual(app._app_mode, MODE_NORMAL)

    async def test_enter_confirms_remove(self):
        app = BookmarkBrowser()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("down")
            await pilot.pause()
            await pilot.press("r")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

        data = json.loads(self.path.read_text())
        self.assertEqual([b["id"] for b in data["bookmarks"]], ["aweshelf_0002"])

    async def test_edit_mode_edits_current_table_cell(self):
        from aweshelf.tui.app import MODE_EDIT

        app = BookmarkBrowser()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("down")
            await pilot.pause()
            await pilot.press("e")
            await pilot.pause()

            self.assertEqual(app._app_mode, MODE_EDIT)
            self.assertEqual(app._edit_attr, "title")
            self.assertEqual(app.query_one("#table").cursor_type, "cell")
            self.assertEqual(len(list(app.query(".edit-field"))), 0)
            app._edit_value = "Changed"

            await pilot.press("enter")
            await pilot.pause()

            self.assertEqual(app._app_mode, MODE_EDIT)
            self.assertEqual(app._selected.title, "Changed")
            self.assertEqual(len(list(app.query(".edit-field"))), 0)

        data = json.loads(self.path.read_text())
        self.assertEqual(data["bookmarks"][0]["title"], "Changed")

    async def test_edit_tab_moves_between_editable_fields(self):
        app = BookmarkBrowser()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("down")
            await pilot.pause()
            await pilot.press("e")
            await pilot.pause()

            self.assertEqual(app._edit_attr, "title")
            await pilot.press("tab")
            await pilot.pause()

            self.assertEqual(app._edit_attr, "aweswitch_profile")

    async def test_edit_arrow_keys_move_between_editable_cells(self):
        app = BookmarkBrowser()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("down")
            await pilot.pause()
            await pilot.press("e")
            await pilot.pause()

            self.assertEqual(app._selected.id, "aweshelf_0001")
            self.assertEqual(app._edit_attr, "title")

            await pilot.press("right")
            await pilot.pause()

            self.assertEqual(app._selected.id, "aweshelf_0001")
            self.assertEqual(app._edit_attr, "aweswitch_profile")

            await pilot.press("down")
            await pilot.pause()

            self.assertEqual(app._selected.id, "aweshelf_0002")
            self.assertEqual(app._edit_attr, "aweswitch_profile")
            self.assertEqual(app._edit_value, "codex")

            app._edit_value = "cc-glm"
            await pilot.press("enter")
            await pilot.pause()

            self.assertEqual(app._app_mode, "edit")
            self.assertEqual(app._selected.id, "aweshelf_0002")

        data = json.loads(self.path.read_text())
        self.assertEqual(data["bookmarks"][1]["aweswitch_profile"], "cc-glm")

    async def test_edit_escape_returns_to_normal_mode(self):
        from aweshelf.tui.app import MODE_NORMAL

        app = BookmarkBrowser()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("down")
            await pilot.pause()
            await pilot.press("e")
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()

            self.assertEqual(app._app_mode, MODE_NORMAL)
            self.assertEqual(app.query_one("#table").cursor_type, "row")

    async def test_browse_search_matches_first_prompt_and_enter_returns_to_table(self):
        from textual.widgets import DataTable, Input

        data = json.loads(self.path.read_text())
        data["bookmarks"][1]["first_prompt"] = "Investigate billing webhook"
        self.path.write_text(json.dumps(data))

        app = BookmarkBrowser()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("/")
            await pilot.press("w", "e", "b", "h", "o", "o", "k")
            await pilot.pause()

            self.assertEqual(app._filter, "webhook")
            self.assertEqual(app._selected.id, "aweshelf_0002")

            await pilot.press("enter")
            await pilot.pause()

            self.assertTrue(app.query_one("#table", DataTable).has_focus)
            self.assertEqual(app._filter, "webhook")
            self.assertTrue(app.query_one("#search", Input).has_class("visible"))

    async def test_browse_search_escape_clears_filter(self):
        from textual.widgets import DataTable, Input

        app = BookmarkBrowser()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("/")
            await pilot.press("c", "o", "d", "e", "x")
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()

            self.assertEqual(app._filter, "")
            self.assertFalse(app.query_one("#search", Input).has_class("visible"))
            self.assertTrue(app.query_one("#table", DataTable).has_focus)


if __name__ == "__main__":
    unittest.main()
