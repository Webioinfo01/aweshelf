"""TUI browse app using textual."""

from contextlib import suppress

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Header, Input, Static

from aweshelf.lib.store import filter_bookmarks, format_bookmark_detail, load_bookmarks, remove_bookmark, update_bookmark
from aweshelf.types import Bookmark

SIDEBAR_FRAC = 60
DETAIL_FRAC = 40
MIN_FRAC = 10
FIRST_PROMPT_EDGE_CHARS = 350
CATEGORY_COLORS = ["green", "orange", "red", "cyan", "magenta"]
MODE_ORDER = ["category", "all"]
SORT_ORDER = ["cat_id", "id"]
CAT_KEY_PREFIX = "__cat__"
ALL_COLUMNS = ["ID", "PROVIDER", "TITLE", "CATEGORY", "PROFILE", "SESSION"]
CATEGORY_COLUMNS = ["ID", "PROVIDER", "TITLE", "PROFILE", "SESSION"]
EDITABLE_ATTRS_ALL = ["title", "category", "aweswitch_profile"]
EDITABLE_ATTRS_CATEGORY = ["title", "aweswitch_profile"]
ATTR_COLUMNS = {
    "title": "TITLE",
    "category": "CATEGORY",
    "aweswitch_profile": "PROFILE",
}
NORMAL_SHORTCUT_TEXT = (
    "enter Resume selected session   q Quit   e Edit   r Remove   "
    "c Category   s Sort   / Search   esc Cancel"
)
EDIT_SHORTCUT_TEXT = (
    "enter Save cell   delete Clear cell   up/down Row   left/right Field   tab Next field   esc Done"
)
CONFIRM_SHORTCUT_TEXT = "enter/y Confirm   esc/n Cancel"

MODE_NORMAL = "normal"
MODE_EDIT = "edit"
MODE_CONFIRM_RESUME = "confirm_resume"
MODE_CONFIRM_REMOVE = "confirm_remove"

class DragHandle(Static):
    """1-cell vertical divider that can be dragged to resize panels."""

    can_focus = False

    DEFAULT_CSS = """
    DragHandle {
        width: 1;
        height: 1fr;
        background: $primary-background;
    }
    """

    def on_mouse_down(self, event) -> None:
        app = self.app
        app._dragging = True
        app._drag_start_x = event.screen_x
        sidebar = app.query_one("#sidebar")
        detail = app.query_one("#detail")
        app._drag_start_sidebar = int(sidebar.styles.width.value) if sidebar.styles.width else SIDEBAR_FRAC
        app._drag_start_detail = int(detail.styles.width.value) if detail.styles.width else DETAIL_FRAC
        self.capture_mouse()

    def on_mouse_move(self, event) -> None:
        app = self.app
        if not app._dragging:
            return
        total = app._drag_start_sidebar + app._drag_start_detail
        delta = event.screen_x - app._drag_start_x
        new_sidebar = max(MIN_FRAC, min(total - MIN_FRAC, app._drag_start_sidebar + delta))
        app.query_one("#sidebar").styles.width = f"{new_sidebar}fr"
        app.query_one("#detail").styles.width = f"{total - new_sidebar}fr"

    def on_mouse_up(self, event) -> None:
        if self.app._dragging:
            self.app._dragging = False
            self.release_mouse()


class BookmarkBrowser(App):
    """Browse and select bookmarks."""

    EMPTY_MESSAGE = "No bookmarks found. Run aweshelf bookmark first."
    HELP_TEXT = "\n".join([
        "/      Filter bookmarks",
        "Esc    Clear filter / cancel",
        "Enter  Resume selected session",
        "e      Edit bookmark",
        "r      Remove bookmark",
        "y      Confirm action",
        "n      Cancel action",
        "c      Toggle Category / All",
        "s      Cycle sort order",
        "?      Show this help",
        "q      Quit",
        "[ / ]  Shrink / grow sidebar",
    ])

    BINDINGS = [
        Binding("enter", "resume", "Resume selected session"),
        Binding("q", "quit", "Quit"),
        Binding("e", "edit", "Edit"),
        Binding("r", "remove", "Remove"),
        Binding("c", "toggle_mode", "Category"),
        Binding("s", "cycle_sort", "Sort"),
        Binding("question_mark", "help", "Help", show=False),
        Binding("slash", "focus_search", "Filter", show=False),
        Binding("escape", "clear_search", "Cancel"),
        Binding("[", "resize_sidebar(-5)", "Shrink sidebar", show=False),
        Binding("]", "resize_sidebar(5)", "Grow sidebar", show=False),
    ]

    CSS = """
    Screen {
        layout: horizontal;
    }
    #sidebar {
        width: 60fr;
    }
    #search {
        display: none;
        dock: top;
        height: 3;
        margin: 0 1;
    }
    #search.visible {
        display: block;
    }
    #detail {
        width: 40fr;
        padding: 1 2;
    }
    #detail-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    #shortcuts {
        dock: bottom;
        height: 1;
        padding: 0 1;
        background: $panel;
        color: $text-muted;
    }
    """

    def __init__(self):
        super().__init__()
        self._bookmarks: list[Bookmark] = []
        self._visible_bookmark_ids: list[str] = []
        self._selected: Bookmark | None = None
        self._filter: str = ""
        self._mode: str = MODE_ORDER[0]
        self._sort_order: str = SORT_ORDER[0]
        self._app_mode: str = MODE_NORMAL
        self._edit_attr: str | None = None
        self._edit_value: str = ""
        self._dragging: bool = False
        self._drag_start_x: int = 0
        self._drag_start_sidebar: int = SIDEBAR_FRAC
        self._drag_start_detail: int = DETAIL_FRAC

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Input(placeholder="Filter bookmarks...", id="search")
                yield DataTable(id="table")
            yield DragHandle()
            with Vertical(id="detail"):
                yield Static("Select a bookmark to view details.", id="detail-title")
                yield Static("", id="detail-body")
        yield Static(self._format_shortcuts(NORMAL_SHORTCUT_TEXT), id="shortcuts")

    def on_mount(self) -> None:
        table = self.query_one("#table", DataTable)
        table.cursor_type = "row"
        self._load_data()
        table.focus()
        self._update_shortcuts()

    def _is_normal(self) -> bool:
        return self._app_mode == MODE_NORMAL

    def _load_data(self) -> None:
        self._bookmarks = load_bookmarks()
        visible = filter_bookmarks(self._bookmarks, self._filter) if self._filter else self._bookmarks
        visible = self._sort_bookmarks(visible)
        visible = self._bookmarks_in_table_order(visible)
        self._visible_bookmark_ids = [b.id for b in visible]
        visible_ids = {b.id for b in visible}
        if self._selected and self._selected.id not in visible_ids:
            self._selected = None
        if self._filter and not self._selected and visible:
            self._selected = visible[0]
            if self._is_normal():
                self._update_detail(self._selected)

        table = self.query_one("#table", DataTable)
        self._reset_table_columns(table)

        if self._mode == "category":
            self._render_grouped(table, visible)
        else:
            self._render_flat(table, visible)
        self._restore_selected_cursor(table)

    def _columns_for_mode(self) -> list[str]:
        return CATEGORY_COLUMNS if self._mode == "category" else ALL_COLUMNS

    def _reset_table_columns(self, table: DataTable) -> None:
        table.clear(columns=True)
        table.add_columns(*self._columns_for_mode())

    def _restore_selected_cursor(self, table: DataTable) -> None:
        if not self._selected:
            return
        with suppress(Exception):
            table.move_cursor(row=table.get_row_index(self._selected.id))

    def _sort_bookmarks(self, bookmarks: list[Bookmark]) -> list[Bookmark]:
        if self._sort_order == "cat_id":
            return sorted(bookmarks, key=lambda b: (b.category or "", b.id))
        return sorted(bookmarks, key=lambda b: b.id)

    def _bookmarks_in_table_order(self, bookmarks: list[Bookmark]) -> list[Bookmark]:
        if self._mode != "category":
            return bookmarks
        by_category: dict[str, list[Bookmark]] = {}
        for b in bookmarks:
            cat = b.category or "uncategorized"
            by_category.setdefault(cat, []).append(b)
        ordered = []
        for cat in sorted(by_category):
            ordered.extend(by_category[cat])
        return ordered

    def _update_shortcuts(self) -> None:
        if not self.is_mounted:
            return
        shortcuts = self.query_one("#shortcuts", Static)
        if self._app_mode == MODE_EDIT:
            shortcuts.update(self._format_shortcuts(EDIT_SHORTCUT_TEXT))
        elif self._app_mode in (MODE_CONFIRM_RESUME, MODE_CONFIRM_REMOVE):
            shortcuts.update(self._format_shortcuts(CONFIRM_SHORTCUT_TEXT))
        else:
            shortcuts.update(self._format_shortcuts(NORMAL_SHORTCUT_TEXT))

    def _format_shortcuts(self, value: str) -> Text:
        text = Text()
        for index, part in enumerate(value.split("   ")):
            if index:
                text.append("   ")
            key, _, label = part.partition(" ")
            text.append(key, style="bold cyan")
            if label:
                text.append(f" {label}", style="dim")
        return text

    def _empty_state(self) -> None:
        msg = self.EMPTY_MESSAGE if not self._bookmarks else "No matches."
        self.query_one("#detail-title", Static).update(msg)
        self.query_one("#detail-body", Static).update(self.HELP_TEXT)

    def _clear_selection(self) -> None:
        self._selected = None
        if self._is_normal():
            self.query_one("#detail-title", Static).update("Select a bookmark to view details.")
            self.query_one("#detail-body", Static).update("")

    def _editable_attrs(self) -> list[str]:
        return EDITABLE_ATTRS_CATEGORY if self._mode == "category" else EDITABLE_ATTRS_ALL

    def _attr_for_column(self, column: int) -> str | None:
        columns = self._columns_for_mode()
        if column < 0 or column >= len(columns):
            return None
        column_name = columns[column]
        for attr, mapped_column in ATTR_COLUMNS.items():
            if mapped_column == column_name and attr in self._editable_attrs():
                return attr
        return None

    def _column_for_attr(self, attr: str) -> int:
        return self._columns_for_mode().index(ATTR_COLUMNS[attr])

    def _value_for_attr(self, b: Bookmark, attr: str) -> str:
        return getattr(b, attr) or ""

    def _display_value_for_attr(self, b: Bookmark, attr: str, value: str) -> str | Text:
        if (
            self._app_mode == MODE_EDIT
            and self._selected
            and b.id == self._selected.id
            and attr == self._edit_attr
        ):
            return Text(f"> {self._edit_value}", style="reverse bold")
        if attr == "title":
            return value[:50] + ("..." if len(value) > 50 else "")
        return value or "-"

    def _add_bookmark_row(self, table: DataTable, b: Bookmark) -> None:
        title = self._display_value_for_attr(b, "title", b.title)
        profile = self._display_value_for_attr(
            b,
            "aweswitch_profile",
            b.aweswitch_profile or "",
        )
        if self._mode == "category":
            values = [b.id, b.provider, title, profile, b.session_id]
        else:
            category = self._display_value_for_attr(b, "category", b.category)
            values = [
                b.id,
                b.provider,
                title,
                category,
                profile,
                b.session_id,
            ]
        table.add_row(*values, key=b.id)

    def _render_flat(self, table: DataTable, visible: list[Bookmark]) -> None:
        if not visible:
            self._empty_state()
            return
        for b in visible:
            self._add_bookmark_row(table, b)

    def _render_grouped(self, table: DataTable, visible: list[Bookmark]) -> None:
        if not visible:
            self._empty_state()
            return

        categories: dict[str, list[Bookmark]] = {}
        for b in visible:
            cat = b.category or "uncategorized"
            categories.setdefault(cat, []).append(b)

        for i, cat in enumerate(sorted(categories)):
            color = CATEGORY_COLORS[i % len(CATEGORY_COLORS)]
            header = Text(f" {cat}", style=f"bold {color}")
            table.add_row(header, "", "", "", "", key=f"{CAT_KEY_PREFIX}{cat}")
            for b in categories[cat]:
                self._add_bookmark_row(table, b)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search":
            self._filter = event.value.lower()
            self._load_data()

    def _is_cat_row(self, key) -> bool:
        return key is not None and str(key).startswith(CAT_KEY_PREFIX)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if not self._is_normal():
            return
        if self._dragging or self._is_cat_row(event.row_key.value):
            self._clear_selection()
            return
        self._select_bookmark(event.row_key.value)
        if self._is_normal():
            self.action_resume()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if self._app_mode in (MODE_CONFIRM_RESUME, MODE_CONFIRM_REMOVE):
            if event.row_key is None or self._is_cat_row(event.row_key.value):
                return
            if not self._selected or event.row_key.value != self._selected.id:
                self._app_mode = MODE_NORMAL
                self._update_shortcuts()
                self._select_bookmark(event.row_key.value)
            return
        if not self._is_normal():
            return
        if self._dragging:
            return
        if event.row_key is None or self._is_cat_row(event.row_key.value):
            self._clear_selection()
            return
        self._select_bookmark(event.row_key.value)

    def _select_bookmark(self, bookmark_id: str) -> None:
        for b in self._bookmarks:
            if b.id == bookmark_id:
                self._selected = b
                if self._is_normal():
                    self._update_detail(b)
                break

    def _update_detail(self, b: Bookmark) -> None:
        self.query_one("#detail-title", Static).update(f" {b.id}")
        lines = [
            f"Title:     {b.title}",
            f"First prompt: {self._format_first_prompt(b.first_prompt)}",
            f"Provider:  {b.provider}",
            f"Session:   {b.session_id}",
            f"Category:  {b.category or '-'}",
            f"Project:   {b.project_path or '-'}",
            f"Profile:   {b.aweswitch_profile or '-'}",
            f"Saved at:  {b.bookmarked_at}",
        ]
        self.query_one("#detail-body", Static).update("\n".join(lines))

    def _format_first_prompt(self, value: str) -> str:
        if not value:
            return "-"
        if len(value) <= FIRST_PROMPT_EDGE_CHARS * 2:
            return value
        return f"{value[:FIRST_PROMPT_EDGE_CHARS]}...{value[-FIRST_PROMPT_EDGE_CHARS:]}"

    # --- mode-gated actions ---

    def action_resume(self) -> None:
        if not self._selected or not self._is_normal():
            return
        self._app_mode = MODE_CONFIRM_RESUME
        self._update_shortcuts()
        self._show_confirm_prompt()

    def action_edit(self) -> None:
        if not self._selected or not self._is_normal():
            return
        self._app_mode = MODE_EDIT
        self._begin_inline_edit()

    def action_remove(self) -> None:
        if not self._selected or not self._is_normal():
            return
        self._app_mode = MODE_CONFIRM_REMOVE
        self._update_shortcuts()
        self._show_confirm_prompt()

    # --- key dispatch for edit / confirm modes ---

    def on_key(self, event) -> None:
        key = event.key
        search = self.query_one("#search", Input)

        if search.has_focus:
            if key == "enter":
                self.query_one("#table", DataTable).focus()
                event.stop()
            elif key == "escape":
                self.action_clear_search()
                event.stop()
            return

        if self._app_mode == MODE_EDIT:
            if key == "escape":
                self._edit_discard()
                event.stop()
            elif key == "enter":
                self._edit_save()
                event.stop()
            elif key in ("tab", "right"):
                self._move_edit_field(1)
                event.stop()
            elif key in ("shift+tab", "left"):
                self._move_edit_field(-1)
                event.stop()
            elif key == "down":
                self._move_edit_row(1)
                event.stop()
            elif key == "up":
                self._move_edit_row(-1)
                event.stop()
            elif key == "backspace":
                self._edit_value = self._edit_value[:-1]
                self._refresh_edit_row()
                event.stop()
            elif key == "delete":
                self._edit_value = ""
                self._refresh_edit_row()
                event.stop()
            elif event.character:
                self._edit_value += event.character
                self._refresh_edit_row()
                event.stop()
            return

        if self._app_mode in (MODE_CONFIRM_RESUME, MODE_CONFIRM_REMOVE):
            if key == "down":
                self._cancel_confirm_and_move_selection(1)
                event.stop()
            elif key == "up":
                self._cancel_confirm_and_move_selection(-1)
                event.stop()
            if key in ("y", "enter"):
                self._confirm_execute()
                event.stop()
            elif key in ("n", "escape"):
                self._confirm_cancel()
                event.stop()
            return

        if key == "escape":
            self.action_clear_search()
            event.stop()

    # --- confirm helpers ---

    def _show_confirm_prompt(self) -> None:
        b = self._selected
        if not b:
            return
        title = self.query_one("#detail-title", Static)
        body = self.query_one("#detail-body", Static)
        if self._app_mode == MODE_CONFIRM_RESUME:
            title.update("Resume this session?")
            body.update(
                f"Session: {b.session_id}\n"
                f"Title:   {b.title}\n\n"
                "[Enter/y] Resume  [Esc/n] Cancel"
            )
        elif self._app_mode == MODE_CONFIRM_REMOVE:
            title.update("Remove this bookmark?")
            body.update(
                f"{b.id}: {b.title}\n\n"
                "[Enter/y] Remove  [Esc/n] Cancel"
            )

    def _confirm_execute(self) -> None:
        if not self._selected:
            self._app_mode = MODE_NORMAL
            self._update_shortcuts()
            return
        if self._app_mode == MODE_CONFIRM_RESUME:
            self._app_mode = MODE_NORMAL
            self._update_shortcuts()
            self.exit(result=self._selected)
            return
        if self._app_mode == MODE_CONFIRM_REMOVE:
            remove_bookmark(self._selected.id)
            self._selected = None
            self._app_mode = MODE_NORMAL
            self._update_shortcuts()
            self.query_one("#detail-title", Static).update("Removed")
            self.query_one("#detail-body", Static).update("")
            self._load_data()

    def _confirm_cancel(self) -> None:
        self._app_mode = MODE_NORMAL
        self._update_shortcuts()
        if self._selected:
            self._update_detail(self._selected)

    # --- edit helpers ---

    def _begin_inline_edit(self) -> None:
        if not self._selected:
            self._app_mode = MODE_NORMAL
            return
        table = self.query_one("#table", DataTable)
        self._edit_attr = self._attr_for_column(table.cursor_column) or self._editable_attrs()[0]
        self._edit_value = self._value_for_attr(self._selected, self._edit_attr)
        table.cursor_type = "none"
        with suppress(Exception):
            table.move_cursor(
                row=table.get_row_index(self._selected.id),
                column=self._column_for_attr(self._edit_attr),
            )
        self.query_one("#detail-title", Static).update(f"Editing: {self._selected.id}")
        self.query_one("#detail-body", Static).update(
            f"{ATTR_COLUMNS[self._edit_attr]}: Enter saves this cell. Esc exits editing."
        )
        self._update_shortcuts()
        self._refresh_edit_row()

    def _refresh_edit_row(self) -> None:
        if self._selected:
            self._load_data()
            if self._app_mode == MODE_EDIT:
                self._sync_edit_cursor()

    def _move_edit_field(self, delta: int) -> None:
        if not self._selected or not self._edit_attr:
            return
        attrs = self._editable_attrs()
        self._edit_attr = attrs[(attrs.index(self._edit_attr) + delta) % len(attrs)]
        self._edit_value = self._value_for_attr(self._selected, self._edit_attr)
        self._refresh_edit_row()

    def _move_edit_row(self, delta: int) -> None:
        if not self._selected or not self._edit_attr or not self._visible_bookmark_ids:
            return
        try:
            current_index = self._visible_bookmark_ids.index(self._selected.id)
        except ValueError:
            return
        next_index = current_index + delta
        if next_index < 0 or next_index >= len(self._visible_bookmark_ids):
            return
        next_id = self._visible_bookmark_ids[next_index]
        for b in self._bookmarks:
            if b.id == next_id:
                self._selected = b
                break
        self._edit_value = self._value_for_attr(self._selected, self._edit_attr)
        self._refresh_edit_row()

    def _cancel_confirm_and_move_selection(self, delta: int) -> None:
        self._app_mode = MODE_NORMAL
        self._update_shortcuts()
        if not self._selected or not self._visible_bookmark_ids:
            return
        try:
            current_index = self._visible_bookmark_ids.index(self._selected.id)
        except ValueError:
            return
        next_index = current_index + delta
        if next_index < 0 or next_index >= len(self._visible_bookmark_ids):
            if self._selected:
                self._update_detail(self._selected)
            return
        self._select_bookmark(self._visible_bookmark_ids[next_index])
        self._restore_selected_cursor(self.query_one("#table", DataTable))

    def _sync_edit_cursor(self) -> None:
        if not self._selected or not self._edit_attr:
            return
        table = self.query_one("#table", DataTable)
        with suppress(Exception):
            table.move_cursor(
                row=table.get_row_index(self._selected.id),
                column=self._column_for_attr(self._edit_attr),
            )
        table.cursor_type = "none"
        self.query_one("#detail-body", Static).update(
            f"{ATTR_COLUMNS[self._edit_attr]}: Enter saves this cell. Esc exits editing."
        )

    def _edit_save(self) -> None:
        if not self._selected:
            self._app_mode = MODE_NORMAL
            self._update_shortcuts()
            return
        selected_id = self._selected.id
        if self._edit_attr:
            update_bookmark(selected_id, **{self._edit_attr: self._edit_value.strip()})
            self._load_data()
            for b in self._bookmarks:
                if b.id == selected_id:
                    self._selected = b
                    break
            self._edit_value = self._value_for_attr(self._selected, self._edit_attr)
            self._refresh_edit_row()
        if self._selected:
            self._update_detail(self._selected)

    def _edit_discard(self) -> None:
        self._edit_attr = None
        self._edit_value = ""
        self._app_mode = MODE_NORMAL
        self.query_one("#table", DataTable).cursor_type = "row"
        self._update_shortcuts()
        if self._selected:
            self._update_detail(self._selected)
            self._load_data()

    # --- unconditional actions ---

    def action_toggle_mode(self) -> None:
        if not self._is_normal():
            return
        idx = MODE_ORDER.index(self._mode)
        self._mode = MODE_ORDER[(idx + 1) % len(MODE_ORDER)]
        self._load_data()

    def action_cycle_sort(self) -> None:
        if not self._is_normal():
            return
        idx = SORT_ORDER.index(self._sort_order)
        self._sort_order = SORT_ORDER[(idx + 1) % len(SORT_ORDER)]
        self._load_data()

    def action_resize_sidebar(self, delta: int) -> None:
        total = SIDEBAR_FRAC + DETAIL_FRAC
        sidebar = self.query_one("#sidebar")
        current = int(sidebar.styles.width.value) if sidebar.styles.width else SIDEBAR_FRAC
        new = max(MIN_FRAC, min(total - MIN_FRAC, current + delta))
        sidebar.styles.width = f"{new}fr"
        self.query_one("#detail").styles.width = f"{total - new}fr"

    def action_help(self) -> None:
        self.query_one("#detail-title", Static).update("Keyboard shortcuts")
        self.query_one("#detail-body", Static).update(self.HELP_TEXT)

    def action_focus_search(self) -> None:
        if not self._is_normal():
            return
        search = self.query_one("#search", Input)
        search.add_class("visible")
        search.focus()

    def action_clear_search(self) -> None:
        search = self.query_one("#search", Input)
        if search.has_class("visible"):
            search.remove_class("visible")
            self._filter = ""
            search.value = ""
            self._load_data()
            self.query_one("#table", DataTable).focus()
