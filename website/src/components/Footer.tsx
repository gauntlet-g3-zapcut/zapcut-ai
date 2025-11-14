import { Heart } from 'lucide-react'

export default function Footer() {
  const currentYear = new Date().getFullYear()

  const footerLinks = {
    Product: [
      { label: "Pricing", href: "#" },
      { label: "Download", href: "#download" },
      { label: "Features", href: "#features" }
    ],
    Company: [
      { label: "Team", href: "#" },
      { label: "Support", href: "#" },
      { label: "Privacy Policy", href: "#" }
    ]
  }

  return (
    <footer className="relative bg-black border-t border-zinc-900 overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-zinc-950 to-black" />

      <div className="relative z-10 px-6 py-16 sm:py-20 lg:py-24">
        {/* Main footer content */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-10 sm:gap-12 mb-16">
          {/* Brand section */}
          <div className="col-span-2">
            <div className="flex items-center gap-3 mb-6">
              <img
                src="/assets/zapcut-app-icon-dark.jpg"
                alt="ZapCut Logo"
                className="w-10 h-10 rounded-lg"
              />
              <h3 className="text-2xl font-bold">
                <span className="gradient-text">ZapCut</span>
              </h3>
            </div>
            <p className="text-gray-400 mb-8 max-w-xs leading-relaxed">
              AI-powered video generation and editing software for creators, professionals, and teams.
            </p>
          </div>

          {/* Links sections */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h4 className="text-white font-semibold mb-5">{category}</h4>
              <ul className="space-y-3">
                {links.map((link, index) => (
                  <li key={index}>
                    <a
                      href={link.href}
                      className="text-gray-400 hover:text-cyan-400 transition-colors duration-200 text-sm"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="pt-10 border-t border-zinc-900">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-6">
            <p className="text-gray-500 text-sm text-center sm:text-left">
              © {currentYear} ZapCut. All rights reserved.
            </p>

            <div className="flex items-center gap-2 text-gray-500 text-sm">
              <span>Made with</span>
              <Heart className="w-4 h-4 text-purple-500 fill-purple-500 animate-pulse" />
              <span>for creators</span>
            </div>
          </div>
        </div>
      </div>

      {/* Decorative gradient */}
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-full h-px bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent" />
    </footer>
  )
}

