import Link from 'next/link'
import { GetStaticProps } from 'next'

interface DocsPageProps {
  docs: {
    slug: string
    title: string
    description: string
    icon: string
    category: string
  }[]
}

export default function DocsPage({ docs }: DocsPageProps) {
  const gettingStarted = docs.filter(doc => doc.category === 'getting-started')
  const coreFeatures = docs.filter(doc => doc.category === 'core')
  const reference = docs.filter(doc => doc.category === 'reference')

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <nav className="flex mb-8" aria-label="Breadcrumb">
            <ol className="inline-flex items-center space-x-1 md:space-x-3">
              <li className="inline-flex items-center">
                <Link href="/" className="text-gray-200 hover:text-white transition-colors">
                  Home
                </Link>
              </li>
              <li>
                <div className="flex items-center">
                  <svg className="w-3 h-3 mx-2 text-gray-300" fill="currentColor" viewBox="0 0 12 12">
                    <path d="M5.293 3.293a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 01-1.414-1.414L6.586 8H3a1 1 0 110-2h3.586L5.293 4.707a1 1 0 010-1.414z"/>
                  </svg>
                  <span className="text-gray-100">Documentation</span>
                </div>
              </li>
            </ol>
          </nav>
          
          <div className="text-center">
            <h1 className="text-5xl font-bold mb-4">
              Documentation
            </h1>
            <p className="text-xl text-gray-100 max-w-3xl mx-auto">
              Everything you need to know about WaddlePerf - from installation to advanced configuration
            </p>
          </div>
          
          {/* Search Bar */}
          <div className="mt-8 max-w-xl mx-auto">
            <div className="relative">
              <input
                type="text"
                placeholder="Search documentation..."
                className="w-full px-4 py-3 pl-12 text-gray-900 bg-white rounded-lg shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
              />
              <svg className="absolute left-4 top-3.5 h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
              </svg>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Quick Links */}
        <div className="mb-12 grid grid-cols-1 md:grid-cols-3 gap-4">
          <a href="#getting-started" className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
            <div className="flex items-center">
              <div className="bg-blue-100 p-3 rounded-lg">
                <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                </svg>
              </div>
              <div className="ml-4">
                <h3 className="font-semibold text-gray-900">Quick Start</h3>
                <p className="text-sm text-gray-600">Get up and running in minutes</p>
              </div>
            </div>
          </a>
          
          <a href="https://github.com/penguintechinc/WaddlePerf" target="_blank" className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
            <div className="flex items-center">
              <div className="bg-gray-100 p-3 rounded-lg">
                <svg className="h-6 w-6 text-gray-600" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
              </div>
              <div className="ml-4">
                <h3 className="font-semibold text-gray-900">GitHub</h3>
                <p className="text-sm text-gray-600">View source code</p>
              </div>
            </div>
          </a>
          
          <a href="/docs/contributing" className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
            <div className="flex items-center">
              <div className="bg-green-100 p-3 rounded-lg">
                <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"></path>
                </svg>
              </div>
              <div className="ml-4">
                <h3 className="font-semibold text-gray-900">Contribute</h3>
                <p className="text-sm text-gray-600">Join our community</p>
              </div>
            </div>
          </a>
        </div>

        {/* Getting Started Section */}
        <div className="mb-12" id="getting-started">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Getting Started</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {gettingStarted.map((doc) => (
              <Link
                key={doc.slug}
                href={`/docs/${doc.slug}`}
                className="group bg-white rounded-xl p-6 shadow-sm hover:shadow-lg transition-all duration-200 border border-gray-100 hover:border-blue-200"
              >
                <div className="flex items-start">
                  <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-3 rounded-lg">
                    <span className="text-2xl">{doc.icon}</span>
                  </div>
                  <div className="ml-4 flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                      {doc.title}
                    </h3>
                    <p className="mt-2 text-sm text-gray-600 leading-relaxed">
                      {doc.description}
                    </p>
                    <div className="mt-4 flex items-center text-sm font-medium text-blue-600 group-hover:text-blue-700">
                      Learn more
                      <svg className="ml-1 h-4 w-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path>
                      </svg>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Core Features Section */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Core Features</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {coreFeatures.map((doc) => (
              <Link
                key={doc.slug}
                href={`/docs/${doc.slug}`}
                className="group bg-white rounded-xl p-6 shadow-sm hover:shadow-lg transition-all duration-200 border border-gray-100 hover:border-green-200"
              >
                <div className="flex items-start">
                  <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-3 rounded-lg">
                    <span className="text-2xl">{doc.icon}</span>
                  </div>
                  <div className="ml-4 flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 group-hover:text-green-600 transition-colors">
                      {doc.title}
                    </h3>
                    <p className="mt-2 text-sm text-gray-600 leading-relaxed">
                      {doc.description}
                    </p>
                    <div className="mt-4 flex items-center text-sm font-medium text-green-600 group-hover:text-green-700">
                      Explore
                      <svg className="ml-1 h-4 w-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path>
                      </svg>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Reference Section */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Reference</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {reference.map((doc) => (
              <Link
                key={doc.slug}
                href={`/docs/${doc.slug}`}
                className="group bg-white rounded-xl p-6 shadow-sm hover:shadow-lg transition-all duration-200 border border-gray-100 hover:border-purple-200"
              >
                <div className="flex items-start">
                  <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-3 rounded-lg">
                    <span className="text-2xl">{doc.icon}</span>
                  </div>
                  <div className="ml-4 flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 group-hover:text-purple-600 transition-colors">
                      {doc.title}
                    </h3>
                    <p className="mt-2 text-sm text-gray-600 leading-relaxed">
                      {doc.description}
                    </p>
                    <div className="mt-4 flex items-center text-sm font-medium text-purple-600 group-hover:text-purple-700">
                      View details
                      <svg className="ml-1 h-4 w-4 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path>
                      </svg>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Help Section */}
        <div className="mt-16 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-8">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Need Help?</h2>
            <p className="text-gray-600 mb-6">Can't find what you're looking for? We're here to help!</p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a href="https://github.com/penguintechinc/WaddlePerf/issues" target="_blank" className="inline-flex items-center px-6 py-3 bg-white text-gray-700 font-medium rounded-lg shadow-sm hover:shadow-md transition-shadow">
                <svg className="h-5 w-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd"></path>
                </svg>
                Report an Issue
              </a>
              <a href="https://github.com/penguintechinc/WaddlePerf/discussions" target="_blank" className="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-medium rounded-lg shadow-sm hover:bg-blue-700 transition-colors">
                <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z"></path>
                </svg>
                Community Forum
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export const getStaticProps: GetStaticProps = async () => {
  const docsConfig = [
    {
      slug: 'installation',
      title: 'Installation',
      description: 'Step-by-step instructions to install and set up WaddlePerf on your system',
      icon: '🚀',
      category: 'getting-started'
    },
    {
      slug: 'usage',
      title: 'Usage Guide',
      description: 'Learn how to use WaddlePerf for network performance testing and monitoring',
      icon: '📖',
      category: 'getting-started'
    },
    {
      slug: 'configuration',
      title: 'Configuration',
      description: 'Configure WaddlePerf for your specific environment and requirements',
      icon: '⚙️',
      category: 'getting-started'
    },
    {
      slug: 'autoperf',
      title: 'AutoPerf Mode',
      description: 'Automated performance monitoring with tiered testing and intelligent alerts',
      icon: '🤖',
      category: 'core'
    },
    {
      slug: 'architecture',
      title: 'Architecture',
      description: 'Technical overview of WaddlePerf\'s system design and components',
      icon: '🏗️',
      category: 'core'
    },
    {
      slug: 'public-regions',
      title: 'Public Regions',
      description: 'Global test regions and endpoints for worldwide performance testing',
      icon: '🌍',
      category: 'core'
    },
    {
      slug: 'api-reference',
      title: 'API Reference',
      description: 'Complete API documentation for integrating with WaddlePerf',
      icon: '📡',
      category: 'reference'
    },
    {
      slug: 'release-notes',
      title: 'Release Notes',
      description: 'Latest updates, features, and improvements in WaddlePerf releases',
      icon: '📋',
      category: 'reference'
    },
    {
      slug: 'contributing',
      title: 'Contributing',
      description: 'Guidelines for contributing to the WaddlePerf open-source project',
      icon: '🤝',
      category: 'reference'
    }
  ]

  return {
    props: {
      docs: docsConfig
    }
  }
}