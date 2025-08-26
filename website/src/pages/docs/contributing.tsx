import Link from 'next/link'

export default function ContributingPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <Link
            href="/docs"
            className="inline-flex items-center text-blue-600 hover:text-blue-800 font-medium mb-4"
          >
            ← Back to Documentation
          </Link>
          <h1 className="text-4xl font-bold text-gray-900">
            🤝 Contributing Guide
          </h1>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="prose prose-lg max-w-none">
            <h2>Welcome Contributors!</h2>
            <p>We're excited that you're interested in contributing to WaddlePerf! This guide will help you get started with contributing to our open-source network performance testing platform.</p>
            
            <h3>🚀 Getting Started</h3>
            <ol>
              <li><strong>Fork the Repository:</strong> Create your own fork of WaddlePerf</li>
              <li><strong>Clone Locally:</strong> <code>git clone https://github.com/penguintechinc/WaddlePerf.git</code></li>
              <li><strong>Set Up Development Environment:</strong> Follow the installation guide</li>
              <li><strong>Create Feature Branch:</strong> <code>git checkout -b feature/your-feature-name</code></li>
            </ol>
            
            <h3>🛠️ Development Environment</h3>
            <h4>Prerequisites:</h4>
            <ul>
              <li><strong>Go 1.21+</strong> for client development</li>
              <li><strong>Python 3.8+</strong> for server and testing tools</li>
              <li><strong>Docker & Docker Compose</strong> for local testing</li>
              <li><strong>Node.js 18+</strong> for website development</li>
            </ul>
            
            <h4>Setup Commands:</h4>
            <pre><code># Server development
cd server
pip install -r requirements.txt

# Go client development  
cd go-client
go mod download

# Website development
cd website
npm install</code></pre>
            
            <h3>📋 Contribution Types</h3>
            <ul>
              <li><strong>Bug Fixes:</strong> Fix identified issues and improve stability</li>
              <li><strong>Feature Development:</strong> Add new testing capabilities</li>
              <li><strong>Documentation:</strong> Improve guides, examples, and API docs</li>
              <li><strong>Performance Optimization:</strong> Enhance speed and resource usage</li>
              <li><strong>Testing:</strong> Add unit tests, integration tests, and examples</li>
            </ul>
            
            <h3>📝 Code Standards</h3>
            <h4>Go Code:</h4>
            <ul>
              <li>Follow <code>gofmt</code> formatting</li>
              <li>Use meaningful variable and function names</li>
              <li>Include comprehensive error handling</li>
              <li>Write unit tests for new functions</li>
            </ul>
            
            <h4>Python Code:</h4>
            <ul>
              <li>Follow PEP8 style guidelines</li>
              <li>Use type hints where appropriate</li>
              <li>Include docstrings for functions and classes</li>
              <li>Maintain async/threading patterns</li>
            </ul>
            
            <h3>🧪 Testing Requirements</h3>
            <ul>
              <li><strong>Unit Tests:</strong> Test individual functions and components</li>
              <li><strong>Integration Tests:</strong> Test component interactions</li>
              <li><strong>Performance Tests:</strong> Ensure no performance regression</li>
              <li><strong>Documentation Tests:</strong> Verify examples work correctly</li>
            </ul>
            
            <h3>📤 Pull Request Process</h3>
            <ol>
              <li><strong>Create Clear Title:</strong> Describe the change concisely</li>
              <li><strong>Write Description:</strong> Explain what, why, and how</li>
              <li><strong>Link Issues:</strong> Reference related GitHub issues</li>
              <li><strong>Add Tests:</strong> Include relevant test coverage</li>
              <li><strong>Update Documentation:</strong> Keep docs current with changes</li>
            </ol>
            
            <h3>🏷️ Issue Labels</h3>
            <ul>
              <li><strong>good-first-issue:</strong> Perfect for new contributors</li>
              <li><strong>bug:</strong> Something isn't working correctly</li>
              <li><strong>enhancement:</strong> New feature or improvement</li>
              <li><strong>documentation:</strong> Improvements to documentation</li>
              <li><strong>performance:</strong> Speed or efficiency improvements</li>
            </ul>
            
            <h3>💬 Communication</h3>
            <ul>
              <li><strong>GitHub Issues:</strong> Bug reports and feature requests</li>
              <li><strong>GitHub Discussions:</strong> General questions and ideas</li>
              <li><strong>Pull Request Comments:</strong> Code review and feedback</li>
              <li><strong>Email:</strong> <a href="mailto:dev@penguintech.io">dev@penguintech.io</a> for private matters</li>
            </ul>
            
            <div className="bg-green-50 border-l-4 border-green-400 p-4 my-6">
              <div className="flex">
                <div className="ml-3">
                  <p className="text-sm text-green-700">
                    <strong>🌟 Recognition:</strong> All contributors are acknowledged in our README and release notes. Thank you for helping make WaddlePerf better!
                  </p>
                </div>
              </div>
            </div>
            
            <h3>📄 Code of Conduct</h3>
            <p>We are committed to providing a welcoming and inspiring community for all. Please review our Code of Conduct before contributing.</p>
            
            <h3>📞 Need Help?</h3>
            <p>Don't hesitate to ask questions! Create an issue with the "question" label or reach out via email. We're here to help you contribute successfully.</p>
          </div>
        </div>
      </div>
    </div>
  )
}