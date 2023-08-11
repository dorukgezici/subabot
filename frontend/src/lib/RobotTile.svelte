<script lang="ts">
	import { faRobot } from '@fortawesome/free-solid-svg-icons';
	import classNames from 'classnames';
	import { onMount } from 'svelte';
	import Fa from 'svelte-fa';

	let botCount = 0;
	let botIndex = 0;
	const bonusBotCount = 4;

	const handleResize = () => {
		// bot width 242.66, height 218.76
		const x = window.innerHeight / 242.66;
		const y = window.innerWidth / 218.76;
		// estimation missing 5 bots for the worst case
		const estimate = Math.floor(x * y);
		botCount = estimate + bonusBotCount;
	};

	const pickRandom = (index: number) => {
		if (index !== botIndex) return;
		let newIndex = Math.floor(
			Math.max(Math.min(Math.random() * botCount - bonusBotCount, (botCount * 2) / 3), 0)
		);
		if (newIndex === botIndex) pickRandom(index);
		else botIndex = newIndex;
	};

	onMount(() => {
		handleResize();
		window.addEventListener('resize', handleResize);

		return () => window.removeEventListener('resize', handleResize);
	});
</script>

{#each Array.from({ length: botCount }) as _, index (index)}
	<Fa
		icon={faRobot}
		class={classNames(
			'text-[10rem] text-accent opacity-75 m-4',
			index % 2 === 0 ? 'rotate-[-20deg]' : 'rotate-[20deg]',
			index === botIndex && 'fa-bounce z-10'
		)}
		on:click={() => pickRandom(index)}
	/>
{/each}
