import { motion } from 'framer-motion'
import { CheckIcon, StarIcon } from '@heroicons/react/24/outline'

const pricingPlans = [
  {
    name: 'Open Source',
    price: 'Free',
    description: 'Perfect for individuals and small teams',
    features: [
      'All core testing features',
      'AutoPerf 3-tier system', 
      'Docker deployment',
      'Community support',
      'GitHub documentation',
      'Open source license'
    ],
    cta: 'Get Started',
    href: 'https://github.com/PenguinCloud/WaddlePerf',
    popular: false
  },
  {
    name: 'Enterprise', 
    price: 'Contact Us',
    description: 'For organizations requiring enterprise features',
    features: [
      'Everything in Open Source',
      'Priority support (24/7)',
      'Custom integrations',
      'Advanced security features',
      'SLA guarantees', 
      'Professional services',
      'Custom deployment options'
    ],
    cta: 'Contact Sales',
    href: 'mailto:sales@penguintech.io',
    popular: true
  },
  {
    name: 'Managed Service',
    price: 'Custom',
    description: 'Fully managed WaddlePerf in the cloud',
    features: [
      'Hosted infrastructure',
      'Automatic updates',
      'Monitoring & alerting',
      'Backup & disaster recovery',
      'Global edge locations',
      'White-label options'
    ],
    cta: 'Learn More',
    href: 'mailto:sales@penguintech.io',
    popular: false
  }
]

export default function Pricing() {
  return (
    <section id="pricing" className="py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4"
          >
            Choose Your Plan
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="text-xl text-gray-600 max-w-3xl mx-auto"
          >
            Start free with open source, scale with enterprise features
          </motion.p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
          {pricingPlans.map((plan, index) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.2 }}
              className={`card relative ${
                plan.popular ? 'ring-2 ring-primary-500 scale-105' : ''
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <div className="bg-primary-500 text-white px-4 py-1 rounded-full text-sm font-medium flex items-center">
                    <StarIcon className="w-4 h-4 mr-1" />
                    Most Popular
                  </div>
                </div>
              )}
              
              <div className="text-center mb-6">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                <div className="text-4xl font-bold text-primary-600 mb-2">{plan.price}</div>
                <p className="text-gray-600">{plan.description}</p>
              </div>

              <ul className="space-y-3 mb-8 flex-grow">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start">
                    <CheckIcon className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>

              <a
                href={plan.href}
                className={`block w-full text-center py-3 px-6 rounded-lg font-semibold transition-all ${
                  plan.popular
                    ? 'bg-primary-600 text-white hover:bg-primary-700'
                    : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                }`}
              >
                {plan.cta}
              </a>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.8 }}
          className="text-center mt-12"
        >
          <p className="text-gray-600 mb-4">
            All plans include access to our comprehensive documentation and community support
          </p>
          <p className="text-sm text-gray-500">
            Enterprise pricing is based on usage and specific requirements. Contact us for a custom quote.
          </p>
        </motion.div>
      </div>
    </section>
  )
}