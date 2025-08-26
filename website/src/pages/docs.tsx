import Link from 'next/link'
import { GetStaticProps } from 'next'
import fs from 'fs'
import path from 'path'

interface DocsPageProps {
  docs: {
    slug: string
    title: string
    description: string
  }[]
}

export default function DocsPage({ docs }: DocsPageProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            📚 Documentation
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Comprehensive guides and documentation for WaddlePerf - your network performance testing platform
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {docs.map((doc) => (
            <Link
              key={doc.slug}
              href={`/docs/${doc.slug}`}
              className="bg-white rounded-lg p-6 shadow-md hover:shadow-lg transition-shadow duration-200 border border-gray-200 hover:border-blue-300"
            >
              <h3 className="text-xl font-semibold text-gray-900 mb-3">
                {doc.title}
              </h3>
              <p className="text-gray-600 leading-relaxed">
                {doc.description}
              </p>
              <div className="mt-4 text-blue-600 font-medium">
                Read more →
              </div>
            </Link>
          ))}
        </div>

        <div className="mt-12 text-center">
          <Link
            href="/"
            className="inline-flex items-center text-blue-600 hover:text-blue-800 font-medium"
          >
            ← Back to Home
          </Link>
        </div>
      </div>
    </div>
  )
}

export const getStaticProps: GetStaticProps = async () => {
  const docsConfig = [
    {
      slug: 'installation',
      title: 'Installation Guide',
      description: 'Step-by-step instructions to install and set up WaddlePerf on your system'
    },
    {
      slug: 'usage',
      title: 'Usage Guide',
      description: 'Learn how to use WaddlePerf for network performance testing and monitoring'
    },
    {
      slug: 'architecture',
      title: 'Architecture',
      description: 'Technical overview of WaddlePerf\'s system architecture and components'
    },
    {
      slug: 'autoperf',
      title: 'AutoPerf Mode',
      description: 'Automated performance monitoring with tiered testing and alerts'
    },
    {
      slug: 'contributing',
      title: 'Contributing',
      description: 'Guidelines for contributing to the WaddlePerf project'
    },
    {
      slug: 'release-notes',
      title: 'Release Notes',
      description: 'Latest updates, features, and improvements in WaddlePerf releases'
    },
    {
      slug: 'public-regions',
      title: 'Public Regions',
      description: 'Information about public WaddlePerf test regions and endpoints'
    },
    {
      slug: 'license',
      title: 'License',
      description: 'License information and terms for using WaddlePerf'
    }
  ]

  return {
    props: {
      docs: docsConfig
    }
  }
}