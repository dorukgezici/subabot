import classNames from 'classnames';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faMagnifyingGlass, faRobot } from '@fortawesome/free-solid-svg-icons';
import SlackButton from '@/components/SlackButton';
import styles from './styles.module.scss';


export default async function Index() {
  const emojis = Array.from({ length: 100 }).map((_, index) => (
    <FontAwesomeIcon key={index} icon={faRobot} className={styles.icon} />
  ));

  return (
    <main>
      <section className={classNames(styles.bg,
        'h-screen flex flex-wrap items-center justify-center overflow-hidden space-y-12'
      )}>
        {emojis}

        <div className={classNames(styles.card,
          'absolute p-20 shadow-2xl rounded-xl'
        )}>
          <div className='w-full my-10 md:w-1/2'>
            <h1 className='text-8xl font-extrabold text-slate-300 md:text-9xl'>Subabot</h1>
            <p className='text-lg text-slate-400 md:text-xl my-4'>
              An AI-powered Slack alert bot to subscribe, classify and notify for keywords on the web.
            </p>
          </div>

          <SlackButton
            text='Add to Slack'
            url={`https://slack.com/oauth/v2/authorize?scope=chat:write,chat:write.public,links:read,links:write,commands,team:read&client_id=${process.env.NEXT_PUBLIC_SLACK_CLIENT_ID}`}
          />
        </div>
      </section>

      <section className='flex justify-center align-middle items-center p-20'>
        <div className='flex-row w-2/3'>
          <h1 className='text-7xl font-extrabold my-10 mr-4'>Never Miss an Update!</h1>
          <p>
            Subabot is the ultimate AI-powered Slack bot designed to monitor the web and alert you whenever there’s an
            update about your favorite keywords. Stay ahead of the competition and never miss a beat, while cutting
            through the noise with AI classification and filtering.
          </p>
        </div>
        <div className='flex w-1/3'>
          <FontAwesomeIcon icon={faMagnifyingGlass} className='hidden md:block w-12 md:w-1/2 lg:1/3 xl:1/4 h-auto' />
        </div>
      </section>
    </main>
  );
}
