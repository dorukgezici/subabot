import { env } from '$env/dynamic/public';

/** @type {import('./$types').PageLoad} */
export async function load({ fetch }) {
	return {
		feeds: await getFeeds(fetch),
		keywords: await getKeywords(fetch)
	};
}

type Fetch = typeof fetch;

async function getFeeds(fetch: Fetch): Promise<Feed[]> {
	const res = await fetch(`${env.PUBLIC_BACKEND_URL}/feeds`, {
		cache: 'no-store'
	});
	if (!res.ok) return [];
	return await res.json();
}

async function getKeywords(fetch: Fetch): Promise<Keyword[]> {
	const res = await fetch(`${env.PUBLIC_BACKEND_URL}/keywords`, {
		cache: 'no-store'
	});
	if (!res.ok) return [];
	return await res.json();
}
