import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <div className="row">
          <div className="col col--6">
            <Heading as="h1" className="hero__title">
              {siteConfig.title}
            </Heading>
            <p className="hero__subtitle">{siteConfig.tagline}</p>
            <div className={styles.buttons}>
              <Link
                className="button button--primary button--lg"
                to="/docs/guides/quickstart">
                Get Started - 5min
              </Link>
              <Link
                className="button button--outline button--lg"
                to="/docs/intro">
                View Documentation
              </Link>
            </div>
          </div>
          <div className="col col--6">
            <div className={styles.heroImage}>
              <img 
                src="/img/screenshots/specifyx-help.webp" 
                alt="SpecifyX CLI Help Command"
                className={styles.screenshot}
              />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

type FeatureItem = {
  title: string;
  description: ReactNode;
  image?: string;
  imageAlt?: string;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Quick Project Setup',
    image: '/img/screenshots/specifyx-check.webp',
    imageAlt: 'SpecifyX check command output',
    description: (
      <>
        Initialize projects with a single command. Built-in system checks ensure
        your environment is ready for spec-driven development.
      </>
    ),
  },
  {
    title: 'Script running commands',
    image: '/img/screenshots/specifyx-run-list.webp', 
    imageAlt: 'SpecifyX script list',
    description: (
      <>
        Run generated Python scripts with argument passthrough support and more.
      </>
    ),
  },
  {
    title: 'System Information',
    image: '/img/screenshots/specifyx-update-info.webp',
    imageAlt: 'SpecifyX system information',
    description: (
      <>
        Keep track of your development environment with detailed system information
        and update notifications built right into the CLI.
      </>
    ),
  },
];

function Feature({title, description, image, imageAlt}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="card shadow--md margin-bottom--md">
        <div className="card__body padding--lg text--center">
          {image && (
            <div className="margin-bottom--md">
              <img 
                src={image}
                alt={imageAlt}
                className={styles.featureImage}
              />
            </div>
          )}
          <Heading as="h3">{title}</Heading>
          <p>{description}</p>
        </div>
      </div>
    </div>
  );
}

function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}

function DemoSection(): ReactNode {
  return (
    <section className={styles.demo}>
      <div className="container">
        <div className="row">
          <div className="col col--12">
            <div className="text--center margin-bottom--lg">
              <Heading as="h2">See SpecifyX in Action</Heading>
              <p>Watch how easy it is to run specification-driven workflows</p>
            </div>
            
            <div className="text--center">
              <video 
                src="/img/gifs/specifyx-init.webm"
                className={styles.demoGif}
                autoPlay
                loop
                muted
                playsInline
              >
                Your browser does not support the video tag.
              </video>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function QuickStartSection(): ReactNode {
  return (
    <section className={styles.quickStart}>
      <div className="container">
        <div className="row">
          <div className="col col--8 col--offset-2">
            <div className="text--center margin-bottom--lg">
              <Heading as="h2">Quick Start</Heading>
              <p>Get up and running in minutes</p>
            </div>
            
            <div className="margin-vert--lg">
              <pre className="prism-code">
                <code>
{`# Install SpecifyX
uv tool install specifyx

# Create a new project  
specifyx init my-awesome-project`}
                </code>
              </pre>
            </div>

            <div className="row margin-top--lg">
              <div className="col col--6">
                <div className="card padding--lg">
                  <div className="card__header">
                    <Heading as="h4">Learn More</Heading>
                  </div>
                  <div className="card__body">
                    <ul>
                      <li><Link to="/docs/guides/installation">Installation Guide</Link></li>
                      <li><Link to="/docs/guides/workflow">Development Workflow</Link></li>
                      <li><Link to="/docs/reference/cli/init">CLI Reference</Link></li>
                    </ul>
                  </div>
                </div>
              </div>
              <div className="col col--6">
                <div className="card padding--lg">
                  <div className="card__header">
                    <Heading as="h4">Examples</Heading>
                  </div>
                  <div className="card__body">
                    <ul>
                      <li><Link to="/docs/guides/quickstart">Quick Start Tutorial</Link></li>
                      <li><a href="https://github.com/barisgit/spec-kit-improved">GitHub Repository</a></li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title} - Spec-Driven Development CLI`}
      description="Enhanced Python CLI tool for specification-driven development with AI integration">
      <HomepageHeader />
      <main>
        <HomepageFeatures />
        <DemoSection />
        <QuickStartSection />
      </main>
    </Layout>
  );
}