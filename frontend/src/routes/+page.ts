import { getFeeds, getKeywords } from '$lib/api';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
	return {
		feeds: await getFeeds(fetch),
		keywords: await getKeywords(fetch)
	};
};
