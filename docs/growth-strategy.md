# Subabot growth strategy

## The product is the distribution

Subabot's narrow wedge is **a useful monitor someone else can reuse**. The acquisition unit is a monitor with specific sources, keywords, and matched stories, not a generic announcement that another monitoring app exists. Virality is an outcome to measure, not a property to promise.

The first audience is independent builders who follow technical releases, product changes, and conversations about their niche. They already share RSS sources and tool setups. A small, useful template is easier to recommend than a new daily destination.

## Product loops in this rebuild

1. A visitor lands on a focused public template in `/explore`.
2. The visitor can inspect its source URLs and keywords before using it.
3. The template opens a prefilled monitor setup. Saving is an explicit user action.
4. The monitor collects useful results. A user can voluntarily publish a monitor configuration as a reusable share link.
5. The recipient can inspect and reuse that configuration. Creator attribution connects the utility back to Subabot and Doruk.

The landing page links to the template library, shows keyword filtering with labeled sample data, offers a sample workspace without an account barrier, and places a direct creator link in the footer and open-source section. Public pages provide metadata and a branded share image.

The implementation status of individual app features should be verified against the current dashboard and API. This strategy is not evidence that an unimplemented analytics or sharing feature exists.

## Rules that protect trust

- Sharing is opt-in. Do not automatically publish feed URLs, keywords, results, or user activity. Never publish Slack webhooks or workspace credentials.
- A shared monitor exposes its name, description, feed URLs, keyword rules, and matched stories. Make these fields clear before publication.
- Show the original source for every signal. Avoid replacing publisher content with unattributed summaries.
- No fabricated user counts, testimonials, star counts, or urgency.
- No forced posting, unsolicited messages, scraped mailing lists, auto-enrollment, or contact imports.
- No claim of guaranteed growth, exhaustive coverage, or instant alerts.
- The product should remain useful when the user never shares anything.

## Initial launch, prepared for manual execution

### 1. Publish useful recipes

Begin with a few high-quality templates tied to actual public feeds: engineering news, developer tools, and design discoveries. Test every source. Give each template a clear outcome and explain why its keywords were selected. Add new recipes only when the sources and matches justify them.

### 2. Tell the rebuild story

Publish a short creator-led post: the old project, the narrow problem retained, what changed, and an honest recording of one monitor finding a match. Link to a relevant template instead of sending every reader to the homepage. A screenshot should show the product and real source attribution, not invented performance metrics.

Suggested post draft:

> I rebuilt an old project because the problem never went away: useful updates get buried. Subabot watches RSS feeds for the words you care about and sends the matches to an inbox or Slack. It is open source, and I put together a few starter monitors you can adapt. Here is the one I use for [specific topic]: [verified template URL].

Nothing is posted automatically by this implementation.

### 3. Contribute where the recipe helps

Manually share a relevant template in a community only when its rules permit it and the post answers a real monitoring problem. Lead with the working recipe and its limitations. Disclose that you built the tool. Prioritize detailed feedback over broad reach.

### 4. Turn feedback into public improvements

Keep a concise changelog in the repository. Credit contributions only with the contributor's permission. Invite source and template suggestions through GitHub issues. Use recurring user problems to choose the next template and product improvement.

## What to measure next

No third-party analytics should be silently added. If a measurement service is introduced, document the data, consent needs, and retention first.

Suggested aggregate funnel events: template viewed, setup opened, monitor created, first successful feed check, first match, optional Slack connected, optional share created, shared configuration reused. Never include raw feed URLs, keywords, webhook URLs, workspace keys, or article content in event payloads.

Activation is a successfully checked monitor, with first match tracked separately because some valid monitors intentionally match infrequently. Retention is a useful monitor still running and revisited after seven days. The share loop is measured by the fraction of activated workspaces that voluntarily share and the fraction of recipients that create a monitor.

## Decisions after launch

Review a small number of actual setup sessions and support reports. Fix the largest setup failure before adding new features. If templates attract visits but do not create monitors, improve source quality and the setup handoff. If monitors run but produce noise, improve keyword guidance and exclusion rules. If people return but rarely share, keep serving those users rather than adding coercive referral mechanics.
