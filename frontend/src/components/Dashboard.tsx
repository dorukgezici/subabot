import {
  useEffect,
  useRef,
  useState,
  type SyntheticEvent,
  type ReactNode,
} from "react";
import {
  ArrowDownToLine,
  ArrowRight,
  ArrowUpRight,
  Bookmark,
  Check,
  CheckCheck,
  ChevronDown,
  CircleHelp,
  Copy,
  ExternalLink,
  Globe2,
  Inbox,
  LayoutGrid,
  LoaderCircle,
  Menu,
  Plus,
  Radio,
  RefreshCw,
  Rss,
  Search,
  Settings,
  Share2,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Trash2,
  X,
  Zap,
} from "lucide-react";
import Logo from "./Logo";
import {
  api,
  ensureWorkspace,
  json,
  safeLink,
  timeAgo,
  token,
  TOKEN_KEY,
  type Monitor,
  type PublicMonitor,
  type Signal,
  type Template,
  type WorkspaceResponse,
} from "@/lib/api";
import { demoMonitors, demoSignals, demoTemplates } from "@/lib/demo";
import "@/styles/dashboard.css";

type View = "inbox" | "saved" | "monitors" | "templates";
type MonitorDraft = Partial<Monitor>;
const blank: MonitorDraft = {
  name: "",
  description: "",
  keywords: [],
  exclude_keywords: [],
  feed_urls: [],
  match_mode: "any",
  color: "#357a57",
  enabled: true,
};
const colors = ["#357a57", "#7577ac", "#aa7950", "#4c84a5", "#b96976"];
function Modal({
  title,
  children,
  onClose,
  wide = false,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  wide?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    dialog?.showModal();
    return () => dialog?.close();
  }, []);
  return (
    <dialog
      ref={ref}
      className={`modal ${wide ? "wide" : ""}`}
      onCancel={onClose}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      aria-labelledby="modal-title"
    >
      <div className="modal-head">
        <h2 id="modal-title">{title}</h2>
        <button
          className="icon-button"
          onClick={onClose}
          aria-label="Close dialog"
        >
          <X size={20} />
        </button>
      </div>
      {children}
    </dialog>
  );
}
function MonitorForm({
  initial,
  onSave,
  onClose,
}: {
  initial: MonitorDraft;
  onSave: (data: MonitorDraft) => Promise<void>;
  onClose: () => void;
}) {
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [color, setColor] = useState(initial.color || colors[0]);
  async function submit(e: SyntheticEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const list = (name: string) =>
      String(f.get(name) || "")
        .split(name === "feeds" ? /\n/ : /,/)
        .map((x) => x.trim())
        .filter(Boolean);
    setSaving(true);
    setError("");
    try {
      await onSave({
        name: String(f.get("name")).trim(),
        description: String(f.get("description") || "").trim(),
        keywords: list("keywords"),
        exclude_keywords: list("exclude"),
        feed_urls: list("feeds"),
        match_mode: f.get("match") === "all" ? "all" : "any",
        color,
        enabled: initial.enabled ?? true,
      });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  }
  return (
    <Modal
      title={initial.id ? "Edit monitor" : "Find your next signal"}
      onClose={onClose}
    >
      <form onSubmit={submit} className="form-stack">
        <p className="form-intro">
          A few sources. A few keywords. Just the updates you want.
        </p>
        <label>
          Monitor name
          <input
            name="name"
            defaultValue={initial.name}
            placeholder="e.g. My AI radar"
            required
            maxLength={80}
            autoFocus
          />
        </label>
        <label>
          Keywords
          <span className="field-help">
            Separate with commas. We match these in the title and summary.
          </span>
          <input
            name="keywords"
            defaultValue={initial.keywords?.join(", ")}
            placeholder="e.g. AI, open source, language model"
            required
            maxLength={1000}
          />
        </label>
        <label>
          RSS feeds
          <span className="field-help">
            One feed URL per line. Use a site's RSS or Atom URL.
          </span>
          <textarea
            name="feeds"
            defaultValue={initial.feed_urls?.join("\n")}
            placeholder={
              "https://hnrss.org/frontpage\nhttps://example.com/feed.xml"
            }
            rows={3}
            required
            maxLength={12000}
          />
        </label>
        <div className="form-split">
          <label>
            Match
            <select name="match" defaultValue={initial.match_mode || "any"}>
              <option value="any">Any keyword</option>
              <option value="all">All keywords</option>
            </select>
          </label>
          <fieldset className="color-picker">
            <legend>Monitor color</legend>
            {colors.map((c) => (
              <button
                type="button"
                key={c}
                style={{ background: c }}
                aria-label={`Select ${c} color`}
                aria-pressed={color === c}
                onClick={() => setColor(c)}
              >
                {color === c && <Check size={14} />}
              </button>
            ))}
          </fieldset>
        </div>
        <details className="advanced">
          <summary>
            Fine-tune your monitor <ChevronDown size={14} />
          </summary>
          <label>
            Exclude keywords
            <input
              name="exclude"
              defaultValue={initial.exclude_keywords?.join(", ")}
              placeholder="e.g. sponsored, giveaway"
              maxLength={1000}
            />
          </label>
          <label>
            Description
            <textarea
              name="description"
              defaultValue={initial.description}
              placeholder="A short note about what you're following"
              rows={2}
              maxLength={300}
            />
          </label>
        </details>
        {error && (
          <p className="inline-error" role="alert">
            {error}
          </p>
        )}
        <div className="modal-footer">
          <span>
            <ShieldCheck size={14} />
            Private by default
          </span>
          <button type="submit" className="button primary" disabled={saving}>
            {saving ? (
              <LoaderCircle className="spin" size={16} />
            ) : (
              <Radio size={16} />
            )}{" "}
            {initial.id ? "Save changes" : "Create monitor"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export default function Dashboard() {
  const [demo] = useState(
    () =>
      typeof window !== "undefined" &&
      new URLSearchParams(window.location.search).get("demo") === "1",
  );
  const [monitors, setMonitors] = useState<Monitor[]>(demo ? demoMonitors : []);
  const [signals, setSignals] = useState<Signal[]>(demo ? demoSignals : []);
  const [templates, setTemplates] = useState<Template[]>(
    demo ? demoTemplates : [],
  );
  const [workspace, setWorkspace] = useState<WorkspaceResponse>({
    workspace: {
      id: "",
      name: demo ? "The curious workspace" : "My workspace",
    },
    slack: { connected: false },
    stats: { monitors: 0, signals: 0, unread: 0 },
  });
  const [hasMore, setHasMore] = useState(false);
  const [nextOffset, setNextOffset] = useState(0);
  const [signalLoading, setSignalLoading] = useState(false);
  const [signalError, setSignalError] = useState("");
  const [loading, setLoading] = useState(!demo);
  const [loadError, setLoadError] = useState("");
  const [view, setView] = useState<View>("inbox");
  const [filter, setFilter] = useState("all");
  const [monitorFilter, setMonitorFilter] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [mobile, setMobile] = useState(false);
  const [toast, setToast] = useState("");
  const [scanning, setScanning] = useState(false);
  const [scanError, setScanError] = useState("");
  const [editor, setEditor] = useState<MonitorDraft | null>(null);
  const [settings, setSettings] = useState(false);
  const [sharing, setSharing] = useState<Monitor | null>(null);
  const [busy, setBusy] = useState(false);
  const searchRef = useRef<HTMLInputElement>(null);
  const sidebarRef = useRef<HTMLElement>(null);
  const pendingSignals = useRef(new Set<string>());
  const requestKey = [view, filter, monitorFilter, query.trim()].join("\0");
  const currentRequest = useRef(requestKey);
  currentRequest.current = requestKey;
  const initialized = useRef(false);
  function signalPath(offset = 0) {
    const params = new URLSearchParams({ limit: "50", offset: String(offset) });
    if (view === "saved") params.set("bookmarked", "true");
    if (filter === "unread") params.set("unread", "true");
    if (monitorFilter) params.set("monitor_id", monitorFilter);
    if (query.trim()) params.set("search", query.trim());
    return `/signals?${params}`;
  }
  async function reload() {
    const key = requestKey;
    const [w, m, s, t] = await Promise.all([
      api<WorkspaceResponse>("/workspace"),
      api<Monitor[]>("/monitors"),
      api<Signal[]>(signalPath()),
      api<Template[]>("/templates"),
    ]);
    setWorkspace(w);
    setMonitors(m);
    if (key === currentRequest.current) {
      setSignals(s);
      setHasMore(s.length === 50);
      setNextOffset(s.length);
    }
    setTemplates(t);
    return t;
  }
  async function loadMore() {
    const key = requestKey;
    setSignalLoading(true);
    setSignalError("");
    try {
      const more = await api<Signal[]>(signalPath(nextOffset));
      if (key !== currentRequest.current) return;
      setSignals((prev) => [
        ...prev,
        ...more.filter((s) => !prev.some((p) => p.id === s.id)),
      ]);
      setNextOffset((prev) => prev + more.length);
      setHasMore(more.length === 50);
    } catch (e) {
      if (key === currentRequest.current) setSignalError((e as Error).message);
    } finally {
      if (key === currentRequest.current) setSignalLoading(false);
    }
  }

  async function boot() {
    setLoading(true);
    setLoadError("");
    try {
      await ensureWorkspace();
      const ts = await reload();
      const params = new URLSearchParams(location.search);
      const chosen = ts.find((t) => t.id === params.get("template"));
      if (chosen) {
        const { id, ...draft } = chosen;
        setEditor(draft);
      }
      if (params.get("clone")) {
        const data = await api<PublicMonitor>(
          `/public/${encodeURIComponent(params.get("clone")!)}`,
        );
        const m = data.monitor;
        setEditor({
          name: m.name,
          description: m.description,
          keywords: m.keywords,
          exclude_keywords: m.exclude_keywords,
          match_mode: m.match_mode,
          feed_urls: m.feed_urls,
          color: m.color,
          public: false,
        });
      }
      if (params.has("template") || params.has("clone"))
        history.replaceState(null, "", "/dashboard");
    } catch (e) {
      setLoadError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    if (!demo && !initialized.current) {
      initialized.current = true;
      void boot();
    }
  }, [demo]);
  useEffect(() => {
    if (!toast) return;
    const id = setTimeout(() => setToast(""), 5000);
    return () => clearTimeout(id);
  }, [toast]);
  useEffect(() => {
    if (!mobile) return;
    const previous = document.activeElement as HTMLElement | null;
    const controls = () =>
      Array.from(
        sidebarRef.current?.querySelectorAll<HTMLElement>(
          "a[href],button:not(:disabled),input:not(:disabled)",
        ) || [],
      ).filter((el) => el.offsetParent !== null);
    controls()[0]?.focus();
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        setMobile(false);
      }
      if (event.key === "Tab") {
        const items = controls();
        const first = items[0];
        const last = items.at(-1);
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        }
        if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }
    }
    const media = matchMedia("(max-width: 760px)");
    const resized = () => {
      if (!media.matches) setMobile(false);
    };
    document.addEventListener("keydown", onKey);
    media.addEventListener("change", resized);
    return () => {
      document.removeEventListener("keydown", onKey);
      media.removeEventListener("change", resized);
      previous?.focus();
    };
  }, [mobile]);
  useEffect(() => {
    function shortcut(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        searchRef.current?.focus();
      }
    }
    window.addEventListener("keydown", shortcut);
    return () => window.removeEventListener("keydown", shortcut);
  }, []);
  const unread = demo
    ? signals.filter((s) => !s.is_read).length
    : workspace.stats.unread;
  const saved = demo
    ? signals.filter((s) => s.is_bookmarked).length
    : workspace.stats.bookmarked || 0;
  const active = monitors.filter((m) => m.enabled).length;
  const sourceCount = new Set(monitors.flatMap((m) => m.feed_urls)).size;
  const visible = signals.filter(
    (s) =>
      (view !== "saved" || s.is_bookmarked) &&
      (filter !== "unread" || !s.is_read) &&
      (!monitorFilter || s.monitor_id === monitorFilter) &&
      `${s.title} ${s.summary} ${s.source} ${s.matched_keywords.join(" ")}`
        .toLowerCase()
        .includes(query.trim().toLowerCase()),
  );
  useEffect(() => {
    if (demo || loading || loadError || !["inbox", "saved"].includes(view))
      return;
    const controller = new AbortController();
    const timer = setTimeout(
      () => {
        setSignalLoading(true);
        setSignalError("");
        void api<Signal[]>(signalPath(), { signal: controller.signal })
          .then((items) => {
            if (controller.signal.aborted) return;
            setSignals(items);
            setHasMore(items.length === 50);
            setNextOffset(items.length);
          })
          .catch((e) => {
            if (!controller.signal.aborted) setSignalError(e.message);
          })
          .finally(() => {
            if (!controller.signal.aborted) setSignalLoading(false);
          });
      },
      query ? 250 : 0,
    );
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [view, filter, monitorFilter, query, loading, loadError, demo]);
  const selectedMonitor = monitors.find((m) => m.id === monitorFilter);
  function go(next: View, id: string | null = null) {
    setView(next);
    setMonitorFilter(id);
    setFilter("all");
    setQuery("");
    setMobile(false);
  }
  async function act(fn: () => Promise<void>) {
    setBusy(true);
    try {
      await fn();
    } catch (e) {
      setToast((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function saveMonitor(data: MonitorDraft) {
    if (demo) {
      setMonitors((prev) =>
        editor?.id
          ? prev.map((m) => (m.id === editor.id ? { ...m, ...data } : m))
          : [
              ...prev,
              {
                ...blank,
                ...data,
                id: `demo-${Date.now()}`,
                public: false,
                share_slug: null,
                created_at: new Date().toISOString(),
                last_checked_at: null,
              } as Monitor,
            ],
      );
    } else {
      const result = await api<Monitor>(
        editor?.id ? `/monitors/${editor.id}` : "/monitors",
        json(editor?.id ? "PATCH" : "POST", data),
      );
      setMonitors((prev) =>
        editor?.id
          ? prev.map((m) => (m.id === result.id ? result : m))
          : [...prev, result],
      );
    }
    setEditor(null);
    setToast(
      editor?.id
        ? "Monitor updated."
        : "Your monitor is ready. Check for signals to see your first matches.",
    );
    go("monitors");
  }
  async function patchSignal(signal: Signal, patch: Partial<Signal>) {
    if (pendingSignals.current.has(signal.id)) return;
    pendingSignals.current.add(signal.id);
    try {
      if (!demo) await api(`/signals/${signal.id}`, json("PATCH", patch));
      setSignals((prev) =>
        prev.map((s) => (s.id === signal.id ? { ...s, ...patch } : s)),
      );
      if (!demo)
        setWorkspace((prev) => ({
          ...prev,
          stats: {
            ...prev.stats,
            unread: Math.max(
              0,
              prev.stats.unread +
                (patch.is_read === undefined || patch.is_read === signal.is_read
                  ? 0
                  : patch.is_read
                    ? -1
                    : 1),
            ),
            bookmarked: Math.max(
              0,
              (prev.stats.bookmarked || 0) +
                (patch.is_bookmarked === undefined ||
                patch.is_bookmarked === signal.is_bookmarked
                  ? 0
                  : patch.is_bookmarked
                    ? 1
                    : -1),
            ),
          },
        }));
    } catch (e) {
      setToast((e as Error).message);
    } finally {
      pendingSignals.current.delete(signal.id);
    }
  }
  async function scan() {
    if (demo) {
      setToast(
        "This is sample data. Create your workspace to check real feeds.",
      );
      return;
    }
    setScanning(true);
    setScanError("");
    try {
      const result = await api<{
        checked: number;
        new_signals: number;
        errors: { feed_url: string; message: string }[];
      }>("/scan", json("POST"));
      await reload();
      setToast(
        `${result.new_signals} new signal${result.new_signals === 1 ? "" : "s"} found across ${result.checked} feed${result.checked === 1 ? "" : "s"}.`,
      );
      if (result.errors.length)
        setScanError(
          result.errors.map((e) => `${e.feed_url}: ${e.message}`).join("\n"),
        );
    } catch (e) {
      setScanError((e as Error).message);
    } finally {
      setScanning(false);
    }
  }
  async function updateMonitor(m: Monitor, patch: Partial<Monitor>) {
    const updated = demo
      ? { ...m, ...patch }
      : await api<Monitor>(`/monitors/${m.id}`, json("PATCH", patch));
    setMonitors((prev) =>
      prev.map((item) => (item.id === m.id ? updated : item)),
    );
    return updated;
  }
  async function removeMonitor(m: Monitor) {
    if (!confirm(`Delete "${m.name}" and its signals? This cannot be undone.`))
      return;
    await act(async () => {
      if (!demo) await api(`/monitors/${m.id}`, json("DELETE"));
      setMonitors((prev) => prev.filter((x) => x.id !== m.id));
      setSignals((prev) => prev.filter((x) => x.monitor_id !== m.id));
      if (!demo) await reload();
      setToast("Monitor deleted.");
    });
  }
  const title =
    view === "monitors"
      ? "Your monitors"
      : view === "templates"
        ? "Find your next obsession."
        : view === "saved"
          ? "The ones worth keeping."
          : selectedMonitor
            ? selectedMonitor.name
            : "Your signal inbox";
  return (
    <div className="app-shell">
      {mobile && (
        <button
          className="sidebar-scrim"
          onClick={() => setMobile(false)}
          aria-label="Close navigation"
        />
      )}
      <aside
        ref={sidebarRef}
        id="workspace-navigation"
        role={mobile ? "dialog" : undefined}
        aria-modal={mobile || undefined}
        aria-label={mobile ? "Workspace navigation" : undefined}
        className={`sidebar ${mobile ? "is-open" : ""}`}
      >
        <div className="sidebar-brand">
          <Logo />
          <button
            className="icon-button mobile-close"
            onClick={() => setMobile(false)}
            aria-label="Close navigation"
          >
            <X size={18} />
          </button>
        </div>
        <button
          className="workspace-switch"
          onClick={() => {
            setMobile(false);
            setSettings(true);
          }}
        >
          <span className="workspace-avatar">{demo ? "C" : "M"}</span>
          <span>
            <strong>{workspace.workspace.name}</strong>
            <small>{demo ? "Sample workspace" : "Personal workspace"}</small>
          </span>
          <ChevronDown size={14} />
        </button>
        <div className="nav-label">WORKSPACE</div>
        <nav className="app-nav" aria-label="Workspace">
          <button
            className={view === "inbox" && !monitorFilter ? "active" : ""}
            onClick={() => go("inbox")}
          >
            <Inbox size={18} />
            Signal inbox<span className="nav-count">{unread || ""}</span>
          </button>
          <button
            className={view === "saved" ? "active" : ""}
            onClick={() => go("saved")}
          >
            <Bookmark size={18} />
            Saved signals
            {saved > 0 && <span className="subtle-count">{saved}</span>}
          </button>
          <button
            className={view === "monitors" ? "active" : ""}
            onClick={() => go("monitors")}
          >
            <Radio size={18} />
            Monitors<span className="subtle-count">{monitors.length}</span>
          </button>
          <button
            className={view === "templates" ? "active" : ""}
            onClick={() => go("templates")}
          >
            <LayoutGrid size={18} />
            Templates<span className="tiny-new">NEW</span>
          </button>
        </nav>
        <div className="nav-label monitor-nav-label">
          YOUR MONITORS
          <button
            onClick={() => {
              setMobile(false);
              setEditor({ ...blank });
            }}
            className="icon-button"
            aria-label="Add monitor"
          >
            <Plus size={15} />
          </button>
        </div>
        <div className="monitor-nav">
          {monitors.map((m) => (
            <button
              key={m.id}
              className={monitorFilter === m.id ? "active" : ""}
              onClick={() => go("inbox", m.id)}
            >
              <span
                className="color-dot"
                style={{ background: m.color, opacity: m.enabled ? 1 : 0.35 }}
              />
              {m.name}
              {!m.enabled && <span className="paused-dot">paused</span>}
            </button>
          ))}
          {!monitors.length && (
            <p>
              Your next curiosity
              <br />
              starts with a monitor.
            </p>
          )}
        </div>
        <div className="sidebar-bottom">
          <div className="slack-nudge">
            <span className="slack-mark" aria-hidden="true">
              ✳
            </span>
            <strong>
              {workspace.slack.connected
                ? "Slack is connected"
                : "Good signals travel."}
            </strong>
            <p>
              {workspace.slack.connected
                ? "New matches go straight to your channel."
                : "Bring the updates that matter into your Slack."}
            </p>
            <button
              onClick={() => {
                setMobile(false);
                setSettings(true);
              }}
            >
              {workspace.slack.connected
                ? "Manage connection"
                : "Connect Slack"}
              <ArrowUpRight size={14} />
            </button>
          </div>
          <button
            className="sidebar-settings"
            onClick={() => {
              setMobile(false);
              setSettings(true);
            }}
          >
            <Settings size={17} />
            Settings & connections
          </button>
          <a
            className="creator-credit"
            href="https://github.com/dorukgezici"
            target="_blank"
            rel="noreferrer"
          >
            <span className="creator-avatar">dg</span>
            <span>
              Made with curiosity
              <br />
              <strong>
                by Doruk Gezici <ArrowUpRight size={11} />
              </strong>
            </span>
          </a>
        </div>
      </aside>
      <div className="app-main" inert={mobile}>
        <header className="app-topbar">
          <button
            className="icon-button mobile-toggle"
            onClick={() => setMobile(true)}
            aria-label="Open navigation"
            aria-expanded={mobile}
            aria-controls="workspace-navigation"
          >
            <Menu size={21} />
          </button>
          <div className="breadcrumb">
            Workspace <span>/</span>
            <strong>
              {view === "inbox"
                ? "Signal inbox"
                : view === "saved"
                  ? "Saved signals"
                  : view === "monitors"
                    ? "Monitors"
                    : "Templates"}
            </strong>
          </div>
          <div className="topbar-right">
            <span className="status-pill">
              <span />
              {demo ? "Interactive demo" : "Your private workspace"}
            </span>
            <a
              className="icon-button"
              href="https://github.com/dorukgezici/subabot#readme"
              target="_blank"
              rel="noreferrer"
              aria-label="Help and documentation"
            >
              <CircleHelp size={18} />
            </a>
            <button
              className="profile-avatar"
              onClick={() => {
                setMobile(false);
                setSettings(true);
              }}
              aria-label="Workspace settings"
            >
              {demo ? "C" : "M"}
            </button>
          </div>
        </header>
        {demo && (
          <div className="demo-banner">
            <span>
              <Sparkles size={14} />
              You’re exploring sample signals. Make yourself at home.
            </span>
            <a href="/dashboard">
              Create my workspace <ArrowRight size={14} />
            </a>
          </div>
        )}
        <main id="main" className="dashboard-content">
          <div className="page-heading">
            <div>
              <div className="heading-eyebrow">
                <span className="color-dot" />A LITTLE LESS NOISE
              </div>
              <h1>{title}</h1>
              <p>
                {view === "monitors"
                  ? "Small radars for the things you care about."
                  : view === "templates"
                    ? "Start with a good idea. Make it your own."
                    : view === "saved"
                      ? "Your personal collection of useful finds."
                      : "The updates you care about, with room to breathe."}
              </p>
            </div>
            <button
              className="button primary"
              onClick={() => {
                setMobile(false);
                setEditor({ ...blank });
              }}
            >
              <Plus size={17} />
              New monitor
            </button>
          </div>
          {loading ? (
            <div className="loading-state">
              <LoaderCircle size={28} className="spin" />
              <h2>Making room for your signals.</h2>
              <p>Opening your workspace...</p>
            </div>
          ) : loadError ? (
            <div className="empty-state">
              <Radio size={32} />
              <h2>We couldn’t open your workspace.</h2>
              <p>{loadError}</p>
              <div className="button-row">
                <button className="button primary" onClick={() => void boot()}>
                  Try again
                </button>
                <button
                  className="button"
                  onClick={() => {
                    setMobile(false);
                    setSettings(true);
                  }}
                >
                  Restore workspace
                </button>
                <a className="button" href="/dashboard?demo=1">
                  Explore the demo
                </a>
                <button
                  className="button ghost"
                  onClick={() => {
                    if (
                      !confirm(
                        "Open a new workspace in this browser? Keep your current recovery key if you want to return to your existing workspace. Its server data will not be deleted.",
                      )
                    )
                      return;
                    localStorage.removeItem(TOKEN_KEY);
                    void boot();
                  }}
                >
                  Start a new workspace
                </button>
              </div>
            </div>
          ) : (
            <>
              {(view === "inbox" || view === "saved") && (
                <>
                  <div className="overview-strip">
                    <div>
                      <span className="stat-icon">
                        <Zap size={17} />
                      </span>
                      <strong>
                        {demo ? signals.length : workspace.stats.signals}
                        <small>Signals collected</small>
                      </strong>
                    </div>
                    <div>
                      <span className="stat-icon">
                        <Radio size={17} />
                      </span>
                      <strong>
                        {active}
                        <small>Active monitors</small>
                      </strong>
                    </div>
                    <div>
                      <span className="stat-icon">
                        <Rss size={17} />
                      </span>
                      <strong>
                        {sourceCount}
                        <small>Sources connected</small>
                      </strong>
                    </div>
                    <button
                      className="check-signals"
                      onClick={() => void scan()}
                      disabled={scanning || !active}
                    >
                      <RefreshCw size={14} className={scanning ? "spin" : ""} />
                      {scanning ? "Checking sources..." : "Check for signals"}
                    </button>
                  </div>
                  <div className="inbox-layout">
                    <section className="signal-panel" aria-label="Signals">
                      <div className="inbox-toolbar">
                        <div className="inbox-tabs">
                          <button
                            className={filter === "all" ? "selected" : ""}
                            onClick={() => setFilter("all")}
                          >
                            {view === "saved" ? "Saved" : "All signals"}
                            {!monitorFilter && (
                              <span>
                                {view === "saved"
                                  ? saved
                                  : demo
                                    ? signals.length
                                    : workspace.stats.signals}
                              </span>
                            )}
                          </button>
                          <button
                            className={filter === "unread" ? "selected" : ""}
                            onClick={() => setFilter("unread")}
                          >
                            Unread
                            {!monitorFilter && view !== "saved" && (
                              <span>{unread}</span>
                            )}
                          </button>
                        </div>
                        <button
                          className="icon-button"
                          title="Mark visible signals as read"
                          aria-label="Mark visible signals as read"
                          disabled={busy || !visible.some((s) => !s.is_read)}
                          onClick={() =>
                            void act(async () => {
                              const unreadSignals = visible.filter(
                                (s) => !s.is_read,
                              );
                              if (!demo)
                                await Promise.all(
                                  unreadSignals.map((s) =>
                                    api(
                                      `/signals/${s.id}`,
                                      json("PATCH", { is_read: true }),
                                    ),
                                  ),
                                );
                              setSignals((prev) =>
                                prev.map((s) =>
                                  visible.some((v) => v.id === s.id)
                                    ? { ...s, is_read: true }
                                    : s,
                                ),
                              );
                              if (!demo)
                                setWorkspace((prev) => ({
                                  ...prev,
                                  stats: {
                                    ...prev.stats,
                                    unread: Math.max(
                                      0,
                                      prev.stats.unread - unreadSignals.length,
                                    ),
                                  },
                                }));
                              setToast("All visible signals marked as read.");
                            })
                          }
                        >
                          <CheckCheck size={18} />
                        </button>
                      </div>
                      <label className="search-box">
                        <Search size={17} />
                        <input
                          ref={searchRef}
                          placeholder="Search your signals..."
                          aria-label="Search signals"
                          value={query}
                          maxLength={200}
                          onChange={(e) => setQuery(e.target.value)}
                        />
                        <kbd>⌘ K</kbd>
                      </label>
                      {selectedMonitor && (
                        <div className="filter-notice">
                          <span
                            className="color-dot"
                            style={{ background: selectedMonitor.color }}
                          />
                          {selectedMonitor.name}
                          <button
                            onClick={() => setMonitorFilter(null)}
                            aria-label="Clear monitor filter"
                          >
                            <X size={13} />
                          </button>
                        </div>
                      )}
                      {scanError && (
                        <div className="scan-warning" role="alert">
                          <strong>Some sources need attention</strong>
                          <p>{scanError}</p>
                          <button
                            onClick={() => setScanError("")}
                            className="text-button"
                          >
                            Dismiss
                          </button>
                        </div>
                      )}
                      {signalError && (
                        <p className="inline-error" role="alert">
                          {signalError}
                        </p>
                      )}
                      {signalLoading && (
                        <div className="signal-loading" role="status">
                          <LoaderCircle size={14} className="spin" /> Finding
                          your signals...
                        </div>
                      )}
                      {visible.length ? (
                        <>
                          <div className="list-label">
                            <span>
                              {query
                                ? "SEARCH RESULTS"
                                : filter === "unread"
                                  ? "WAITING FOR YOU"
                                  : "LATEST SIGNALS"}
                            </span>
                            <span>
                              {demo
                                ? "SAMPLE DATA"
                                : `${visible.length} updates`}
                            </span>
                          </div>
                          <div className="signals-list">
                            {visible.map((signal) => {
                              const monitor = monitors.find(
                                (m) => m.id === signal.monitor_id,
                              );
                              return (
                                <article
                                  className={`signal-card ${signal.is_read ? "is-read" : ""}`}
                                  key={signal.id}
                                >
                                  <div className="signal-source">
                                    <span
                                      className="source-avatar"
                                      style={{
                                        background: `${monitor?.color || "#357a57"}12`,
                                        color: monitor?.color || "#357a57",
                                      }}
                                    >
                                      {signal.source.slice(0, 1).toUpperCase()}
                                    </span>
                                    <span>{signal.source}</span>
                                    <span className="source-separator">·</span>
                                    <time
                                      dateTime={
                                        signal.published_at || undefined
                                      }
                                    >
                                      {timeAgo(signal.published_at)}
                                    </time>
                                    {!signal.is_read && (
                                      <span
                                        className="unread-dot"
                                        aria-label="Unread"
                                      />
                                    )}
                                    <button
                                      className={`icon-button bookmark-button ${signal.is_bookmarked ? "is-saved" : ""}`}
                                      onClick={() =>
                                        void patchSignal(signal, {
                                          is_bookmarked: !signal.is_bookmarked,
                                        })
                                      }
                                      aria-label={
                                        signal.is_bookmarked
                                          ? "Unsave signal"
                                          : "Save signal"
                                      }
                                      aria-pressed={signal.is_bookmarked}
                                    >
                                      <Bookmark
                                        size={17}
                                        fill={
                                          signal.is_bookmarked
                                            ? "currentColor"
                                            : "none"
                                        }
                                      />
                                    </button>
                                  </div>
                                  <a
                                    className="signal-title"
                                    href={safeLink(signal.url)}
                                    target="_blank"
                                    rel="noreferrer"
                                    onClick={() =>
                                      void patchSignal(signal, {
                                        is_read: true,
                                      })
                                    }
                                  >
                                    <h2>{signal.title}</h2>
                                    <ArrowUpRight size={17} />
                                  </a>
                                  <p className="signal-summary">
                                    {signal.summary}
                                  </p>
                                  <div className="signal-footer">
                                    <button
                                      className="monitor-chip"
                                      onClick={() =>
                                        go("inbox", monitor?.id || null)
                                      }
                                    >
                                      <span
                                        className="color-dot"
                                        style={{ background: monitor?.color }}
                                      />
                                      {monitor?.name || "Monitor"}
                                    </button>
                                    <span className="matched-label">
                                      Matched
                                    </span>
                                    {signal.matched_keywords
                                      .slice(0, 3)
                                      .map((k) => (
                                        <span className="keyword-chip" key={k}>
                                          {k}
                                        </span>
                                      ))}
                                    <button
                                      className="read-toggle"
                                      onClick={() =>
                                        void patchSignal(signal, {
                                          is_read: !signal.is_read,
                                        })
                                      }
                                      aria-label={
                                        signal.is_read
                                          ? "Mark as unread"
                                          : "Mark as read"
                                      }
                                      title={
                                        signal.is_read
                                          ? "Mark as unread"
                                          : "Mark as read"
                                      }
                                    >
                                      {signal.is_read ? (
                                        <CheckCheck size={15} />
                                      ) : (
                                        <Check size={15} />
                                      )}
                                    </button>
                                  </div>
                                </article>
                              );
                            })}
                          </div>
                          <div className="end-note">
                            <span />A little more informed. A little less
                            overwhelmed.
                            <span />
                          </div>
                        </>
                      ) : (
                        <div className="empty-state">
                          <div className="empty-icon">
                            {view === "saved" ? (
                              <Bookmark size={28} />
                            ) : query ? (
                              <Search size={28} />
                            ) : (
                              <Radio size={28} />
                            )}
                          </div>
                          <h2>
                            {query
                              ? "No signals found."
                              : view === "saved"
                                ? "Keep the good ones close."
                                : filter === "unread"
                                  ? "A clear inbox. A clear head."
                                  : monitors.length
                                    ? "Your next signal is out there."
                                    : "What are you curious about?"}
                          </h2>
                          <p>
                            {query
                              ? "Try a different word or clear your search."
                              : view === "saved"
                                ? "Save a signal using the bookmark icon. Find it right here whenever you need it."
                                : filter === "unread"
                                  ? "You’ve read every signal in this view. Come back when something new catches your radar."
                                  : monitors.length
                                    ? "Your monitors are ready. Check your sources for matching stories."
                                    : "Create a monitor to collect the updates you actually want to read. A starter template makes it easy."}
                          </p>
                          {query ? (
                            <button
                              className="button"
                              onClick={() => setQuery("")}
                            >
                              Clear search
                            </button>
                          ) : !monitors.length ? (
                            <button
                              className="button primary"
                              onClick={() => go("templates")}
                            >
                              Explore starter templates
                              <ArrowRight size={16} />
                            </button>
                          ) : filter === "all" && view !== "saved" ? (
                            <button
                              className="button primary"
                              onClick={() => void scan()}
                              disabled={scanning}
                            >
                              {scanning
                                ? "Checking..."
                                : "Find my first signals"}
                            </button>
                          ) : null}
                        </div>
                      )}
                      {hasMore && !demo && (
                        <div className="load-more">
                          <button
                            className="button"
                            onClick={() => void loadMore()}
                            disabled={signalLoading}
                          >
                            Load more signals
                            <ChevronDown size={14} />
                          </button>
                        </div>
                      )}
                    </section>
                    <aside className="inbox-aside">
                      <div className="aside-head">
                        <h2>On your radar</h2>
                        <button
                          className="icon-button"
                          onClick={() => go("monitors")}
                          aria-label="Manage monitors"
                        >
                          <SlidersHorizontal size={16} />
                        </button>
                      </div>
                      {monitors.slice(0, 5).map((m) => (
                        <button
                          className="radar-item"
                          key={m.id}
                          onClick={() => go("inbox", m.id)}
                        >
                          <span
                            className="radar-icon"
                            style={{
                              background: `${m.color}12`,
                              color: m.color,
                            }}
                          >
                            <Radio size={18} />
                          </span>
                          <span>
                            <strong>{m.name}</strong>
                            <small>{m.keywords.slice(0, 3).join(", ")}</small>
                          </span>
                          <span
                            className={`monitor-status ${m.enabled ? "on" : ""}`}
                          />
                        </button>
                      ))}
                      <button
                        className="add-radar"
                        onClick={() => {
                          setMobile(false);
                          setEditor({ ...blank });
                        }}
                      >
                        <Plus size={16} />
                        Add a monitor
                      </button>
                      <div className="discovery-card">
                        <span className="discovery-icon">
                          <Sparkles size={22} />
                        </span>
                        <span className="eyebrow">CURIOSITY, SHARED</span>
                        <h3>
                          A good radar is
                          <br />
                          even better shared.
                        </h3>
                        <p>
                          Publish a watchlist. Give someone else a head start.
                        </p>
                        <button onClick={() => go("monitors")}>
                          Share your curiosity
                          <ArrowUpRight size={15} />
                        </button>
                        <div className="orbit-art" aria-hidden="true">
                          <i />
                          <i />
                          <i />
                          <span />
                        </div>
                      </div>
                      <div className="quiet-note">
                        <ShieldCheck size={15} />
                        <p>
                          Your monitors are private.
                          <br />
                          You decide what gets shared.
                        </p>
                      </div>
                    </aside>
                  </div>
                </>
              )}
              {view === "monitors" && (
                <>
                  <div className="section-toolbar">
                    <span>
                      {monitors.length} monitors{" "}
                      <span className="muted">· {active} active</span>
                    </span>
                    <span className="muted">
                      <ShieldCheck size={14} /> Private until you publish
                    </span>
                  </div>
                  {!monitors.length ? (
                    <div className="empty-state">
                      <Radio size={32} />
                      <h2>A home for your curiosity.</h2>
                      <p>Add your first monitor or start with a template.</p>
                      <button
                        className="button primary"
                        onClick={() => go("templates")}
                      >
                        Explore templates
                        <ArrowRight size={16} />
                      </button>
                    </div>
                  ) : (
                    <div className="monitor-grid">
                      {monitors.map((m) => (
                        <article className="monitor-card" key={m.id}>
                          <div className="monitor-card-top">
                            <span
                              className="large-radar"
                              style={{
                                color: m.color,
                                background: `${m.color}12`,
                              }}
                            >
                              <Radio size={23} />
                            </span>
                            <label className="switch">
                              <input
                                type="checkbox"
                                checked={m.enabled}
                                aria-label={`${m.enabled ? "Pause" : "Resume"} ${m.name}`}
                                disabled={busy}
                                onChange={() =>
                                  void act(async () => {
                                    await updateMonitor(m, {
                                      enabled: !m.enabled,
                                    });
                                  })
                                }
                              />
                              <span />
                            </label>
                          </div>
                          <button
                            className="monitor-title-button"
                            onClick={() => go("inbox", m.id)}
                          >
                            <h2>{m.name}</h2>
                            <ArrowUpRight size={16} />
                          </button>
                          <p>
                            {m.description ||
                              `Following ${m.keywords.join(", ")}`}
                          </p>
                          <div className="monitor-keywords">
                            {m.keywords.slice(0, 4).map((k) => (
                              <span className="keyword-chip" key={k}>
                                {k}
                              </span>
                            ))}
                          </div>
                          <div className="monitor-meta">
                            <span>
                              <Rss size={13} />
                              {m.feed_urls.length} sources
                            </span>
                            <span>
                              {m.last_checked_at
                                ? "Checked " + timeAgo(m.last_checked_at)
                                : "Not checked yet"}
                            </span>
                            <span className={m.enabled ? "text-green" : ""}>
                              {m.enabled ? "Active" : "Paused"}
                            </span>
                          </div>
                          {m.last_error && (
                            <p className="monitor-error" role="status">
                              {m.last_error}
                            </p>
                          )}
                          <div className="monitor-actions">
                            <button onClick={() => setEditor(m)}>
                              <SlidersHorizontal size={14} />
                              Edit
                            </button>
                            <button onClick={() => setSharing(m)}>
                              <Share2 size={14} />
                              {m.public ? "Published" : "Share"}
                            </button>
                            <button
                              onClick={() => void removeMonitor(m)}
                              aria-label={`Delete ${m.name}`}
                              disabled={busy}
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </article>
                      ))}
                      <button
                        className="new-monitor-card"
                        onClick={() => {
                          setMobile(false);
                          setEditor({ ...blank });
                        }}
                      >
                        <span>
                          <Plus size={24} />
                        </span>
                        <strong>Follow something new</strong>
                        <p>Your next great find starts here.</p>
                      </button>
                    </div>
                  )}
                </>
              )}
              {view === "templates" && (
                <>
                  <div className="template-intro">
                    <span>
                      <LayoutGrid size={18} />A little inspiration to get you
                      going
                    </span>
                    <p>
                      Real RSS sources and thoughtful keywords. Edit anything
                      before you start.
                    </p>
                  </div>
                  <div className="template-grid">
                    {templates.map((t) => (
                      <article className="template-card" key={t.id}>
                        <div className="template-card-top">
                          <span
                            className="large-radar"
                            style={{
                              background: `${t.color}12`,
                              color: t.color,
                            }}
                          >
                            <Radio size={23} />
                          </span>
                          <span className="template-category">
                            {t.category}
                          </span>
                        </div>
                        <h2>{t.name}</h2>
                        <p>{t.description}</p>
                        <div className="monitor-keywords">
                          {t.keywords.slice(0, 4).map((k) => (
                            <span className="keyword-chip" key={k}>
                              {k}
                            </span>
                          ))}
                        </div>
                        <div className="template-bottom">
                          <span>{t.feed_urls.length} curated sources</span>
                          <button
                            className="button"
                            onClick={() => {
                              const { id, ...draft } = t;
                              setEditor(draft);
                            }}
                          >
                            Use template
                            <ArrowRight size={14} />
                          </button>
                        </div>
                      </article>
                    ))}
                  </div>
                  <p className="template-footnote">
                    Built for curious people, by one.{" "}
                    <a
                      href="https://github.com/dorukgezici/subabot/issues/new"
                      target="_blank"
                      rel="noreferrer"
                    >
                      Suggest a template <ArrowUpRight size={13} />
                    </a>
                  </p>
                </>
              )}
            </>
          )}
          <footer className="app-footer">
            <span>
              <span className="color-dot" />
              Stay curious. We’ll keep an eye out.
            </span>
            <a
              href="https://github.com/dorukgezici/subabot"
              target="_blank"
              rel="noreferrer"
            >
              Open source, always
              <ArrowUpRight size={12} />
            </a>
          </footer>
        </main>
      </div>
      {editor && (
        <MonitorForm
          initial={editor}
          onSave={saveMonitor}
          onClose={() => setEditor(null)}
        />
      )}
      {settings && (
        <SettingsModal
          demo={demo}
          workspace={workspace}
          onClose={() => setSettings(false)}
          onChanged={async () => {
            if (!demo) {
              await reload();
              setLoadError("");
            }
          }}
          onToast={setToast}
        />
      )}
      {sharing && (
        <Modal
          title="Good signals are worth sharing."
          onClose={() => setSharing(null)}
        >
          <div className="form-stack">
            <div className="share-preview">
              <span
                className="large-radar"
                style={{
                  color: sharing.color,
                  background: `${sharing.color}12`,
                }}
              >
                <Radio size={25} />
              </span>
              <h3>{sharing.name}</h3>
              <p>{sharing.description || sharing.keywords.join(", ")}</p>
              <small>Curated with Subabot · Built by Doruk Gezici</small>
            </div>
            <p className="form-intro">
              Publishing makes this monitor’s name, keywords, source URLs, and
              matching stories public. Your workspace key and Slack connection
              stay private. Anyone with the link can use the settings to make
              their own monitor.
            </p>
            {sharing.public && sharing.share_slug ? (
              <>
                <label>
                  Public watchlist link
                  <input
                    readOnly
                    value={`${location.origin}/s/${sharing.share_slug}`}
                  />
                </label>
                <div className="button-row">
                  <button
                    className="button primary"
                    onClick={() =>
                      void act(async () => {
                        await navigator.clipboard.writeText(
                          `${location.origin}/s/${sharing.share_slug}`,
                        );
                        setToast("Watchlist link copied.");
                      })
                    }
                  >
                    <Copy size={15} />
                    Copy link
                  </button>
                  <a
                    className="button"
                    href={`/s/${sharing.share_slug}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open watchlist
                    <ExternalLink size={15} />
                  </a>
                  <button
                    className="button danger"
                    disabled={busy}
                    onClick={() =>
                      void act(async () => {
                        setSharing(
                          await updateMonitor(sharing, { public: false }),
                        );
                        setToast("Watchlist is private again.");
                      })
                    }
                  >
                    Unpublish
                  </button>
                </div>
              </>
            ) : (
              <button
                className="button primary"
                disabled={busy}
                onClick={() =>
                  void act(async () => {
                    if (demo) {
                      setToast(
                        "Create your own workspace to publish a real watchlist.",
                      );
                      return;
                    }
                    setSharing(await updateMonitor(sharing, { public: true }));
                    setToast("Your public watchlist is ready to share.");
                  })
                }
              >
                <Globe2 size={16} />
                Publish watchlist
              </button>
            )}
          </div>
        </Modal>
      )}
      {toast && (
        <div role="status" className="toast">
          <span>{toast}</span>
          <button
            className="icon-button"
            onClick={() => setToast("")}
            aria-label="Dismiss notification"
          >
            <X size={15} />
          </button>
        </div>
      )}
    </div>
  );
}

function SettingsModal({
  demo,
  workspace,
  onClose,
  onChanged,
  onToast,
}: {
  demo: boolean;
  workspace: WorkspaceResponse;
  onClose: () => void;
  onChanged: () => Promise<void>;
  onToast: (s: string) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [recovery, setRecovery] = useState(false);
  async function action(fn: () => Promise<void>) {
    if (demo) {
      onToast("You’re in the demo. Create a workspace to save your settings.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function submitName(e: SyntheticEvent<HTMLFormElement>) {
    e.preventDefault();
    const name = String(new FormData(e.currentTarget).get("name"));
    void action(async () => {
      await api("/workspace", json("PATCH", { name }));
      await onChanged();
      onToast("Workspace name saved.");
    });
  }
  function submitSlack(e: SyntheticEvent<HTMLFormElement>) {
    e.preventDefault();
    const webhook_url = String(new FormData(e.currentTarget).get("webhook"));
    const form = e.currentTarget;
    void action(async () => {
      await api("/integrations/slack", json("POST", { webhook_url }));
      form.reset();
      await onChanged();
      onToast("Slack connected. New signals will arrive in your channel.");
    });
  }
  return (
    <Modal title="Make yourself at home." onClose={onClose}>
      <div className="form-stack settings-stack">
        <form onSubmit={submitName}>
          <label>
            Workspace name
            <div className="input-action">
              <input
                name="name"
                defaultValue={workspace.workspace.name}
                maxLength={80}
                minLength={1}
                required
              />
              <button className="button" disabled={busy}>
                Save
              </button>
            </div>
          </label>
        </form>
        <section className="settings-section">
          <div className="settings-section-title">
            <span className="slack-mark">✳</span>
            <h3>Your signals, in Slack.</h3>
            {workspace.slack.connected && (
              <span className="connected-label">Connected</span>
            )}
          </div>
          <p>
            Connect an incoming webhook to deliver new matches to a channel you
            choose. Only matches discovered while Slack is connected are
            delivered. Previously collected signals are not sent.
          </p>
          {workspace.slack.connected ? (
            <button
              className="button danger"
              disabled={busy}
              onClick={() =>
                void action(async () => {
                  await api("/integrations/slack", json("DELETE"));
                  await onChanged();
                  onToast("Slack disconnected.");
                })
              }
            >
              Disconnect Slack
            </button>
          ) : (
            <form onSubmit={submitSlack}>
              <label>
                Slack webhook URL
                <input
                  name="webhook"
                  type="password"
                  placeholder="https://hooks.slack.com/services/..."
                  autoComplete="off"
                  required
                />
              </label>
              <div className="slack-setup-links">
                <a
                  href="https://api.slack.com/messaging/webhooks"
                  target="_blank"
                  rel="noreferrer"
                >
                  How to get a webhook <ExternalLink size={12} />
                </a>
                <button className="button primary" disabled={busy}>
                  Connect Slack
                  <ArrowRight size={14} />
                </button>
              </div>
            </form>
          )}
        </section>
        <section className="settings-section">
          <h3>
            <ShieldCheck size={17} />
            Keep your workspace safe.
          </h3>
          <p>
            This browser remembers your workspace. Save your private recovery
            key to access it on another device. Anyone with the key can access
            and delete your data.
          </p>
          <div className="button-row">
            <button
              className="button"
              onClick={() => {
                if (demo) {
                  onToast("The sample workspace has no recovery key.");
                  return;
                }
                const blob = new Blob(
                  [
                    JSON.stringify(
                      { app: "subabot", version: 1, token: token() },
                      null,
                      2,
                    ),
                  ],
                  { type: "application/json" },
                );
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = "subabot-private-recovery.json";
                a.click();
                URL.revokeObjectURL(url);
                onToast("Recovery key downloaded. Keep it somewhere private.");
              }}
            >
              <ArrowDownToLine size={15} />
              Save recovery key
            </button>
            <button
              className="button ghost"
              onClick={() => setRecovery(!recovery)}
            >
              Restore a workspace
            </button>
          </div>
          {recovery && (
            <form
              className="restore-form"
              onSubmit={(e) => {
                e.preventDefault();
                const value = String(
                  new FormData(e.currentTarget).get("key"),
                ).trim();
                void action(async () => {
                  let key = value;
                  try {
                    key = JSON.parse(value).token || value;
                  } catch {}
                  const response = await fetch("/api/workspace", {
                    headers: { Authorization: `Bearer ${key}` },
                  });
                  if (!response.ok)
                    throw new Error(
                      "That recovery key could not be verified. Your current workspace is unchanged.",
                    );
                  localStorage.setItem(TOKEN_KEY, key);
                  location.href = "/dashboard";
                });
              }}
            >
              <label>
                Private recovery key
                <span className="field-help">
                  Paste the key or the contents of your recovery file.
                </span>
                <textarea name="key" rows={3} required autoComplete="off" />
              </label>
              <button className="button" disabled={busy}>
                Restore workspace
              </button>
            </form>
          )}
        </section>
        <details className="advanced danger-zone">
          <summary>
            Delete workspace
            <ChevronDown size={14} />
          </summary>
          <p>
            Delete all monitors, collected signals, and the Slack connection.
            This cannot be undone.
          </p>
          <button
            className="button danger"
            disabled={busy}
            onClick={() => {
              if (
                !confirm("Permanently delete this workspace and all its data?")
              )
                return;
              void action(async () => {
                await api("/workspace", json("DELETE"));
                localStorage.removeItem(TOKEN_KEY);
                location.href = "/dashboard";
              });
            }}
          >
            Delete my workspace
          </button>
        </details>
        {error && (
          <p className="inline-error" role="alert">
            {error}
          </p>
        )}
        <div className="settings-footer">
          <a href="/privacy">Privacy</a>
          <a href="/terms">Terms</a>
          <a
            href="https://github.com/dorukgezici/subabot"
            target="_blank"
            rel="noreferrer"
          >
            Source code
            <ArrowUpRight size={12} />
          </a>
        </div>
      </div>
    </Modal>
  );
}
