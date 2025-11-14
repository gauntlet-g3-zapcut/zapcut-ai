# ZapCut Marketing Website

A futuristic, dark-themed marketing landing page for [zapcut.video](https://zapcut.video) - AI-powered video generation and editing software.

## Tech Stack

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Fast build tool
- **Tailwind CSS v4** - Styling with dark theme
- **Framer Motion** - Smooth animations
- **Lucide React** - Icon library

## Features

- 🌑 **100% Dark Theme** - Easy on the eyes, modern aesthetic
- ✨ **Animated Text & Effects** - Gradient text, shimmer, float animations
- 🎨 **Futuristic Design** - Cyan/purple gradients, glowing effects
- 📱 **Fully Responsive** - Works on all screen sizes
- ⚡ **Lightning Fast** - Static site with optimal performance
- 🎯 **Download CTAs** - Platform-specific download buttons (Windows, macOS, Linux)

## Project Structure

```
website/
├── src/
│   ├── components/
│   │   ├── Hero.tsx          # Hero section with animated headline
│   │   ├── Features.tsx      # Feature showcase grid
│   │   ├── DownloadCTA.tsx   # Download buttons for all platforms
│   │   └── Footer.tsx        # Footer with links
│   ├── lib/
│   │   └── utils.ts          # Utility functions
│   ├── App.tsx               # Main app component
│   ├── main.tsx              # Entry point
│   └── globals.css           # Global styles & animations
├── public/
│   └── zapcut-app-icon.jpg   # App icon
├── index.html                # HTML entry
├── package.json              # Dependencies
├── vite.config.ts            # Vite configuration
├── tsconfig.json             # TypeScript configuration
└── .gitignore                # Git ignore patterns
```

## Getting Started

### Install Dependencies

```bash
npm install
```

### Development Server

```bash
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

### Build for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Design Elements

### Color Scheme
- **Backgrounds**: Black (#000000), Dark Gray (#18181b, #09090b)
- **Text**: White (#ffffff), Light Gray (#d4d4d8)
- **Accents**: Cyan (#06b6d4), Purple (#8b5cf6), Pink (#ec4899)

### Animations
- **Gradient Text**: Animated background position for shimmer effect
- **Float**: Subtle up/down motion on decorative elements
- **Glow**: Pulsing shadow effects on hover
- **Scroll Reveal**: Components fade/slide in when scrolled into view

### Typography
- Large, bold headings with gradient fills
- Generous line-height for readability
- Modern sans-serif font stack

## Customization

### Update Download Links

Edit the platform buttons in `src/components/DownloadCTA.tsx`:

```tsx
<a href="YOUR_WINDOWS_DOWNLOAD_URL">
  ...
</a>
```

### Modify Colors

Update the gradient colors in `src/globals.css` and component files.

### Add More Features

Add new feature cards to the `features` array in `src/components/Features.tsx`.

## Deployment

The site is a static bundle. Deploy the `dist/` folder to any static hosting service:

- **Vercel**: `vercel --prod`
- **Netlify**: Drag & drop the `dist/` folder
- **GitHub Pages**: Push `dist/` to gh-pages branch
- **AWS S3**: Upload `dist/` contents to S3 bucket

## License

Part of the ZapCut project.
