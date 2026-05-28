export interface AweshelfBookmark {
  id: string;
  provider: string;
  session_id: string;
  title: string;
  category: string;
  project_path: string;
  first_prompt?: string;
  aweswitch_profile?: string | null;
  bookmarked_at: string;
}

export interface BookmarkGroup {
  category: string;
  bookmarks: AweshelfBookmark[];
}

export type BookmarkSortBy = "recent" | "id";

export interface BookmarkViewOptions {
  sortBy?: BookmarkSortBy;
  provider?: string;
  category?: string;
}

export const UNCATEGORIZED_CATEGORY = "Uncategorized";

export function normalizeCategory(category: string | undefined | null): string {
  const trimmed = category?.trim();
  return trimmed ? trimmed : UNCATEGORIZED_CATEGORY;
}

export function groupBookmarks(bookmarks: AweshelfBookmark[]): BookmarkGroup[] {
  const grouped = new Map<string, AweshelfBookmark[]>();

  for (const bookmark of bookmarks) {
    const category = normalizeCategory(bookmark.category);
    const current = grouped.get(category) ?? [];
    current.push(bookmark);
    grouped.set(category, current);
  }

  return [...grouped.entries()]
    .sort(([left], [right]) => compareCategories(left, right))
    .map(([category, categoryBookmarks]) => ({
      category,
      bookmarks: categoryBookmarks
    }));
}

function compareCategories(left: string, right: string): number {
  if (left === UNCATEGORIZED_CATEGORY && right !== UNCATEGORIZED_CATEGORY) {
    return 1;
  }
  if (right === UNCATEGORIZED_CATEGORY && left !== UNCATEGORIZED_CATEGORY) {
    return -1;
  }
  return left.localeCompare(right);
}
