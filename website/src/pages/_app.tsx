import '../styles/globals.css'
import type { AppProps } from 'next/app'
import Head from 'next/head'

export default function App({ Component, pageProps }: AppProps) {
  return (
    <>
      <Head>
        <title>WaddlePerf - Network Performance Testing Platform</title>
        <meta name="description" content="Waddle fast, test faster! Comprehensive network performance testing and monitoring at penguin speed." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
        <meta property="og:title" content="WaddlePerf - Network Performance Testing" />
        <meta property="og:description" content="Comprehensive network performance testing and monitoring platform" />
        <meta property="og:type" content="website" />
        <meta name="twitter:card" content="summary_large_image" />
      </Head>
      <Component {...pageProps} />
    </>
  )
}