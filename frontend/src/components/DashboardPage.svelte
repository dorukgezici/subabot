<script lang="ts">
    import { actions, getActionProps } from "astro:actions";
    import { Alert, Header, RemoveButton } from "@/components";
    import { importFeeds, triggerCrawl } from "@/lib/api";
    import type { Feed, Keyword } from "@/types/rss";
    import dayjs from "@/lib/dayjs";

    export let data: {
        feeds: Feed[];
        keywords: Keyword[];
    };
    export let form: {
        feed?: string;
        keyword?: string;
        error?: string;
    };
</script>

<main class="min-h-screen">
    <Header />

    <section class="flex flex-wrap justify-center p-8 sm:p-16 gap-8">
        <button class="btn" on:click={async () => await triggerCrawl()}>
            Trigger Crawl
        </button>
        <button
            class="btn"
            on:click={async () => (data.feeds = await importFeeds())}
        >
            Import Feeds
        </button>
    </section>

    <section class="flex flex-wrap justify-center p-8 sm:p-16 gap-8">
        <div class="flex flex-col prose">
            <h2>Sources <span class="badge">{data.feeds.length}</span></h2>
            <ul>
                {#each data.feeds as feed (feed.key)}
                    <li>
                        <a href={feed.key} target="_blank">{feed.title}</a>
                        <form
                            method="POST"
                            class="inline"
                            on:submit={async (e) => {
                                e.preventDefault();
                                const formData = new FormData(e.target);
                                await actions.removeFeed(formData);
                                window.location.reload();
                            }}
                        >
                            <input {...getActionProps(actions.removeFeed)} />
                            <input type="hidden" name="key" value={feed.key} />
                            <button type="submit" class="btn btn-xs">x</button>
                        </form>
                        <small class="block">
                            {feed.refreshed_at
                                ? dayjs.unix(feed.refreshed_at).fromNow()
                                : "never"}
                        </small>
                    </li>
                {:else}
                    <li><i>No feeds are added.</i></li>
                {/each}
            </ul>
            <form
                method="POST"
                on:submit={async (e) => {
                    e.preventDefault();
                    const formData = new FormData(e.target);
                    await actions.addFeed(formData);
                    window.location.reload();
                }}
            >
                <input {...getActionProps(actions.addFeed)} />
                <input
                    name="feed"
                    type="url"
                    value={form?.feed ?? ""}
                    placeholder="Add new feed"
                    class="input w-full max-w-xs my-2"
                />

                {#if form?.feed && form?.error}
                    <Alert error={form.error} />
                {/if}
            </form>
        </div>

        <div class="flex flex-col prose">
            <h2>Keywords <span class="badge">{data.keywords.length}</span></h2>
            <ul>
                {#each data.keywords as keyword (keyword.key)}
                    <li>
                        <span>{keyword.value}</span>
                        <form
                            method="POST"
                            class="inline ml-2"
                            on:submit={async (e) => {
                                e.preventDefault();
                                const formData = new FormData(e.target);
                                await actions.removeKeyword(formData);
                                window.location.reload();
                            }}
                        >
                            <input {...getActionProps(actions.removeKeyword)} />
                            <input
                                type="hidden"
                                name="key"
                                value={keyword.key}
                            />
                            <RemoveButton />
                        </form>
                        <small class="block">
                            {keyword.checked_at
                                ? dayjs.unix(keyword.checked_at).fromNow()
                                : "never"}
                        </small>
                    </li>
                {:else}
                    <li><i>No keywords are added.</i></li>
                {/each}
            </ul>
            <form
                method="POST"
                on:submit={async (e) => {
                    e.preventDefault();
                    const formData = new FormData(e.target);
                    await actions.addKeyword(formData);
                    window.location.reload();
                }}
            >
                <input {...getActionProps(actions.addKeyword)} />
                <input
                    name="keyword"
                    type="text"
                    value={form?.keyword ?? ""}
                    placeholder="Add new keyword"
                    class="input w-full max-w-xs my-2"
                />

                {#if form?.keyword && form?.error}
                    <Alert error={form.error} />
                {/if}
            </form>
        </div>
    </section>
</main>
