"""TUI browse app using textual."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Input, Static

from aweshelf.lib.store import load_bookmarks, remove_bookmark, update_bookmark
from aweshelf.types import Bookmark

SIDEBAR_FRAC = 60
DETAIL_FRAC = 40
MIN_FRAC = 10
CATEGORY_COLORS = ["green", "orange", "red", "cyan", "magenta"]
MODE_ORDER = ["all", "category"]
SORT_ORDER = ["cat_id", "id"]

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


class EditScreen(Screen):
    """Inline edit screen for bookmark fields."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    CSS = """
    #edit-title {
        text-style: bold;
        color: $accent;
        margin: 1 0;
    }
    #edit-fields {
        height: auto;
        margin: 1 0;
    }
    .edit-label {
        color: $text-muted;
        margin-top: 1;
    }
    #edit-actions {
        height: auto;
        margin-top: 1;
    }
    .btn {
        min-width: 10;
        margin-right: 1;
    }
    """

    def __init__(self, bookmark: Bookmark):
        super().__init__()
        self._bookmark = bookmark
        self._changes: dict[str, str] = {}

    def compose(self) -> ComposeResult:
        yield Static(f"Editing: {self._bookmark.title}", id="edit-title")
        with Vertical(id="edit-fields"):
            for attr, label in EDIT_FIELDS:
                current = getattr(self._bookmark, attr) or ""
                yield Static(f"{label}:", classes="edit-label")
                yield Input(value=current, id=f"edit-{attr}", placeholder=f"Current: {current or '(empty)'}")
        with Horizontal(id="edit-actions"):
            yield Button("Save", variant="success", id="save-btn", classes="btn")
            yield Button("Cancel", id="cancel-btn", classes="btn")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            self._collect_and_save()
        elif event.button.id == "cancel-btn":
            self.dismiss()

    def action_cancel(self) -> None:
        self.dismiss()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._collect_and_save()

    def _collect_and_save(self) -> None:
        for attr, _ in EDIT_FIELDS:
            inp = self.query_one(f"#edit-{attr}", Input)
            new_val = inp.value.strip()
            old_val = getattr(self._bookmark, attr) or ""
            if new_val and new_val != old_val:
                self._changes[attr] = new_val
        if not self._changes:
            self.dismiss()
            return
        self.dismiss(self._changes)


class ConfirmScreen(Screen):
    """Confirmation prompt for destructive actions."""

    BINDINGS = [
        Binding("escape", "cancel", "No"),
    ]

    CSS = """
    #confirm-msg {
        margin: 1 0;
        text-style: bold;
    }
    #confirm-actions {
        height: auto;
        margin-top: 1;
    }
    .btn {
        min-width: 10;
        margin-right: 1;
    }
    """

    def __init__(self, message: str):
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        yield Static(self._message, id="confirm-msg")
        with Horizontal(id="confirm-actions"):
            yield Button("Yes", variant="error", id="yes-btn", classes="btn")
            yield Button("No", id="no-btn", classes="btn")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes-btn":
            self.dismiss(True)
        elif event.button.id == "no-btn":
            self.dismiss(False)

    def action_cancel(self) -> None:
        self.dismiss(False)


class BookmarkBrowser(App):
    """Browse and select bookmarks."""

    EMPTY_MESSAGE = "No bookmarks found. Run aweshelf bookmark first."
    HELP_TEXT = "\n".join([
        "/      Filter bookmarks",
        "Esc    Clear filter / return to table",
        "Enter  Resume selected bookmark",
        "e      Edit bookmark",
        "r      Remove bookmark",
        "m      Toggle All / Category mode",
        "s      Cycle sort order",
        "?      Show this help",
        "q      Quit",
        "[ / ]  Shrink / grow sidebar",
    ])

    BINDINGS = [
        Binding("enter", "resume", "Resume", show=False),
        Binding("q", "quit", "Quit"),
        Binding("e", "edit", "Edit"),
        Binding("r", "remove", "Remove"),
        Binding("m", "toggle_mode", "Mode"),
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
    #grouped {
        height: 1fr;
    }
    .cat-header {
        padding: 0 1;
        text-style: bold;
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
    """

    def __init__(self):
        super().__init__()
        self._bookmarks: list[Bookmark] = []
        self._selected: Bookmark | None = None
        self._filter: str = ""
        self._mode: str = MODE_ORDER[0]
        self._sort_order: str = SORT_ORDER[0]
        self._dragging: bool = False
        self._drag_start_x: int = 0
        self._drag_start_sidebar: int = SIDEBAR_FRAC
        self._drag_start_detail: int = DETAIL_FRAC

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Input(placeholder="Filter bookmarks...", id="search")
                with Vertical(id="grouped"):
                    pass
                yield DataTable(id="table")
            yield DragHandle()
            with Vertical(id="detail"):
                yield Static("Select a bookmark to view details.", id="detail-title")
                yield Static("", id="detail-body")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#table", DataTable)
        table.add_columns("ID", "PROVIDER", "TITLE", "CATEGORY", "PROFILE")
        table.cursor_type = "row"
        self._load_data()

    def _matches_filter(self, b: Bookmark) -> bool:
        if not self._filter:
            return True
        f = self._filter
        return (
            f in b.title.lower()
            or f in b.category.lower()
            or f in b.session_id.lower()
            or f in b.project_path.lower()
            or (b.aweswitch_profile and f in b.aweswitch_profile.lower())
        )

    def _load_data(self) -> None:
        self._bookmarks = load_bookmarks()
        visible = [b for b in self._bookmarks if self._matches_filter(b)]
        visible = self._sort_bookmarks(visible)

        grouped = self.query_one("#grouped")
        flat = self.query_one("#table")

        if self._mode == "category":
            flat.display = False
            grouped.display = True
            self._render_grouped(visible)
        else:
            grouped.display = False
            flat.display = True
            self._render_flat(visible)

    def _sort_bookmarks(self, bookmarks: list[Bookmark]) -> list[Bookmark]:
        if self._sort_order == "cat_id":
            return sorted(bookmarks, key=lambda b: (b.category or "", b.id))
        return sorted(bookmarks, key=lambda b: b.id)

    def _empty_state(self) -> None:
        msg = self.EMPTY_MESSAGE if not self._bookmarks else "No matches."
        self.query_one("#detail-title", Static).update(msg)
        self.query_one("#detail-body", Static).update(self.HELP_TEXT)

    def _render_flat(self, visible: list[Bookmark]) -> None:
        table = self.query_one("#table", DataTable)
        table.clear()
        if not visible:
            self._empty_state()
            return
        for b in visible:
            table.add_row(
                b.id,
                b.provider,
                b.title[:50] + ("..." if len(b.title) > 50 else ""),
                b.category or "-",
                b.aweswitch_profile or "-",
                key=b.id,
            )

    def _render_grouped(self, visible: list[Bookmark]) -> None:
        grouped = self.query_one("#grouped")
        grouped.remove_children()
        if not visible:
            self._empty_state()
            return

        categories: dict[str, list[Bookmark]] = {}
        for b in visible:
            cat = b.category or "uncategorized"
            categories.setdefault(cat, []).append(b)

        for i, cat in enumerate(sorted(categories)):
            color = CATEGORY_COLORS[i % len(CATEGORY_COLORS)]
            header = Static(f" {cat}", classes="cat-header")
            header.styles.color = color
            grouped.mount(header)
            dt = DataTable()
            dt.add_columns("ID", "PROVIDER", "TITLE", "PROFILE")
            dt.cursor_type = "row"
            for b in categories[cat]:
                dt.add_row(
                    b.id,
                    b.provider,
                    b.title[:50] + ("..." if len(b.title) > 50 else ""),
                    b.aweswitch_profile or "-",
                    key=b.id,
                )
            grouped.mount(dt)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search":
            self._filter = event.value.lower()
            self._load_data()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if self._dragging:
            return
        self._select_bookmark(event.row_key.value)
        self.action_resume()

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if self._dragging or event.row_key is None:
            return
        self._select_bookmark(event.row_key.value)

    def _select_bookmark(self, bookmark_id: str) -> None:
        for b in self._bookmarks:
            if b.id == bookmark_id:
                self._selected = b
                self._update_detail(b)
                break

    def _update_detail(self, b: Bookmark) -> None:
        self.query_one("#detail-title", Static).update(f" {b.title}")
        lines = [
            f"ID:        {b.id}",
            f"Provider:  {b.provider}",
            f"Session:   {b.session_id}",
            f"Category:  {b.category or '-'}",
            f"Project:   {b.project_path or '-'}",
            f"Profile:   {b.aweswitch_profile or '-'}",
            f"Saved at:  {b.bookmarked_at}",
        ]
        self.query_one("#detail-body", Static).update("\n".join(lines))

    def action_resume(self) -> None:
        if self._selected:
            self.exit(result=self._selected)

    def action_toggle_mode(self) -> None:
        idx = MODE_ORDER.index(self._mode)
        self._mode = MODE_ORDER[(idx + 1) % len(MODE_ORDER)]
        self._load_data()

    def action_cycle_sort(self) -> None:
        idx = SORT_ORDER.index(self._sort_order)
        self._sort_order = SORT_ORDER[(idx + 1) % len(SORT_ORDER)]
        self._load_data()

    def action_edit(self) -> None:
        if not self._selected:
            return

        def on_edit_result(result) -> None:
            if result:
                update_bookmark(self._selected.id, **result)
                self._load_data()
                # Re-select the updated bookmark
                for b in self._bookmarks:
                    if b.id == self._selected.id:
                        self._selected = b
                        self._update_detail(b)
                        break

        self.push_screen(EditScreen(self._selected), on_edit_result)

    def action_remove(self) -> None:
        if not self._selected:
            return
        b = self._selected

        def on_confirm(result) -> None:
            if result:
                remove_bookmark(b.id)
                self._selected = None
                self.query_one("#detail-title", Static).update(f"Removed {b.id}")
                self.query_one("#detail-body", Static).update("")
                self._load_data()

        msg = f"Remove bookmark {b.id} ({b.title})?"
        self.push_screen(ConfirmScreen(msg), on_confirm)

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
