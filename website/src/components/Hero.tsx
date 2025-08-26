import { motion } from 'framer-motion'
import { PlayIcon, ArrowDownIcon } from '@heroicons/react/24/outline'

export default function Hero() {
  return (
    <section className="pt-24 pb-12 sm:pt-32 sm:pb-16 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-32 w-80 h-80 rounded-full bg-primary-100 opacity-50"></div>
        <div className="absolute -bottom-32 -left-32 w-80 h-80 rounded-full bg-secondary-100 opacity-50"></div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        <div className="text-center">
          {/* Penguin ASCII Art */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8 }}
            className="mb-8"
          >
            <pre className="text-sm sm:text-base text-primary-600 font-mono penguin-shadow">
{`     ___     
    (.  \\    
     \\   |   
      >  )  
     /  /    Waddle fast, test faster! 🚀
    /  /     Network Performance Testing at Penguin Speed
   (  (      
    \\ \\_     
     \\__)    `}
            </pre>
          </motion.div>

          {/* Main Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-4xl sm:text-6xl lg:text-7xl font-bold text-gray-900 mb-6"
          >
            <span className="block">Network Testing</span>
            <span className="block">
              Made <span className="text-primary-600">Simple</span>
            </span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="text-xl sm:text-2xl text-gray-600 max-w-3xl mx-auto mb-10"
          >
            Complete user experience testing from one system to another. 
            Monitor internet connectivity, test inter-region latency, and analyze intra-cluster performance.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="space-y-4 sm:space-y-0 sm:space-x-4 sm:flex sm:justify-center mb-16"
          >
            <a
              href="https://github.com/PenguinCloud/WaddlePerf"
              className="inline-flex items-center btn-primary text-lg px-8 py-4"
            >
              <PlayIcon className="w-6 h-6 mr-2" />
              Get Started Free
            </a>
            <a
              href="#features"
              className="inline-flex items-center btn-secondary text-lg px-8 py-4"
            >
              Learn More
            </a>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="grid grid-cols-1 sm:grid-cols-3 gap-8 max-w-2xl mx-auto"
          >
            {[
              { value: '3-Tier', label: 'Smart Testing System' },
              { value: '8+', label: 'Testing Tools' },
              { value: '100%', label: 'Open Source' },
            ].map((stat, index) => (
              <div key={stat.label} className="text-center">
                <div className="text-2xl sm:text-3xl font-bold text-primary-600">{stat.value}</div>
                <div className="text-sm text-gray-600">{stat.label}</div>
              </div>
            ))}
          </motion.div>
        </div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2 }}
          className="absolute bottom-8 left-1/2 transform -translate-x-1/2"
        >
          <ArrowDownIcon className="w-6 h-6 text-gray-400 animate-bounce" />
        </motion.div>
      </div>
    </section>
  )
}