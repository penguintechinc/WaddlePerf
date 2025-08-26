import { useState, useEffect } from 'react'
import Head from 'next/head'
import { motion } from 'framer-motion'
import { 
  ChartBarIcon, 
  GlobeAltIcon, 
  BoltIcon, 
  ShieldCheckIcon,
  ServerIcon,
  DevicePhoneMobileIcon,
  ComputerDesktopIcon,
  PlayIcon,
  ArrowDownIcon,
  CheckIcon
} from '@heroicons/react/24/outline'

import Navigation from '../components/Navigation'
import Hero from '../components/Hero'
import Features from '../components/Features'
import Pricing from '../components/Pricing'
import Footer from '../components/Footer'

const features = [
  {
    name: 'AutoPerf Monitoring',
    description: 'Intelligent 3-tier testing system that automatically escalates when thresholds are exceeded.',
    icon: ChartBarIcon,
  },
  {
    name: 'Global Testing',
    description: 'Test connectivity between any endpoints - regions, clusters, or internet connections.',
    icon: GlobeAltIcon,
  },
  {
    name: 'Lightning Fast',
    description: 'Optimized for speed with minimal resource usage during continuous monitoring.',
    icon: BoltIcon,
  },
  {
    name: 'Enterprise Security',
    description: 'Security gold standard with vulnerability scanning and secure deployment options.',
    icon: ShieldCheckIcon,
  },
  {
    name: 'Multi-Platform',
    description: 'Native clients for Windows, macOS, Linux, plus Docker and cloud deployments.',
    icon: ServerIcon,
  },
  {
    name: 'Mobile Responsive',
    description: 'Full-featured web interface that works perfectly on all devices.',
    icon: DevicePhoneMobileIcon,
  },
]

const testingTools = [
  'ipping - Advanced ping testing',
  'HTTPtrace - HTTP connection analysis', 
  'MTR - Network route diagnostics',
  'iperf3 - Bandwidth testing',
  'SSH Ping - SSH connectivity checks',
  'Custom MTU Discovery',
  'UDP Ping Server/Client',
  'DNS Resolution Timing'
]

export default function Home() {
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const checkDevice = () => {
      setIsMobile(window.innerWidth < 768)
    }
    
    checkDevice()
    window.addEventListener('resize', checkDevice)
    return () => window.removeEventListener('resize', checkDevice)
  }, [])

  return (
    <>
      <Head>
        <title>WaddlePerf - Network Performance Testing Platform</title>
        <meta name="description" content="Waddle fast, test faster! Comprehensive network performance testing and monitoring at penguin speed." />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
        <Navigation isMobile={isMobile} />
        <Hero />
        
        {/* Features Section */}
        <section id="features" className="py-24 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <motion.h2
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4"
              >
                Waddle Fast, Test Faster! 🚀
              </motion.h2>
              <motion.p
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.2 }}
                className="text-xl text-gray-600 max-w-3xl mx-auto mb-16"
              >
                Complete network performance testing from one system to another. Test internet connectivity, 
                inter-region latency, or intra-cluster performance with penguin precision.
              </motion.p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {features.map((feature, index) => (
                <motion.div
                  key={feature.name}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1 }}
                  className="card group hover:border-primary-200"
                >
                  <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-primary-200 transition-colors">
                    <feature.icon className="w-6 h-6 text-primary-600" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">{feature.name}</h3>
                  <p className="text-gray-600">{feature.description}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* AutoPerf Tiers Section */}
        <section className="py-24 bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <motion.h2
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4"
              >
                AutoPerf: Smart 3-Tier Testing
              </motion.h2>
              <motion.p
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.2 }}
                className="text-xl text-gray-600 max-w-3xl mx-auto"
              >
                Intelligent monitoring that escalates testing depth based on detected anomalies
              </motion.p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {[
                {
                  tier: 'Tier 1',
                  title: 'Basic Monitoring',
                  frequency: 'Every 5 minutes',
                  description: 'Lightweight baseline monitoring with minimal resource usage',
                  tests: ['Basic Ping', 'HTTP GET', 'DNS Resolution', 'TCP Connect'],
                  color: 'green'
                },
                {
                  tier: 'Tier 2', 
                  title: 'Intermediate Diagnostics',
                  frequency: 'Threshold triggered',
                  description: 'Identify nature and scope of network issues',
                  tests: ['Extended Ping', 'Traceroute/MTR', 'iperf3 Quick', 'Port Scan'],
                  color: 'yellow'
                },
                {
                  tier: 'Tier 3',
                  title: 'Comprehensive Analysis', 
                  frequency: 'Critical issues',
                  description: 'Full diagnostic suite for root cause analysis',
                  tests: ['Extended iperf3', 'Full MTR', 'Packet Capture', 'System Diagnostics'],
                  color: 'red'
                }
              ].map((tier, index) => (
                <motion.div
                  key={tier.tier}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.2 }}
                  className={`card relative overflow-hidden ${
                    tier.color === 'green' ? 'border-green-200 hover:border-green-300' :
                    tier.color === 'yellow' ? 'border-yellow-200 hover:border-yellow-300' :
                    'border-red-200 hover:border-red-300'
                  }`}
                >
                  <div className={`absolute top-0 right-0 w-20 h-20 rounded-full opacity-10 ${
                    tier.color === 'green' ? 'bg-green-500' :
                    tier.color === 'yellow' ? 'bg-yellow-500' :
                    'bg-red-500'
                  } transform translate-x-8 -translate-y-8`}></div>
                  
                  <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium mb-4 ${
                    tier.color === 'green' ? 'bg-green-100 text-green-800' :
                    tier.color === 'yellow' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {tier.tier}
                  </div>
                  
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">{tier.title}</h3>
                  <p className="text-sm text-gray-500 mb-3">{tier.frequency}</p>
                  <p className="text-gray-600 mb-4">{tier.description}</p>
                  
                  <ul className="space-y-2">
                    {tier.tests.map((test) => (
                      <li key={test} className="flex items-center text-sm text-gray-600">
                        <CheckIcon className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
                        {test}
                      </li>
                    ))}
                  </ul>
                  
                  {index < 2 && (
                    <ArrowDownIcon className="w-6 h-6 text-gray-400 mx-auto mt-6 lg:hidden" />
                  )}
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Testing Tools Section */}
        <section className="py-24 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <motion.h2
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4"
              >
                Comprehensive Testing Suite
              </motion.h2>
              <motion.p
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.2 }}
                className="text-xl text-gray-600 max-w-3xl mx-auto"
              >
                Industry-leading network diagnostic tools integrated into one powerful platform
              </motion.p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl mx-auto">
              {testingTools.map((tool, index) => (
                <motion.div
                  key={tool}
                  initial={{ opacity: 0, x: index % 2 === 0 ? -20 : 20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-center p-4 bg-gray-50 rounded-lg hover:bg-primary-50 transition-colors"
                >
                  <CheckIcon className="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
                  <span className="text-gray-800 font-medium">{tool}</span>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <Pricing />
        
        {/* CTA Section */}
        <section className="py-24 bg-gradient-to-r from-primary-600 to-primary-800">
          <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-3xl sm:text-4xl font-bold text-white mb-4"
            >
              Ready to Start Waddling?
            </motion.h2>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
              className="text-xl text-primary-100 mb-8"
            >
              Join thousands of developers and IT teams who trust WaddlePerf for their network testing needs.
            </motion.p>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.4 }}
              className="space-y-4 sm:space-y-0 sm:space-x-4 sm:flex sm:justify-center"
            >
              <a
                href="https://github.com/PenguinCloud/WaddlePerf"
                className="inline-flex items-center btn bg-white text-primary-600 hover:bg-gray-100"
              >
                <PlayIcon className="w-5 h-5 mr-2" />
                Get Started Free
              </a>
              <a
                href="/docs"
                className="inline-flex items-center btn bg-primary-700 text-white hover:bg-primary-800 border-2 border-primary-500"
              >
                View Documentation
              </a>
            </motion.div>
          </div>
        </section>

        <Footer />
      </div>
    </>
  )
}