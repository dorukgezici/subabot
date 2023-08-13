<script>
	import { env } from '$env/dynamic/public';
	import { Footer } from '$lib';
	import { config } from '@fortawesome/fontawesome-svg-core';
	import '@fortawesome/fontawesome-svg-core/styles.css';
	import dayjs from 'dayjs';
	import relativeTime from 'dayjs/plugin/relativeTime';
	import '../app.css';

	config.autoAddCss = false;
	dayjs.extend(relativeTime);
</script>

<svelte:head>
	<meta name="slack-app-id" content={env.PUBLIC_SLACK_APP_ID} />
</svelte:head>

<slot />
<Footer />
