<script>
	import { Footer } from '$lib';
	import { config } from '@fortawesome/fontawesome-svg-core';
	import '@fortawesome/fontawesome-svg-core/styles.css';
	import dayjs from 'dayjs';
	import relativeTime from 'dayjs/plugin/relativeTime';
	import '../app.css';

	config.autoAddCss = false;
	dayjs.extend(relativeTime);
</script>

<slot />
<Footer />
