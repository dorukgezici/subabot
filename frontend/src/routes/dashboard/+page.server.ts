import { createFeed, createKeyword, deleteFeed, deleteKeyword } from '$lib/api';
import { fail } from '@sveltejs/kit';
import type { Actions } from './$types';

export const actions: Actions = {
	addFeed: async ({ request, fetch }) => {
		const data = await request.formData();
		const url = data.get('feed') as string;

		if (!url || url.length < 11 || !url.startsWith('https://')) {
			return fail(400, { feed: url, error: 'Feed must be a valid https URL.' });
		}

		await createFeed(fetch, url);
		return { success: true };
	},
	removeFeed: async ({ request, fetch }) => {
		const data = await request.formData();
		const key = data.get('key') as string;

		await deleteFeed(fetch, key);
		return { success: true };
	},
	addKeyword: async ({ request, fetch }) => {
		const data = await request.formData();
		const value = data.get('keyword') as string;

		if (!value || value.length < 3 || value.length > 30) {
			return fail(400, { keyword: value, error: 'Keyword must be between 3 and 30 characters.' });
		}

		await createKeyword(fetch, value);
		return { success: true };
	},
	removeKeyword: async ({ request, fetch }) => {
		const data = await request.formData();
		const key = data.get('key') as string;

		await deleteKeyword(fetch, key);
		return { success: true };
	}
};
