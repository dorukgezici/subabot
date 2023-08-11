import { env } from '$env/dynamic/public';
type Fetch = typeof fetch;

export async function getFeeds(fetch: Fetch): Promise<Feed[]> {
	const res = await fetch(`${env.PUBLIC_BACKEND_URL}/feeds`, { cache: 'no-store' });
	if (!res.ok) return [];
	return await res.json();
}

export async function getKeywords(fetch: Fetch): Promise<Keyword[]> {
	const res = await fetch(`${env.PUBLIC_BACKEND_URL}/keywords`, { cache: 'no-store' });
	if (!res.ok) return [];
	return await res.json();
}
