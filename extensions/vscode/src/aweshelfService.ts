import { execFile } from "node:child_process";
import { existsSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { promisify } from "node:util";

import { AweshelfBookmark } from "./bookmark";

const execFileAsync = promisify(execFile);
const SAFE_SHELL_TOKEN = /^[A-Za-z0-9_/:=.,@%+-]+$/;

export interface AweshelfServiceOptions {
  commandPath?: string;
  configPath?: string;
  cwd?: string;
  env?: NodeJS.ProcessEnv;
}

export interface BookmarkEdits {
  title?: string;
  category?: string;
  profile?: string;
}

export interface AweshelfSession {
  session_id: string;
  title: string;
  provider: string;
  project_path: string;
  source_path?: string;
  first_prompt?: string;
  model?: string | null;
  created_at?: string | null;
}

export interface ResumeOptions {
  profile?: string;
  raw?: boolean;
}

export interface ResumeDryRunTarget {
  bookmark_id: string;
  title: string;
  argv: string[];
  cwd: string | null;
  command: string;
  warning?: string | null;
}

export interface ListOptions {
  sortBy?: "title" | "recent" | "id";
  provider?: string;
  category?: string;
}

export function buildListArgs(query?: string, options: ListOptions = {}): string[] {
  const trimmed = query?.trim() ?? "";
  const args = trimmed ? ["search", trimmed, "--json"] : ["list", "--json"];
  if (options.sortBy === "recent") {
    args.push("--sort", "recent");
  }
  if (options.provider) {
    args.push("--provider", options.provider);
  }
  if (options.category) {
    args.push("--category", options.category);
  }
  return args;
}

export function buildVersionArgs(): string[] {
  return ["--version"];
}

export function buildShowArgs(bookmarkId: string): string[] {
  return ["show", bookmarkId, "--json"];
}

export function buildEditArgs(bookmarkId: string, edits: BookmarkEdits): string[] {
  const args = ["edit", bookmarkId];
  if (edits.title !== undefined) {
    args.push("--title", edits.title);
  }
  if (edits.category !== undefined) {
    args.push("--category", edits.category);
  }
  if (edits.profile !== undefined) {
    args.push("--profile", edits.profile);
  }
  if (args.length === 2) {
    throw new Error("edit requires at least one field");
  }
  return args;
}

export function buildResumeArgs(bookmarkId: string): string[] {
  return ["resume", bookmarkId];
}

export function buildRemoveArgs(bookmarkId: string): string[] {
  return ["rm", bookmarkId, "--force"];
}

export function buildBookmarkCurrentArgs(): string[] {
  return ["bookmark", "--current"];
}

export function buildBookmarkSessionArgs(sessionId: string, edits: BookmarkEdits): string[] {
  const args = ["bookmark", sessionId];
  if (edits.title !== undefined) {
    args.push("--title", edits.title);
  }
  if (edits.category !== undefined) {
    args.push("--category", edits.category);
  }
  if (edits.profile !== undefined && edits.profile !== "") {
    args.push("--profile", edits.profile);
  }
  return args;
}

export function buildSessionsArgs(limit = 20): string[] {
  return ["sessions", "--json", "--limit", String(limit)];
}

export function buildResumeDryRunArgs(bookmarkId: string, options: ResumeOptions = {}): string[] {
  const args = ["resume", bookmarkId, "--dry-run", "--json"];
  if (options.profile) {
    args.push("--profile", options.profile);
  }
  if (options.raw) {
    args.push("--raw");
  }
  return args;
}

export function createAweshelfEnv(configPath?: string): NodeJS.ProcessEnv | undefined {
  const trimmed = configPath?.trim();
  if (!trimmed) {
    return undefined;
  }
  return { AWESHELF_CONFIG: trimmed };
}

export function resolveBookmarkConfigPath(configPath?: string, homeDir = os.homedir()): string {
  const trimmed = configPath?.trim();
  return trimmed || path.join(homeDir, ".config", "aweshelf", "bookmarks.json");
}

export function resolveCommandPath(
  configuredCommandPath?: string,
  extensionPath?: string,
  fileExists: (candidate: string) => boolean = existsSync
): string {
  const commandPath = configuredCommandPath?.trim() || "aweshelf";
  if (commandPath !== "aweshelf" || !extensionPath) {
    return commandPath;
  }

  const devVenvCommand = path.resolve(extensionPath, "../../.venv/bin/aweshelf");
  return fileExists(devVenvCommand) ? devVenvCommand : commandPath;
}

export function buildShellCommand(commandPath: string, args: string[]): string {
  return [commandPath, ...args].map(shellQuote).join(" ");
}

export function formatCommandError(error: unknown): string {
  const commandError = error as {
    code?: string;
    path?: string;
    stderr?: string | Buffer;
    message?: string;
  };

  if (isCommandNotFoundError(error)) {
    const executable = commandError.path || "aweshelf";
    return `The aweshelf executable was not found: ${executable}. Set aweshelf.commandPath to the full aweshelf path.`;
  }

  const stderr = commandError.stderr?.toString().trim();
  if (stderr) {
    return stderr;
  }

  return commandError.message || "aweshelf command failed";
}

export function isCommandNotFoundError(error: unknown): boolean {
  return (error as { code?: string }).code === "ENOENT";
}

export class AweshelfService {
  readonly commandPath: string;
  readonly configPath: string;
  private readonly cwd?: string;
  private readonly extraEnv?: NodeJS.ProcessEnv;

  constructor(options: AweshelfServiceOptions = {}) {
    this.commandPath = options.commandPath?.trim() || "aweshelf";
    this.configPath = options.configPath?.trim() || "";
    this.cwd = options.cwd;
    this.extraEnv = options.env;
  }

  async listBookmarks(query?: string, options: ListOptions = {}): Promise<AweshelfBookmark[]> {
    const stdout = await this.runJsonCommand(buildListArgs(query, options));
    const parsed = JSON.parse(stdout);
    if (!Array.isArray(parsed)) {
      throw new Error("aweshelf returned JSON that is not an array");
    }
    return parsed as AweshelfBookmark[];
  }

  async checkAvailable(): Promise<void> {
    await this.runCommand(buildVersionArgs());
  }

  async showBookmark(bookmarkId: string): Promise<AweshelfBookmark> {
    const stdout = await this.runJsonCommand(buildShowArgs(bookmarkId));
    const parsed = JSON.parse(stdout);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      throw new Error("aweshelf returned JSON that is not a bookmark object");
    }
    return parsed as AweshelfBookmark;
  }

  async listSessions(limit = 20): Promise<AweshelfSession[]> {
    const stdout = await this.runJsonCommand(buildSessionsArgs(limit));
    const parsed = JSON.parse(stdout);
    if (!Array.isArray(parsed)) {
      throw new Error("aweshelf returned JSON that is not a session array");
    }
    return parsed as AweshelfSession[];
  }

  async getResumeTarget(bookmarkId: string, options: ResumeOptions = {}): Promise<ResumeDryRunTarget> {
    const stdout = await this.runJsonCommand(buildResumeDryRunArgs(bookmarkId, options));
    const parsed = JSON.parse(stdout);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      throw new Error("aweshelf returned JSON that is not a resume target object");
    }
    return parsed as ResumeDryRunTarget;
  }

  async bookmarkSession(sessionId: string, edits: BookmarkEdits): Promise<void> {
    await this.runCommand(buildBookmarkSessionArgs(sessionId, edits));
  }

  async editBookmark(bookmarkId: string, edits: BookmarkEdits): Promise<void> {
    await this.runCommand(buildEditArgs(bookmarkId, edits));
  }

  async removeBookmark(bookmarkId: string): Promise<void> {
    await this.runCommand(buildRemoveArgs(bookmarkId));
  }

  private async runJsonCommand(args: string[]): Promise<string> {
    const { stdout } = await this.runCommand(args);
    return stdout;
  }

  private async runCommand(args: string[]): Promise<{ stdout: string; stderr: string }> {
    return execFileAsync(this.commandPath, args, {
      cwd: this.cwd,
      env: this.buildChildEnv(),
      maxBuffer: 1024 * 1024 * 8
    });
  }

  private buildChildEnv(): NodeJS.ProcessEnv {
    return {
      ...process.env,
      ...createAweshelfEnv(this.configPath),
      ...this.extraEnv
    };
  }
}

function shellQuote(value: string): string {
  if (value && SAFE_SHELL_TOKEN.test(value)) {
    return value;
  }
  return `'${value.replace(/'/g, "'\\''")}'`;
}
