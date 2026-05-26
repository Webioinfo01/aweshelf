"""TUI browse app using textual."""

from textual.app import App, ComposeResult
from textual.widgets import DataTable, Static, Footer, Header
from textual.containers import Horizontal, Vertical
from textual.binding import Binding

from aweshelf.lib.store import load_bookmarks
from aweshelf.types import Bookmark


class BookmarkBrowser(App):
    """Browse and select bookmarks."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "resume", "Resume"),
    ]

    CSS = """
    Screen {
        layout: horizontal;
    }
    #sidebar {
        width: 60%;
        border-right: solid $primary;
    }
    #detail {
        width: 40%;
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

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield DataTable(id="table")
            with Vertical(id="detail"):
                yield Static("Select a bookmark to view details.", id="detail-title")
                yield Static("", id="detail-body")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#table", DataTable)
        table.add_columns("ID", "PROVIDER", "TITLE", "CATEGORY", "PROFILE")
        table.cursor_type = "row"
        self._load_data()

    def _load_data(self) -> None:
        table = self.query_one("#table", DataTable)
        table.clear()
        self._bookmarks = load_bookmarks()
        for b in self._bookmarks:
            table.add_row(
                b.id,
                b.provider,
                b.title[:50] + ("..." if len(b.title) > 50 else ""),
                b.category or "-",
                b.aweswitch_profile or "-",
                key=b.id,
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        bookmark_id = event.row_key.value
        for b in self._bookmarks:
            if b.id == bookmark_id:
                self._selected = b
                self._update_detail(b)
                self.exit(result=b)
                return

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key is None:
            return
        bookmark_id = event.row_key.value
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
