"""TUI browse app using textual."""

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Footer, Header, Input, Static

from aweshelf.lib.store import load_bookmarks, remove_bookmark, update_bookmark
from aweshelf.types import Bookmark

SIDEBAR_FRAC = 60
DETAIL_FRAC = 40
MIN_FRAC = 10
CATEGORY_COLORS = ["green", "orange", "red", "cyan", "magenta"]
MODE_ORDER = ["category", "all"]
SORT_ORDER = ["cat_id", "id"]
CAT_KEY_PREFIX = "__cat__"
ALL_COLUMNS = ["ID", "PROVIDER", "TITLE", "CATEGORY", "PROFILE", "SESSION"]
CATEGORY_COLUMNS = ["ID", "PROVIDER", "TITLE", "PROFILE", "SESSION"]

MODE_NORMAL = "normal"
MODE_EDIT = "edit"
MODE_CONFIRM_RESUME = "confirm_resume"
MODE_CONFIRM_REMOVE = "confirm_remove"

EDIT_FIELDS = [
    ("title", "Title"),
    ("category", "Category"),
    ("aweswitch_profile", "Profile"),
]


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
        "Enter  Resume bookmark",
        "e      Edit bookmark",
        "r      Remove bookmark",
        "y      Confirm action",
        "n      Cancel action",
        "m      Toggle Category / All",
        "s      Cycle sort order",
        "?      Show this help",
        "q      Quit",
        "[ / ]  Shrink / grow sidebar",
    ])

    BINDINGS = [
        Binding("enter", "resume", "Resume", show=False, priority=True),
        Binding("q", "quit", "Quit"),
        Binding("e", "edit", "Edit"),
        Binding("r", "remove", "Remove"),
        Binding("m", "toggle_mode", "Category"),
        Binding("s", "cycle_sort", "Sort"),
        Binding("question_mark", "help", "Help", show=False),
        Binding("slash", "focus_search", "Filter", show=False),
        Binding("escape", "clear_search", "Clear", show=False),
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
    .edit-field {
        margin: 0 0 1 0;
    }
    .edit-label {
        color: $text-muted;
    }
    .edit-input {
        margin: 0 0 0 2;
    }
    .edit-hint {
        color: $text-muted;
        margin-top: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self._bookmarks: list[Bookmark] = []
        self._selected: Bookmark | None = None
        self._filter: str = ""
        self._mode: str = MODE_ORDER[0]
        self._sort_order: str = SORT_ORDER[0]
        self._app_mode: str = MODE_NORMAL
        self._edit_changes: dict[str, str] = {}
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
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#table", DataTable)
        table.cursor_type = "row"
        self._load_data()
        table.focus()

    def _is_normal(self) -> bool:
        return self._app_mode == MODE_NORMAL

    def _matches_filter(self, b: Bookmark) -> bool:
        if not self._filter:
            return True
        f = self._filter
        return (
            f in b.title.lower()
            or f in b.category.lower()
            or f in b.session_id.lower()
            or f in b.project_path.lower()
            or f in b.first_prompt.lower()
            or (b.aweswitch_profile and f in b.aweswitch_profile.lower())
        )

    def _load_data(self) -> None:
        self._bookmarks = load_bookmarks()
        visible = [b for b in self._bookmarks if self._matches_filter(b)]
        visible = self._sort_bookmarks(visible)

        table = self.query_one("#table", DataTable)
        self._reset_table_columns(table)

        if self._mode == "category":
            self._render_grouped(table, visible)
        else:
            self._render_flat(table, visible)

    def _columns_for_mode(self) -> list[str]:
        return CATEGORY_COLUMNS if self._mode == "category" else ALL_COLUMNS

    def _reset_table_columns(self, table: DataTable) -> None:
        table.clear(columns=True)
        table.add_columns(*self._columns_for_mode())

    def _sort_bookmarks(self, bookmarks: list[Bookmark]) -> list[Bookmark]:
        if self._sort_order == "cat_id":
            return sorted(bookmarks, key=lambda b: (b.category or "", b.id))
        return sorted(bookmarks, key=lambda b: b.id)

    def _empty_state(self) -> None:
        msg = self.EMPTY_MESSAGE if not self._bookmarks else "No matches."
        self.query_one("#detail-title", Static).update(msg)
        self.query_one("#detail-body", Static).update(self.HELP_TEXT)

    def _add_bookmark_row(self, table: DataTable, b: Bookmark) -> None:
        title = b.title[:50] + ("..." if len(b.title) > 50 else "")
        if self._mode == "category":
            values = [b.id, b.provider, title, b.aweswitch_profile or "-", b.session_id]
        else:
            values = [
                b.id,
                b.provider,
                title,
                b.category or "-",
                b.aweswitch_profile or "-",
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
        if self._dragging or self._is_cat_row(event.row_key.value):
            return
        self._select_bookmark(event.row_key.value)
        if self._is_normal():
            self.action_resume()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if self._dragging or event.row_key is None or self._is_cat_row(event.row_key.value):
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
            f"Prompt:    {b.first_prompt or '-'}",
            f"Provider:  {b.provider}",
            f"Session:   {b.session_id}",
            f"Category:  {b.category or '-'}",
            f"Project:   {b.project_path or '-'}",
            f"Profile:   {b.aweswitch_profile or '-'}",
            f"Saved at:  {b.bookmarked_at}",
        ]
        self.query_one("#detail-body", Static).update("\n".join(lines))

    # --- mode-gated actions ---

    def action_resume(self) -> None:
        if not self._selected or not self._is_normal():
            return
        self._app_mode = MODE_CONFIRM_RESUME
        self._show_confirm_prompt()

    def action_edit(self) -> None:
        if not self._selected or not self._is_normal():
            return
        self._app_mode = MODE_EDIT
        self._edit_changes = {}
        self._show_edit_form()

    def action_remove(self) -> None:
        if not self._selected or not self._is_normal():
            return
        self._app_mode = MODE_CONFIRM_REMOVE
        self._show_confirm_prompt()

    # --- key dispatch for edit / confirm modes ---

    def on_key(self, event) -> None:
        key = event.key

        if self._app_mode == MODE_EDIT:
            if key == "escape":
                self._edit_discard()
                event.stop()
            elif key == "enter":
                self._edit_save()
                event.stop()
            return

        if self._app_mode in (MODE_CONFIRM_RESUME, MODE_CONFIRM_REMOVE):
            if key == "y":
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
                "[y] Resume  [n] Cancel"
            )
        elif self._app_mode == MODE_CONFIRM_REMOVE:
            title.update("Remove this bookmark?")
            body.update(
                f"{b.id}: {b.title}\n\n"
                "[y] Remove  [n] Cancel"
            )

    def _confirm_execute(self) -> None:
        if not self._selected:
            self._app_mode = MODE_NORMAL
            return
        if self._app_mode == MODE_CONFIRM_RESUME:
            self._app_mode = MODE_NORMAL
            self.exit(result=self._selected)
            return
        if self._app_mode == MODE_CONFIRM_REMOVE:
            remove_bookmark(self._selected.id)
            self._selected = None
            self._app_mode = MODE_NORMAL
            self.query_one("#detail-title", Static).update("Removed")
            self.query_one("#detail-body", Static).update("")
            self._load_data()

    def _confirm_cancel(self) -> None:
        self._app_mode = MODE_NORMAL
        if self._selected:
            self._update_detail(self._selected)

    # --- edit helpers ---

    def _show_edit_form(self) -> None:
        b = self._selected
        if not b:
            return
        title = self.query_one("#detail-title", Static)
        body = self.query_one("#detail-body", Static)
        title.update(f"Editing: {b.title}")
        lines = []
        for attr, label in EDIT_FIELDS:
            current = getattr(b, attr) or ""
            lines.append(f"{label}: {current}")
        lines.append("")
        lines.append("Enter: save | Esc: discard")
        body.update("\n".join(lines))
        first_input = self._mount_edit_inputs(b)
        if first_input:
            first_input.focus()

    def _mount_edit_inputs(self, b: Bookmark) -> Input | None:
        detail = self.query_one("#detail")
        for widget in list(detail.query(".edit-field")):
            widget.remove()
        for widget in list(detail.query(".edit-hint")):
            widget.remove()
        first_input = None
        for attr, label in EDIT_FIELDS:
            current = getattr(b, attr) or ""
            row = Horizontal(classes="edit-field")
            row.mount(Static(f"{label}:", classes="edit-label"))
            inp = Input(
                value=current,
                placeholder=f"Current: {current or '(empty)'}",
                id=f"edit-{attr}",
                classes="edit-input",
            )
            row.mount(inp)
            detail.mount(row)
            if first_input is None:
                first_input = inp
        return first_input

    def _edit_save(self) -> None:
        if not self._selected:
            self._app_mode = MODE_NORMAL
            return
        for attr, _ in EDIT_FIELDS:
            try:
                inp = self.query_one(f"#edit-{attr}", Input)
                new_val = inp.value.strip()
                old_val = getattr(self._selected, attr) or ""
                if new_val and new_val != old_val:
                    self._edit_changes[attr] = new_val
            except Exception:
                pass
        if self._edit_changes:
            update_bookmark(self._selected.id, **self._edit_changes)
            self._load_data()
            for b in self._bookmarks:
                if b.id == self._selected.id:
                    self._selected = b
                    break
        self._app_mode = MODE_NORMAL
        if self._selected:
            self._update_detail(self._selected)

    def _edit_discard(self) -> None:
        self._edit_changes = {}
        self._app_mode = MODE_NORMAL
        if self._selected:
            self._update_detail(self._selected)

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
