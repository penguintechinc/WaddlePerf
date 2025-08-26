import { motion } from 'framer-motion'

export default function Footer() {
  return (
    <footer className="bg-gray-900">
      <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:py-16 lg:px-8">
        <div className="xl:grid xl:grid-cols-3 xl:gap-8">
          <div className="space-y-8 xl:col-span-1">
            <div className="flex items-center">
              <div className="text-2xl mr-2">🐧</div>
              <div className="font-bold text-xl text-white">
                Waddle<span className="text-primary-400">Perf</span>
              </div>
            </div>
            <p className="text-gray-400 text-base">
              Network performance testing at penguin speed. 
              Open source, enterprise-ready, and built for scale.
            </p>
            <div className="flex space-x-6">
              <a href="https://github.com/penguintechinc/WaddlePerf" className="text-gray-400 hover:text-gray-300">
                <span className="sr-only">GitHub</span>
                <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                  <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                </svg>
              </a>
            </div>
          </div>
          <div className="mt-12 grid grid-cols-2 gap-8 xl:mt-0 xl:col-span-2">
            <div className="md:grid md:grid-cols-2 md:gap-8">
              <div>
                <h3 className="text-sm font-semibold text-gray-300 tracking-wider uppercase">Product</h3>
                <ul className="mt-4 space-y-4">
                  <li><a href="#features" className="text-base text-gray-400 hover:text-white">Features</a></li>
                  <li><a href="#pricing" className="text-base text-gray-400 hover:text-white">Pricing</a></li>
                  <li><a href="https://github.com/penguintechinc/WaddlePerf/releases" className="text-base text-gray-400 hover:text-white">Download</a></li>
                  <li><a href="https://github.com/penguintechinc/WaddlePerf" className="text-base text-gray-400 hover:text-white">GitHub</a></li>
                </ul>
              </div>
              <div className="mt-12 md:mt-0">
                <h3 className="text-sm font-semibold text-gray-300 tracking-wider uppercase">Documentation</h3>
                <ul className="mt-4 space-y-4">
                  <li><a href="/docs/installation" className="text-base text-gray-400 hover:text-white">Installation</a></li>
                  <li><a href="/docs/usage" className="text-base text-gray-400 hover:text-white">Usage Guide</a></li>
                  <li><a href="/docs/autoperf" className="text-base text-gray-400 hover:text-white">AutoPerf</a></li>
                  <li><a href="/docs/architecture" className="text-base text-gray-400 hover:text-white">Architecture</a></li>
                </ul>
              </div>
            </div>
            <div className="md:grid md:grid-cols-2 md:gap-8">
              <div>
                <h3 className="text-sm font-semibold text-gray-300 tracking-wider uppercase">Support</h3>
                <ul className="mt-4 space-y-4">
                  <li><a href="https://github.com/penguintechinc/WaddlePerf/issues" className="text-base text-gray-400 hover:text-white">GitHub Issues</a></li>
                  <li><a href="/docs/contributing" className="text-base text-gray-400 hover:text-white">Contributing</a></li>
                  <li><a href="mailto:support@penguintech.io" className="text-base text-gray-400 hover:text-white">Email Support</a></li>
                  <li><a href="/docs/security" className="text-base text-gray-400 hover:text-white">Security</a></li>
                </ul>
              </div>
              <div className="mt-12 md:mt-0">
                <h3 className="text-sm font-semibold text-gray-300 tracking-wider uppercase">Company</h3>
                <ul className="mt-4 space-y-4">
                  <li><a href="https://penguintech.io" className="text-base text-gray-400 hover:text-white">Penguin Technologies</a></li>
                  <li><a href="mailto:sales@penguintech.io" className="text-base text-gray-400 hover:text-white">Contact Sales</a></li>
                  <li><a href="/privacy" className="text-base text-gray-400 hover:text-white">Privacy Policy</a></li>
                  <li><a href="/terms" className="text-base text-gray-400 hover:text-white">Terms of Service</a></li>
                </ul>
              </div>
            </div>
          </div>
        </div>
        <div className="mt-12 border-t border-gray-800 pt-8">
          <p className="text-base text-gray-400 xl:text-center">
            &copy; 2024 Penguin Technologies Inc. All rights reserved. WaddlePerf is open source under the MIT License.
          </p>
        </div>
      </div>
    </footer>
  )
}