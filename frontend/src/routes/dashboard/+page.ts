import { getFeeds, getKeywords } from '$lib/api';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
	const [feeds, keywords] = await Promise.all([getFeeds(fetch), getKeywords(fetch)]);
	return { feeds, keywords };
};
