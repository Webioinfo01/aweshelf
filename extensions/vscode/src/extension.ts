import * as vscode from "vscode";
import { readFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";

import {
  AweshelfService,
  AweshelfSession,
  BookmarkEdits,
  buildResumeArgs,
  buildShellCommand,
  createAweshelfEnv,
  formatCommandError,
  isCommandNotFoundError,
  resolveBookmarkConfigPath,
  resolveCommandPath
} from "./aweshelfService";
import { AweshelfBookmark, BookmarkSortBy, normalizeCategory } from "./bookmark";
import { formatBookmarkDetailMarkdown } from "./bookmarkDetail";
import {
  BookmarkNode,
  BookmarkTreeProvider,
  getBookmarkFromTreeNode
} from "./bookmarkTreeProvider";

export function activate(context: vscode.ExtensionContext): void {
  const provider = new BookmarkTreeProvider(createService(context));
  const treeView = vscode.window.createTreeView("aweshelfBookmarks", {
    treeDataProvider: provider,
    showCollapseAll: true
  });
  let bookmarkWatcher = registerBookmarkWatcher(context, provider);
  void promptForCommandPathIfMissing(context);

  context.subscriptions.push(
    treeView,
    vscode.commands.registerCommand("aweshelf.refresh", () => provider.refresh()),
    vscode.commands.registerCommand("aweshelf.searchBookmarks", async () => {
      const query = await vscode.window.showInputBox({
        prompt: "Search aweshelf bookmarks",
        value: provider.getQuery()
      });
      if (query !== undefined) {
        provider.setQuery(query);
      }
    }),
    vscode.commands.registerCommand("aweshelf.clearSearch", () => provider.setQuery("")),
    vscode.commands.registerCommand("aweshelf.sortBookmarks", async () => {
      const selected = await vscode.window.showQuickPick(
        [
          { label: "Title", value: "title" as BookmarkSortBy },
          { label: "Recent", value: "recent" as BookmarkSortBy },
          { label: "ID", value: "id" as BookmarkSortBy }
        ],
        { placeHolder: "Sort aweshelf bookmarks" }
      );
      if (selected) {
        provider.setSortBy(selected.value);
      }
    }),
    vscode.commands.registerCommand("aweshelf.filterProvider", async () => {
      const service = createService(context);
      try {
        const bookmarks = await service.listBookmarks(provider.getQuery());
        const providers = [...new Set(bookmarks.map((bookmark) => bookmark.provider))].sort();
        const selected = await vscode.window.showQuickPick(
          [
            { label: "All providers", value: undefined },
            ...providers.map((item) => ({ label: item, value: item }))
          ],
          { placeHolder: "Filter by provider" }
        );
        if (selected) {
          provider.setProviderFilter(selected.value);
        }
      } catch (error) {
        void vscode.window.showErrorMessage(formatCommandError(error));
      }
    }),
    vscode.commands.registerCommand("aweshelf.filterCategory", async () => {
      const service = createService(context);
      try {
        const bookmarks = await service.listBookmarks(provider.getQuery());
        const categories = [...new Set(bookmarks.map((bookmark) => normalizeCategory(bookmark.category)))].sort();
        const selected = await vscode.window.showQuickPick(
          [
            { label: "All categories", value: undefined },
            ...categories.map((item) => ({ label: item, value: item }))
          ],
          { placeHolder: "Filter by category" }
        );
        if (selected) {
          provider.setCategoryFilter(selected.value);
        }
      } catch (error) {
        void vscode.window.showErrorMessage(formatCommandError(error));
      }
    }),
    vscode.commands.registerCommand("aweshelf.clearFilters", () => provider.clearFilters()),
    vscode.commands.registerCommand("aweshelf.bookmarkSession", async () => {
      const service = createService(context);
      try {
        const sessions = await service.listSessions(50);
        const session = await pickSession(sessions);
        if (!session) {
          return;
        }
        const edits = await promptNewBookmarkMetadata(service, session);
        if (!edits) {
          return;
        }
        await service.bookmarkSession(session.session_id, edits);
        provider.refresh();
        void vscode.window.showInformationMessage(`Bookmarked ${session.title || session.session_id}`);
      } catch (error) {
        void vscode.window.showErrorMessage(formatCommandError(error));
      }
    }),
    vscode.commands.registerCommand("aweshelf.showBookmarkDetail", async (node?: BookmarkNode) => {
      const bookmark = getSelectedBookmark(node, treeView);
      if (!bookmark) {
        void vscode.window.showWarningMessage("Select an aweshelf bookmark to show.");
        return;
      }

      const service = createService(context);
      try {
        const latestBookmark = await service.showBookmark(bookmark.id);
        const document = await vscode.workspace.openTextDocument({
          language: "markdown",
          content: formatBookmarkDetailMarkdown(latestBookmark)
        });
        await vscode.window.showTextDocument(document, { preview: true });
      } catch (error) {
        void vscode.window.showErrorMessage(formatCommandError(error));
      }
    }),
    vscode.commands.registerCommand("aweshelf.copySessionId", async (node?: BookmarkNode) => {
      const bookmark = getSelectedBookmark(node, treeView);
      if (!bookmark) {
        void vscode.window.showWarningMessage("Select an aweshelf bookmark to copy.");
        return;
      }
      await vscode.env.clipboard.writeText(bookmark.session_id);
      void vscode.window.showInformationMessage(`Copied session ID for ${bookmark.id}`);
    }),
    vscode.commands.registerCommand("aweshelf.copyResumeCommand", async (node?: BookmarkNode) => {
      const bookmark = getSelectedBookmark(node, treeView);
      if (!bookmark) {
        void vscode.window.showWarningMessage("Select an aweshelf bookmark to copy.");
        return;
      }
      const service = createService(context);
      try {
        const target = await service.getResumeTarget(bookmark.id);
        await vscode.env.clipboard.writeText(target.command);
        void vscode.window.showInformationMessage(`Copied resume command for ${bookmark.id}`);
      } catch (error) {
        void vscode.window.showErrorMessage(formatCommandError(error));
      }
    }),
    vscode.commands.registerCommand("aweshelf.openProjectPath", async (node?: BookmarkNode) => {
      const bookmark = getSelectedBookmark(node, treeView);
      if (!bookmark?.project_path) {
        void vscode.window.showWarningMessage("Selected bookmark has no project path.");
        return;
      }
      await vscode.env.openExternal(vscode.Uri.file(bookmark.project_path));
    }),
    vscode.commands.registerCommand("aweshelf.editBookmark", async (node?: BookmarkNode) => {
      const bookmark = getSelectedBookmark(node, treeView);
      if (!bookmark) {
        void vscode.window.showWarningMessage("Select an aweshelf bookmark to edit.");
        return;
      }

      const service = createService(context);
      const edits = await promptBookmarkEdits(service, bookmark);
      if (!edits) {
        return;
      }

      try {
        await service.editBookmark(bookmark.id, edits);
        provider.refresh();
        void vscode.window.showInformationMessage(`Updated ${bookmark.id}`);
      } catch (error) {
        void vscode.window.showErrorMessage(formatCommandError(error));
      }
    }),
    vscode.commands.registerCommand("aweshelf.removeBookmark", async (node?: BookmarkNode) => {
      const bookmark = getSelectedBookmark(node, treeView);
      if (!bookmark) {
        void vscode.window.showWarningMessage("Select an aweshelf bookmark to remove.");
        return;
      }

      const choice = await vscode.window.showWarningMessage(
        `Remove ${bookmark.id} (${bookmark.title || "Untitled"})?`,
        { modal: true },
        "Remove"
      );
      if (choice !== "Remove") {
        return;
      }

      const service = createService(context);
      try {
        await service.removeBookmark(bookmark.id);
        provider.refresh();
        void vscode.window.showInformationMessage(`Removed ${bookmark.id}`);
      } catch (error) {
        void vscode.window.showErrorMessage(formatCommandError(error));
      }
    }),
    vscode.commands.registerCommand("aweshelf.resumeBookmarkWithProfile", async (node?: BookmarkNode) => {
      const bookmark = getSelectedBookmark(node, treeView);
      if (!bookmark) {
        void vscode.window.showWarningMessage("Select an aweshelf bookmark to resume.");
        return;
      }
      const service = createService(context);
      const profile = await pickProfile(service, bookmark.provider, bookmark.aweswitch_profile || undefined, true);
      if (profile === undefined) {
        return;
      }
      openAweshelfTerminal(service, ["resume", bookmark.id, "--profile", profile]);
    }),
    vscode.commands.registerCommand("aweshelf.resumeBookmarkRaw", (node?: BookmarkNode) => {
      const bookmark = getSelectedBookmark(node, treeView);
      if (!bookmark) {
        void vscode.window.showWarningMessage("Select an aweshelf bookmark to resume.");
        return;
      }
      const service = createService(context);
      openAweshelfTerminal(service, ["resume", bookmark.id, "--raw"]);
    }),
    vscode.commands.registerCommand("aweshelf.resumeBookmark", (node?: BookmarkNode) => {
      const bookmark = getSelectedBookmark(node, treeView);
      if (!bookmark) {
        void vscode.window.showWarningMessage("Select an aweshelf bookmark to resume.");
        return;
      }
      const service = createService(context);
      openAweshelfTerminal(service, buildResumeArgs(bookmark.id));
    }),
    vscode.workspace.onDidChangeConfiguration((event) => {
      if (event.affectsConfiguration("aweshelf")) {
        provider.setService(createService(context));
        bookmarkWatcher.dispose();
        bookmarkWatcher = registerBookmarkWatcher(context, provider);
        provider.refresh();
      }
    })
  );
}

export function deactivate(): void {}

function createService(context: vscode.ExtensionContext): AweshelfService {
  const config = vscode.workspace.getConfiguration("aweshelf");
  const configuredCommandPath = config.get<string>("commandPath", "aweshelf");
  return new AweshelfService({
    commandPath: resolveCommandPath(configuredCommandPath, context.extensionPath),
    configPath: config.get<string>("configPath", "")
  });
}

async function promptForCommandPathIfMissing(context: vscode.ExtensionContext): Promise<void> {
  const service = createService(context);
  try {
    await service.checkAvailable();
  } catch (error) {
    if (!isCommandNotFoundError(error)) {
      return;
    }

    const choice = await vscode.window.showErrorMessage(
      formatCommandError(error),
      "Set Path",
      "Open Settings"
    );

    if (choice === "Open Settings") {
      await vscode.commands.executeCommand("workbench.action.openSettings", "aweshelf.commandPath");
      return;
    }

    if (choice === "Set Path") {
      const commandPath = await vscode.window.showInputBox({
        prompt: "Path to the aweshelf executable",
        value: service.commandPath === "aweshelf" ? "" : service.commandPath,
        placeHolder: "/path/to/aweshelf"
      });
      if (commandPath === undefined) {
        return;
      }
      await vscode.workspace
        .getConfiguration("aweshelf")
        .update("commandPath", commandPath.trim() || "aweshelf", vscode.ConfigurationTarget.Global);
      void vscode.window.showInformationMessage("Updated aweshelf.commandPath. Refresh Aweshelf to retry.");
    }
  }
}

function openAweshelfTerminal(service: AweshelfService, args: string[]): void {
  const terminal = vscode.window.createTerminal({
    name: "Aweshelf",
    env: createAweshelfEnv(service.configPath)
  });
  terminal.show();
  terminal.sendText(buildShellCommand(service.commandPath, args));
}

function registerBookmarkWatcher(
  context: vscode.ExtensionContext,
  provider: BookmarkTreeProvider
): vscode.FileSystemWatcher {
  const service = createService(context);
  const configPath = resolveBookmarkConfigPath(service.configPath);
  const watcher = vscode.workspace.createFileSystemWatcher(
    new vscode.RelativePattern(path.dirname(configPath), path.basename(configPath))
  );
  watcher.onDidCreate(() => provider.refresh());
  watcher.onDidChange(() => provider.refresh());
  watcher.onDidDelete(() => provider.refresh());
  context.subscriptions.push(watcher);
  return watcher;
}

function getSelectedBookmark(
  node: BookmarkNode | undefined,
  treeView: vscode.TreeView<BookmarkNode | unknown>
): AweshelfBookmark | undefined {
  return getBookmarkFromTreeNode(node ?? treeView.selection[0]);
}

async function promptBookmarkEdits(
  service: AweshelfService,
  bookmark: AweshelfBookmark
): Promise<BookmarkEdits | undefined> {
  const title = await vscode.window.showInputBox({
    prompt: "Bookmark title",
    value: bookmark.title
  });
  if (title === undefined) {
    return undefined;
  }

  const category = await vscode.window.showInputBox({
    prompt: "Bookmark category",
    value: bookmark.category || ""
  });
  if (category === undefined) {
    return undefined;
  }

  const profile = await pickProfile(service, bookmark.provider, bookmark.aweswitch_profile || undefined, true);
  if (profile === undefined) {
    return undefined;
  }

  const edits: BookmarkEdits = {};
  if (title !== bookmark.title) {
    edits.title = title;
  }
  if (category !== (bookmark.category || "")) {
    edits.category = category;
  }
  if (profile !== (bookmark.aweswitch_profile || "")) {
    edits.profile = profile;
  }

  if (Object.keys(edits).length === 0) {
    void vscode.window.showInformationMessage("No bookmark changes to save.");
    return undefined;
  }

  return edits;
}

async function pickSession(sessions: AweshelfSession[]): Promise<AweshelfSession | undefined> {
  if (sessions.length === 0) {
    void vscode.window.showWarningMessage("No aweshelf sessions found in this project.");
    return undefined;
  }
  const selected = await vscode.window.showQuickPick(
    sessions.map((session) => ({
      label: session.title || "Untitled session",
      description: session.provider,
      detail: `${session.project_path || "-"}\n${session.session_id}`,
      session
    })),
    { placeHolder: "Select a session to bookmark", matchOnDescription: true, matchOnDetail: true }
  );
  return selected?.session;
}

async function promptNewBookmarkMetadata(
  service: AweshelfService,
  session: AweshelfSession
): Promise<BookmarkEdits | undefined> {
  const title = await vscode.window.showInputBox({
    prompt: "Bookmark title",
    value: session.title || "Untitled session"
  });
  if (title === undefined) {
    return undefined;
  }
  const category = await vscode.window.showInputBox({
    prompt: "Bookmark category",
    value: ""
  });
  if (category === undefined) {
    return undefined;
  }
  const profile = await pickProfile(service, session.provider, undefined, false);
  if (profile === undefined && session.provider === "claude") {
    return undefined;
  }
  return {
    title,
    category,
    profile
  };
}

async function pickProfile(
  service: AweshelfService,
  provider: string,
  currentProfile?: string,
  allowClear = false
): Promise<string | undefined> {
  if (provider !== "claude") {
    return "";
  }
  const profiles = loadAweswitchProfiles(provider);
  const picks: Array<{ label: string; description?: string; value: string | undefined }> = [
    { label: allowClear ? "Clear profile" : "No profile", value: "" },
    ...profiles.map((name) => ({
      label: name,
      description: name === currentProfile ? "current" : undefined,
      value: name
    }))
  ];
  const selected = await vscode.window.showQuickPick(picks, {
    placeHolder: "Select aweswitch profile",
    ignoreFocusOut: true
  });
  return selected?.value;
}

function loadAweswitchProfiles(provider: string): string[] {
  const configPath = process.env["AWESWITCH_CONFIG"]
    || path.join(os.homedir(), ".config", "aweswitch", "config.json");
  try {
    const data = JSON.parse(readFileSync(configPath, "utf-8"));
    const profiles = data?.profiles?.[provider];
    if (profiles && typeof profiles === "object") {
      return Object.keys(profiles).sort();
    }
  } catch {
    // config missing or invalid — no profiles available
  }
  return [];
}
