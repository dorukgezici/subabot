import type { Monitor, Signal, Template } from "./api";
export const demoTemplates: Template[] = [
  {
    id: "ai-radar",
    name: "AI radar",
    description: "Model releases, useful tools, and ideas worth knowing.",
    keywords: ["AI", "LLM", "model", "OpenAI"],
    feed_urls: [
      "https://hnrss.org/frontpage",
      "https://techcrunch.com/category/artificial-intelligence/feed/",
    ],
    color: "#357a57",
    category: "Technology",
  },
  {
    id: "indie-founders",
    name: "Indie founders",
    description: "Small teams, new launches, and the craft of building.",
    keywords: ["startup", "founder", "launch", "Show HN"],
    feed_urls: ["https://hnrss.org/frontpage"],
    color: "#aa7950",
    category: "Startups",
  },
  {
    id: "design-engineering",
    name: "Design engineering",
    description: "Where thoughtful interfaces meet great code.",
    keywords: ["design", "CSS", "React", "Astro"],
    feed_urls: [
      "https://hnrss.org/frontpage",
      "https://www.smashingmagazine.com/feed/",
    ],
    color: "#7577ac",
    category: "Design",
  },
];
export function demoMonitors(): Monitor[] {
  return demoTemplates.map((t, i) => ({
    ...t,
    id: `demo-${i}`,
    exclude_keywords: [],
    match_mode: "any",
    enabled: true,
    public: false,
    share_slug: null,
    created_at: new Date().toISOString(),
    last_checked_at: new Date().toISOString(),
  }));
}
export function demoSignals(): Signal[] {
  const stories = [
    [
      "A smaller model. A bigger world of possibilities.",
      "A new generation of efficient language models is making it easier to build useful, personal tools without a server rack.",
      "The AI notebook",
      0,
      ["model", "AI"],
      "https://huggingface.co/blog",
    ],
    [
      "Show HN: I built the tool I kept wishing existed",
      "A solo founder shares the process behind a tiny product, from a weekend experiment to the first real customers.",
      "Hacker News",
      1,
      ["Show HN", "founder"],
      "https://news.ycombinator.com/show",
    ],
    [
      "The small details that make an interface feel right",
      "On quieter motion, generous spacing, and designing interactions that stay out of the way.",
      "Design notes",
      2,
      ["design", "CSS"],
      "https://www.smashingmagazine.com/",
    ],
    [
      "What happens when AI tools become genuinely useful?",
      "Less spectacle, more everyday value. A closer look at practical workflows emerging around open language models.",
      "The AI notebook",
      0,
      ["AI", "LLM"],
      "https://huggingface.co/blog",
    ],
    [
      "Building for the first ten people, not the next million",
      "Why listening to a handful of early customers can be the most effective startup strategy.",
      "The founder journal",
      1,
      ["startup", "founder"],
      "https://news.ycombinator.com/",
    ],
    [
      "A fresh perspective on building with Astro and React",
      "Fast pages, small islands of interactivity, and a simpler way to think about the frontend.",
      "Frontend dispatch",
      2,
      ["Astro", "React"],
      "https://astro.build/blog/",
    ],
  ];
  return stories.map((s, i) => ({
    id: `sample-${i}`,
    monitor_id: `demo-${s[3]}`,
    title: s[0] as string,
    summary: s[1] as string,
    source: s[2] as string,
    published_at: new Date(Date.now() - (i + 1) * 3600000).toISOString(),
    matched_keywords: s[4] as string[],
    url: s[5] as string,
    is_read: i > 3,
    is_bookmarked: i === 2,
  }));
}
