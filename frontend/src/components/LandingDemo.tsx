import { useEffect, useState } from "react";
import {
  ArrowDown,
  ArrowUpRight,
  Bell,
  Check,
  ChevronDown,
  Hash,
  Inbox,
  ListFilter,
  Plus,
  Radio,
  Search,
} from "lucide-react";

const topics = ["AI", "open source", "design"] as const;
type Topic = (typeof topics)[number];
const examples: Record<
  Topic,
  {
    title: string;
    snippet: string;
    source: string;
    letter: string;
    color: string;
    tag: string;
  }[]
> = {
  AI: [
    {
      title: "Small teams, big ideas: building with AI",
      snippet:
        "A practical look at the tools changing how independent makers work.",
      source: "The builder’s journal",
      letter: "b",
      color: "blue",
      tag: "AI",
    },
    {
      title: "A more open future for AI",
      snippet:
        "Meet the open source projects making machine learning more accessible.",
      source: "Engineering notes",
      letter: "e",
      color: "orange",
      tag: "AI",
    },
    {
      title: "Designing useful AI experiences",
      snippet:
        "What happens when a new capability starts with a real human problem?",
      source: "Design dispatch",
      letter: "d",
      color: "purple",
      tag: "AI",
    },
  ],
  "open source": [
    {
      title: "A more open future for AI",
      snippet:
        "Meet the open source projects making machine learning more accessible.",
      source: "Engineering notes",
      letter: "e",
      color: "orange",
      tag: "open source",
    },
    {
      title: "The small tools that make the web better",
      snippet:
        "An open source reading list for people who like to build in public.",
      source: "The builder’s journal",
      letter: "b",
      color: "blue",
      tag: "open source",
    },
    {
      title: "A community-built alternative to another subscription",
      snippet:
        "An open source project finds its audience by solving one problem well.",
      source: "Product stories",
      letter: "p",
      color: "pink",
      tag: "open source",
    },
  ],
  design: [
    {
      title: "Designing useful AI experiences",
      snippet:
        "What happens when a new capability starts with a real human problem?",
      source: "Design dispatch",
      letter: "d",
      color: "purple",
      tag: "design",
    },
    {
      title: "Less interface. More intention.",
      snippet:
        "A field guide to the design decisions that help people find their focus.",
      source: "Design dispatch",
      letter: "d",
      color: "purple",
      tag: "design",
    },
    {
      title: "The craft behind a calmer inbox",
      snippet: "Inside a design process that starts by taking things away.",
      source: "Product stories",
      letter: "p",
      color: "pink",
      tag: "design",
    },
  ],
};

function Bot({ small = false }: { small?: boolean }) {
  return (
    <span
      className={`landing-demo-bot${small ? " is-small" : ""}`}
      aria-hidden="true"
    >
      <i />
      <i />
    </span>
  );
}

export default function LandingDemo() {
  const [topic, setTopic] = useState<Topic>("AI");
  const [stage, setStage] = useState(0);
  const [interacted, setInteracted] = useState(false);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setStage(2);
      return;
    }
    const timer = window.setInterval(
      () => setStage((current) => Math.min(current + 1, 2)),
      1600,
    );
    const finish = window.setTimeout(() => window.clearInterval(timer), 3500);
    return () => {
      window.clearInterval(timer);
      window.clearTimeout(finish);
    };
  }, []);

  function chooseTopic(value: Topic) {
    setTopic(value);
    setStage(2);
    setInteracted(true);
  }

  return (
    <div className={`landing-demo stage-${stage}`}>
      <div className="landing-demo-toolbar">
        <div className="landing-demo-window-dots" aria-hidden="true">
          <i />
          <i />
          <i />
        </div>
        <span>
          <span className="landing-demo-toolbar-dot" /> Your corner of the
          internet
        </span>
        <span className="landing-demo-sample">Sample data</span>
      </div>
      <div className="landing-demo-body">
        <aside className="landing-demo-sidebar" aria-label="Sample workspace">
          <div className="landing-demo-workspace">
            <Bot small />
            <strong>Your workspace</strong>
            <ChevronDown size={13} />
          </div>
          <div className="landing-demo-sidebar-items" aria-hidden="true">
            <div className="is-selected">
              <Inbox size={17} />
              <span>Signal inbox</span>
              <b>3</b>
            </div>
            <div>
              <Radio size={17} />
              <span>Monitors</span>
              <span className="landing-demo-sidebar-count">3</span>
            </div>
          </div>
          <span className="landing-demo-side-label">
            YOUR SOURCES <Plus size={13} aria-hidden="true" />
          </span>
          <div className="landing-demo-source">
            <span className="landing-source-icon blue">b</span>The builder’s
            journal
          </div>
          <div className="landing-demo-source">
            <span className="landing-source-icon orange">e</span>Engineering
            notes
          </div>
          <div className="landing-demo-source">
            <span className="landing-source-icon purple">d</span>Design dispatch
          </div>
          <div className="landing-demo-sidebar-bottom">
            <span className="landing-live-dot" />
            Listening for the good stuff
          </div>
        </aside>
        <div className="landing-demo-inbox">
          <div className="landing-demo-inbox-heading">
            <div>
              <span className="landing-demo-breadcrumb">
                Workspace <span>/</span> Inbox
              </span>
              <h2>
                All your signals<span className="landing-count-badge">3</span>
              </h2>
            </div>
            <ListFilter size={17} aria-hidden="true" />
          </div>
          <div className="landing-demo-filter">
            <span className="landing-demo-filter-label">
              <Search size={13} aria-hidden="true" /> Matching
            </span>
            <div
              className="landing-topic-buttons"
              aria-label="Try a sample keyword"
            >
              {topics.map((value) => (
                <button
                  type="button"
                  key={value}
                  aria-pressed={topic === value}
                  onClick={() => chooseTopic(value)}
                >
                  {value}
                </button>
              ))}
            </div>
          </div>
          <div className="landing-demo-list">
            <div className="landing-demo-day">
              LATEST MATCHES <span>3 signals</span>
            </div>
            {examples[topic].map((item, index) => (
              <article className="landing-demo-story" key={item.title}>
                <span className={`landing-source-icon ${item.color}`}>
                  {item.letter}
                </span>
                <div className="landing-demo-story-content">
                  <div className="landing-demo-story-meta">
                    {item.source}
                    <span>{index * 8 + 2}m ago</span>
                  </div>
                  <h3>{item.title}</h3>
                  <p>{item.snippet}</p>
                  <span className="landing-demo-story-tag">
                    <Hash size={11} aria-hidden="true" />
                    {item.tag}
                  </span>
                </div>
                <span className="landing-demo-unread" aria-label="Unread" />
              </article>
            ))}
          </div>
          <div className="landing-demo-caught-up">
            <Check size={13} aria-hidden="true" /> The rest of the noise?
            Filtered out.
          </div>
        </div>
        <aside className="landing-demo-delivery">
          <div className="landing-demo-delivery-label">
            <Bell size={14} aria-hidden="true" /> YOUR SIGNAL, DELIVERED
          </div>
          <div className="landing-demo-rule">
            <div>
              <span className="landing-live-dot" />
              Monitor is listening
            </div>
            <strong>My daily inspiration</strong>
            <p>3 sources · Keyword matches</p>
            <div className="landing-demo-rule-keywords">
              {topics.map((value) => (
                <span
                  className={value === topic ? "is-active" : ""}
                  key={value}
                >
                  {value}
                </span>
              ))}
            </div>
          </div>
          <div className="landing-demo-flow" aria-hidden="true">
            <span />
            <ArrowDown size={17} />
            <span />
          </div>
          <div className="landing-demo-slack">
            <div className="landing-demo-slack-channel">
              <span className="landing-slack-symbol" aria-hidden="true">
                ✳
              </span>{" "}
              <strong># fresh-signals</strong>
              <span>Slack</span>
            </div>
            <div className="landing-demo-slack-message">
              <Bot small />
              <div>
                <div>
                  <strong>subabot</strong>
                  <span className="landing-app-label">APP</span>
                </div>
                <p>A little something for your radar.</p>
                <div className="landing-demo-slack-link">
                  {examples[topic][0].title}
                </div>
                <span className="landing-demo-slack-match">
                  Matched “{topic}”
                </span>
              </div>
            </div>
          </div>
          <span className="landing-demo-delivered">
            <Check size={12} aria-hidden="true" /> Slack preview
          </span>
        </aside>
      </div>
      <div className="landing-demo-caption">
        <span>
          <span className="landing-demo-caption-dot" /> Try a keyword. Watch the
          signal change.
        </span>
        <a href="/dashboard?demo=1">
          Take a closer look <ArrowUpRight size={14} aria-hidden="true" />
        </a>
      </div>
      <p className="sr-only" role="status" aria-live="polite">
        {interacted
          ? `Showing three sample signals matching ${topic}. The Slack preview shows the first match.`
          : ""}
      </p>
    </div>
  );
}
