# WaddlePerf Marketing Website

A modern, responsive marketing website for WaddlePerf built with Next.js, TypeScript, and Tailwind CSS. Optimized for deployment on Cloudflare Pages.

## 🚀 Features

- **Responsive Design**: Automatically adapts to mobile vs desktop
- **Modern Stack**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **Animations**: Framer Motion for smooth interactions
- **Performance**: Optimized for Cloudflare Pages static deployment
- **SEO Ready**: Meta tags, structured data, and performance optimized

## 🛠️ Development

### Prerequisites
- Node.js 18+ 
- npm or yarn

### Local Development
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Open http://localhost:3000
```

### Build for Production
```bash
# Build and export static files
npm run build

# Files will be in /out directory
```

## 📦 Deployment

### Cloudflare Pages
1. Connect your GitHub repository to Cloudflare Pages
2. Set build command: `npm run build`
3. Set build output directory: `out`
4. Deploy!

### Environment Variables
No environment variables needed - this is a static site.

## 🎨 Customization

### Colors
Primary brand colors are configured in `tailwind.config.js`:
- Primary: Blue shades (WaddlePerf brand)
- Secondary: Green shades (for accents)

### Content
Update content in the following files:
- `src/pages/index.tsx` - Main landing page
- `src/components/` - Individual sections
- `package.json` - Site metadata

### Styling
- Global styles: `src/styles/globals.css`
- Component styles: Tailwind CSS classes
- Custom animations: Defined in Tailwind config

## 🏗️ Project Structure

```
website/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/         # Next.js pages
│   └── styles/        # Global CSS
├── public/            # Static assets
├── package.json       # Dependencies and scripts
├── next.config.js     # Next.js configuration
├── tailwind.config.js # Tailwind CSS configuration
└── postcss.config.js  # PostCSS configuration
```

## 📱 Mobile Optimization

The site automatically detects mobile vs desktop and adjusts:
- Navigation menu (hamburger on mobile)
- Layout and spacing
- Typography scaling
- Touch-friendly interactions

## ⚡ Performance

- Static site generation (SSG)
- Optimized images
- Minimal JavaScript bundle
- CSS-in-JS with Tailwind
- Lazy loading for animations

## 🔧 Available Scripts

```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run start    # Start production server
npm run lint     # Run ESLint
npm run export   # Export static files
```

## 🎯 Key Pages & Sections

- **Hero**: Main landing with penguin ASCII art
- **Features**: Product capabilities and benefits  
- **AutoPerf**: 3-tier testing system explanation
- **Testing Tools**: Comprehensive tool showcase
- **Pricing**: Open source vs enterprise plans
- **CTA**: Download and documentation links

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on mobile and desktop
5. Submit a pull request

## 📄 License

This website is part of the WaddlePerf project and is licensed under the MIT License.

## 🐧 About WaddlePerf

WaddlePerf is a comprehensive network performance testing platform that allows complete testing of user experience from one system to another. Built by Penguin Technologies Inc.

For more information, visit the main [WaddlePerf repository](https://github.com/PenguinCloud/WaddlePerf).