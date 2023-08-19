<script lang="ts">
	import { env } from '$env/dynamic/public';
	import { RobotTile, SlackButton } from '$lib';
	import { faMagnifyingGlass } from '@fortawesome/free-solid-svg-icons';
	import dayjs from 'dayjs';
	import Fa from 'svelte-fa';

	export let data: {
		feeds: Feed[];
		keywords: Keyword[];
	};
</script>

<main>
	<section
		class="h-screen flex flex-wrap items-center justify-center overflow-hidden space-y-12 bg-gradient-to-tl from-neutral via-primary to-secondary"
	>
		<RobotTile />

		<div
			class="bg-primary opacity-95 absolute p-8 sm:p-16 md:p-24 shadow-2xl rounded-3xl w-full lg:w-2/3 max-w-[900px] border-solid border-2 border-primary"
		>
			<div class="my-10">
				<h1 class="text-7xl font-extrabold text-slate-300 sm:text-8xl md:text-9xl">Subabot</h1>
				<p class="text-xl text-slate-400 sm:text-2xl md:text-3xl my-4 md:my-6">
					An AI-powered Slack alert bot to{' '}
					<span class="underline">subscribe</span>,{' '}
					<span class="underline">classify</span> and{' '}
					<span class="underline">notify</span> for keywords on RSS feeds.
				</p>
			</div>

			<SlackButton
				text="Add to Slack"
				url={`https://slack.com/oauth/v2/authorize?scope=chat:write,chat:write.public,links:read,links:write,commands,team:read&client_id=${env.PUBLIC_SLACK_CLIENT_ID}&redirect_uri=${env.PUBLIC_BACKEND_URL}/slack/oauth`}
			/>
		</div>
	</section>

	<section class="flex items-center justify-center p-8 sm:p-16">
		<div class="w-3/5 max-w-4xl">
			<h1 class="text-5xl sm:text-6xl md:text-7xl font-extrabold my-10 mr-4">
				Never Miss an Update!
			</h1>
			<p class="text-xl">
				Subabot is the ultimate AI-powered Slack bot designed to monitor the web and alert you
				whenever there’s an update about your favorite keywords. Stay ahead of the competition and
				never miss a beat, while cutting through the noise with AI classification and filtering.
			</p>
		</div>
		<div class="w-2/5 hidden md:flex max-w-sm">
			<Fa icon={faMagnifyingGlass} style="width: %100; height: auto" />
		</div>
	</section>

	<section class="flex flex-wrap justify-center p-8 sm:p-16 gap-8">
		<div class="flex flex-col">
			<h2 class="text-xl font-bold">Sources</h2>
			<ul class="list-disc">
				{#each data.feeds as feed (feed.key)}
					<li>
						<a href={feed.key} target="_blank" class="link">
							{feed.title}
						</a>
						<p>
							{feed.refreshed_at ? dayjs.unix(feed.refreshed_at).fromNow() : 'never'}
						</p>
					</li>
				{/each}
			</ul>
		</div>

		<div class="flex flex-col">
			<h2 class="text-xl font-bold">Keywords</h2>
			<ul class="list-disc">
				{#each data.keywords as keyword (keyword.key)}
					<li>
						<h3>{keyword.value}</h3>
						<p>
							{keyword.checked_at ? dayjs.unix(keyword.checked_at).fromNow() : 'never'}
						</p>
					</li>
				{/each}
			</ul>
		</div>
	</section>

	<section class="flex items-center justify-center p-8 sm:p-16">
		<!-- pricing -->
	</section>
</main>
