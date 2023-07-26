'use client';
import { faRobot } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import classNames from 'classnames';
import { useEffect, useState } from 'react';


export default function RobotTile() {
  const [botCount, setBotCount] = useState(0);
  const [botIndex, setBotIndex] = useState(0);
  const bonusBotCount = 4;

  const handleResize = () => {
    // bot width 242.66, height 218.76
    const x = window.innerHeight / 242.66;
    const y = window.innerWidth / 218.76;
    // estimation missing 5 bots for the worst case
    const estimate = Math.floor(x * y);
    setBotCount(estimate + bonusBotCount);
  };

  const pickRandom = (index: number) => {
    if (index !== botIndex) return;
    let newIndex = Math.floor(Math.max(Math.min(Math.random() * botCount - bonusBotCount, botCount * 2 / 3), 0));
    if (newIndex === botIndex) pickRandom(index);
    else setBotIndex(newIndex);
  };

  useEffect(() => {
    handleResize();
    window.addEventListener('resize', handleResize);

    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const icons = Array.from({ length: botCount }).map((_, index) => (
    <FontAwesomeIcon
      key={index} icon={faRobot}
      className={classNames(
        'text-[10rem] text-lighter opacity-75 m-4',
        index % 2 === 0 ? 'rotate-[-20deg]' : 'rotate-[20deg]',
        index === botIndex && 'fa-bounce z-10'
      )}
      onClick={() => pickRandom(index)}
    />
  ));

  return <>{icons}</>;
}
