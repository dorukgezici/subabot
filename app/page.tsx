import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faMagnifyingGlass } from '@fortawesome/free-solid-svg-icons';
import RobotTile from '@/components/RobotTile';
import SlackButton from '@/components/SlackButton';


export default async function Home() {
  return (
    <main>
      <section
        className='h-screen flex flex-wrap items-center justify-center overflow-hidden space-y-12 bg-gradient-to-tl from-dark via-primary to-light'
      >
        <RobotTile />

        <div
          className='bg-primary opacity-95 absolute p-8 sm:p-16 md:p-24 shadow-2xl rounded-3xl w-full lg:w-2/3 max-w-[900px] border-solid border-2 border-primary'
        >
          <div className='my-10'>
            <h1 className='text-7xl font-extrabold text-slate-300 sm:text-8xl md:text-9xl'>Subabot</h1>
            <p className='text-xl text-slate-400 sm:text-2xl md:text-3xl my-4 md:my-6'>
              An AI-powered Slack alert bot to <span className='underline'>subscribe</span>, <span
              className='underline'>classify</span> and <span className='underline'>notify</span> for keywords on the
              web.
            </p>
          </div>

          <SlackButton
            text='Add to Slack'
            url={`https://slack.com/oauth/v2/authorize?scope=chat:write,chat:write.public,links:read,links:write,commands,team:read&client_id=${process.env.NEXT_PUBLIC_SLACK_CLIENT_ID}`}
          />
        </div>
      </section>

      <section className='flex items-center justify-center p-8 sm:p-16'>
        <div className='w-2/3 max-w-4xl'>
          <h1 className='text-5xl sm:text-6xl md:text-7xl font-extrabold my-10 mr-4'>Never Miss an Update!</h1>
          <p className='text-xl'>
            Subabot is the ultimate AI-powered Slack bot designed to monitor the web and alert you whenever there’s an
            update about your favorite keywords. Stay ahead of the competition and never miss a beat, while cutting
            through the noise with AI classification and filtering.
          </p>
        </div>
        <div className='w-1/3 hidden md:flex max-w-sm'>
          <FontAwesomeIcon icon={faMagnifyingGlass} className='w-full md:h-[324px] lg:h-[384px]' />
        </div>
      </section>

      <section className=''>
        {/* pricing */}
      </section>
    </main>
  );
}
