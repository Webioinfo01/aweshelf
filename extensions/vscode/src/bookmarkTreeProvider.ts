import * as vscode from "vscode";

import { AweshelfService, formatCommandError } from "./aweshelfService";
import { AweshelfBookmark, BookmarkGroup, BookmarkSortBy, BookmarkViewOptions, groupBookmarks } from "./bookmark";
import { ListOptions } from "./aweshelfService";

type TreeNode = CategoryNode | BookmarkNode;

export class CategoryNode {
  readonly contextValue = "aweshelfCategory";

  constructor(readonly group: BookmarkGroup) {}
}

export class BookmarkNode {
  readonly contextValue = "aweshelfBookmark";

  constructor(readonly bookmark: AweshelfBookmark) {}
}

export class BookmarkTreeProvider implements vscode.TreeDataProvider<TreeNode> {
  private service: AweshelfService;
  private query = "";
  private options: BookmarkViewOptions = { sortBy: "id" };
  private readonly onDidChangeTreeDataEmitter = new vscode.EventEmitter<TreeNode | undefined>();

  readonly onDidChangeTreeData = this.onDidChangeTreeDataEmitter.event;

  constructor(service: AweshelfService) {
    this.service = service;
  }

  setService(service: AweshelfService): void {
    this.service = service;
  }

  setQuery(query: string): void {
    this.query = query.trim();
    this.refresh();
  }

  getQuery(): string {
    return this.query;
  }

  setSortBy(sortBy: BookmarkSortBy): void {
    this.options = { ...this.options, sortBy };
    this.refresh();
  }

  setProviderFilter(provider?: string): void {
    this.options = { ...this.options, provider };
    this.refresh();
  }

  setCategoryFilter(category?: string): void {
    this.options = { ...this.options, category };
    this.refresh();
  }

  clearFilters(): void {
    this.query = "";
    this.options = { sortBy: this.options.sortBy ?? "id" };
    this.refresh();
  }

  getOptions(): BookmarkViewOptions {
    return { ...this.options };
  }

  refresh(): void {
    this.onDidChangeTreeDataEmitter.fire(undefined);
  }

  async getChildren(element?: TreeNode): Promise<TreeNode[]> {
    if (element instanceof CategoryNode) {
      return element.group.bookmarks.map((bookmark) => new BookmarkNode(bookmark));
    }

    try {
      const listOptions: ListOptions = {
        sortBy: this.options.sortBy,
        provider: this.options.provider,
        category: this.options.category
      };
      const bookmarks = await this.service.listBookmarks(this.query, listOptions);
      return groupBookmarks(bookmarks).map((group) => new CategoryNode(group));
    } catch (error) {
      void vscode.window.showErrorMessage(formatCommandError(error));
      return [];
    }
  }

  getTreeItem(element: TreeNode): vscode.TreeItem {
    if (element instanceof CategoryNode) {
      const item = new vscode.TreeItem(
        `${element.group.category} (${element.group.bookmarks.length})`,
        vscode.TreeItemCollapsibleState.Expanded
      );
      item.contextValue = element.contextValue;
      item.iconPath = new vscode.ThemeIcon("folder");
      return item;
    }

    const bookmark = element.bookmark;
    const item = new vscode.TreeItem(
      bookmark.title || bookmark.id,
      vscode.TreeItemCollapsibleState.None
    );
    item.id = bookmark.id;
    item.description = describeBookmark(bookmark);
    item.tooltip = buildTooltip(bookmark);
    item.contextValue = element.contextValue;
    item.iconPath = new vscode.ThemeIcon("bookmark");
    item.command = {
      command: "aweshelf.resumeBookmark",
      title: "Resume Bookmark",
      arguments: [element]
    };
    return item;
  }
}

export function getBookmarkFromTreeNode(element: unknown): AweshelfBookmark | undefined {
  return element instanceof BookmarkNode ? element.bookmark : undefined;
}

function describeBookmark(bookmark: AweshelfBookmark): string {
  const profile = bookmark.aweswitch_profile ? ` · ${bookmark.aweswitch_profile}` : "";
  return `${bookmark.provider}${profile}`;
}

function buildTooltip(bookmark: AweshelfBookmark): string {
  const lines = [
    bookmark.title || bookmark.id,
    `ID: ${bookmark.id}`,
    `Provider: ${bookmark.provider}`,
    `Session: ${bookmark.session_id}`,
    `Category: ${bookmark.category || "Uncategorized"}`,
    `Project: ${bookmark.project_path || "-"}`,
    `Profile: ${bookmark.aweswitch_profile || "-"}`
  ];
  if (bookmark.first_prompt) {
    lines.push("", bookmark.first_prompt);
  }
  return lines.join("\n");
}
