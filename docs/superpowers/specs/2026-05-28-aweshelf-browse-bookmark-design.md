# aweshelf Browse and Bookmark Interaction Design

Date: 2026-05-28

## Goal

Improve three related workflows without changing aweshelf's storage format or command surface:

1. Make `aweshelf browse` edit mode feel like direct table editing, with one clear editing cursor.
2. Let interactive `aweshelf bookmark` collect title and aweswitch profile, and reject profiles that do not exist in aweswitch.
3. Expose search in `aweshelf browse` so it matches the fields searched by `aweshelf search`.

## Current State

`browse` already has a Textual `DataTable`, an internal selected bookmark, inline cell rendering, category/all modes, and a hidden filter input opened with `/`. The current edit mode still feels like row selection and cell editing are both visible at once. It also moves only between fields in the selected row.

`bookmark` interactive mode currently prompts for category only. Title can be passed by `-t/--title`, and profile can be passed by `--profile`, but interactive users cannot set those fields as part of the prompt flow. Profile detection exists, and `profile_exists()` can validate a profile name against aweswitch config.

## Design

### Browse Normal Mode

Normal mode keeps the current table-first workflow:

- `up/down` changes the selected bookmark row.
- `enter` opens resume confirmation for the selected bookmark.
- `e` enters edit mode.
- `r` opens remove confirmation.
- `c` toggles Category/All mode.
- `s` cycles sort order.
- `/` opens search.
- `esc` clears search when search is visible.

The bottom shortcut bar should mention search:

```text
enter Resume selected session   q Quit   e Edit   r Remove   c Category   s Sort   / Search   esc Cancel
```

### Browse Edit Mode

Edit mode uses a single table cell as the visible editing cursor.

When the user presses `e`:

- The app switches to edit mode.
- The table cursor type becomes `cell`.
- The selected row remains the internal target row, but row selection is not used as a second visible editing affordance.
- If the current cursor column maps to an editable field, editing starts there.
- If the current cursor column is not editable, editing starts on `TITLE`.

Editable fields:

- Category mode: `TITLE`, `PROFILE`
- All mode: `TITLE`, `CATEGORY`, `PROFILE`

Keyboard behavior in edit mode:

- Printable characters update the active cell buffer.
- `backspace` removes the previous character from the active cell buffer.
- `delete` clears the active cell buffer.
- `enter` saves the active cell and stays in edit mode.
- `esc` exits edit mode and returns to normal row navigation.
- `left/right` move between editable cells in the current row.
- `tab/shift+tab` move between editable cells in the current row.
- `up/down` move to the previous or next bookmark row while preserving the current editable field.
- Category header rows are skipped while moving up/down.
- Moving to another cell loads that cell's current stored value into the edit buffer.

The edit shortcut bar should be:

```text
enter Save cell   up/down Row   left/right Field   tab Next field   esc Done
```

The active cell should render as reversed/bold text with the edit buffer. No right-side edit form is introduced.

### Browse Search

`browse` search remains a lightweight filter input instead of becoming a separate screen.

Behavior:

- `/` shows and focuses the top search input.
- Typing filters rows live.
- `enter` returns focus to the table while keeping the filter.
- `esc` clears the filter, hides the input, and returns focus to the table.
- Search is disabled while in edit or confirmation modes.

Match fields align with `aweshelf search` and include:

- title
- category
- session ID
- project path
- aweswitch profile
- first prompt

### Bookmark Interactive Flow

Interactive `aweshelf bookmark` prompts in this order:

1. Pick a session when no `SESSION_ID` is provided.
2. Prompt for `Title`, using the detected title or first prompt as the default.
3. Prompt for `Category`, preserving the existing category list display.
4. Prompt for `Profile`, using the detected aweswitch profile as the default when available.

Profile rules:

- Empty profile is allowed and stores `None`/empty profile as today.
- A non-empty profile must exist in aweswitch config under any provider.
- Interactive mode retries until the user enters an existing profile or an empty value.
- Non-interactive `--profile PROFILE` fails with a Click error when the profile does not exist.

This validation should use the existing aweswitch config parsing boundary instead of duplicating config file knowledge inside the command.

## Data Flow

Browse edit saves through `update_bookmark()` exactly as it does today. After saving, the app reloads bookmarks, restores the selected bookmark by ID, and keeps the active editable field.

Bookmark profile validation calls `profile_exists(profile)` before constructing the `Bookmark`. Auto-detected profiles are still accepted only if they exist in the loaded aweswitch config.

No schema migration is required.

## Error Handling

- If no bookmark row is selected, edit/remove/resume do nothing.
- If edit movement cannot find another bookmark row, it stays on the current cell.
- If the active bookmark disappears after a save/filter reload, edit mode exits cleanly.
- Invalid CLI `--profile` raises `ClickException("aweswitch profile not found: <name>")`.
- Invalid interactive profile prints the same problem and asks again.

## Tests

Add focused tests for:

- `e` enters edit mode with `cell` cursor type and the expected active field.
- Edit mode `up/down` moves between bookmark rows and preserves the active field.
- Edit mode `left/right` or `tab/shift+tab` moves across editable cells.
- `enter` saves only the active cell and stays in edit mode.
- `esc` exits edit mode and restores normal row navigation.
- Browse search matches title, category, session ID, project path, profile, and first prompt.
- `/`, `enter`, and `esc` search focus behavior.
- Interactive bookmark prompts for title, category, and profile.
- Interactive invalid profile retries.
- `--profile` rejects an unknown aweswitch profile.

## Out Of Scope

- Changing the bookmark JSON format.
- Adding a separate browse search command.
- Replacing Textual `DataTable` with a custom table renderer.
- Adding profile completion or provider-specific profile filtering.
