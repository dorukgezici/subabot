import colors from 'tailwindcss/colors';

/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	daisyui: {
		themes: [
			{
				subabot: {
					primary: '#203a43ff',
					secondary: '#2c5364ff',
					accent: '#b0c4deff',
					neutral: '#0f2027ff',
					'base-100': colors.slate[300],
					info: '#3abff8',
					success: '#36d399',
					warning: '#fbbd23',
					error: '#f87272'
				}
			}
		]
	},
	plugins: [require('@tailwindcss/typography'), require('daisyui')]
};
