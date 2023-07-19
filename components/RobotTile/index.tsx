'use client';
import { useState } from 'react';
import classNames from 'classnames';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faRobot } from '@fortawesome/free-solid-svg-icons';


export default function RobotTile({ count }: { count: number }) {
  const [botIndex, setBotIndex] = useState(0);
  // 242.66 bot width

  const icons = Array.from({ length: count }).map((_, index) => (
    <FontAwesomeIcon
      key={index} icon={faRobot}
      className={classNames(
        'text-[10rem] text-lighter opacity-75 m-4',
        index % 2 === 0 ? 'rotate-[-20deg]' : 'rotate-[20deg]',
        index === botIndex && 'fa-bounce z-10'
      )}
      onClick={() => {
        if (index !== botIndex) return;
        setBotIndex(Math.floor(Math.random() * count));
      }}
    />
  ));

  return <>{icons}</>;
}
