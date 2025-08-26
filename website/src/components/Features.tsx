import { motion } from 'framer-motion'
import { CheckIcon } from '@heroicons/react/24/outline'

const features = [
  'AutoPerf 3-tier escalation system',
  'Real-time network performance monitoring', 
  'Multi-platform support (Linux, Windows, macOS)',
  'Docker and Kubernetes deployments',
  'S3 integration for result storage',
  'Enterprise security standards',
  'RESTful API and webhook integration',
  'Comprehensive documentation'
]

export default function Features() {
  return (
    <section id="features" className="py-24 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Why Choose WaddlePerf?
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Built for developers and IT teams who demand reliable, comprehensive network testing
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl mx-auto">
          {features.map((feature, index) => (
            <motion.div
              key={feature}
              initial={{ opacity: 0, x: index % 2 === 0 ? -20 : 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center p-4 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow"
            >
              <CheckIcon className="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
              <span className="text-gray-800">{feature}</span>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}