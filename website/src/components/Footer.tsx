import { Github, Twitter, Youtube, Mail, Heart } from 'lucide-react'

export default function Footer() {
  const currentYear = new Date().getFullYear()

  const socialLinks = [
    { icon: <Github className="w-5 h-5" />, href: "#", label: "GitHub" },
    { icon: <Twitter className="w-5 h-5" />, href: "#", label: "Twitter" },
    { icon: <Youtube className="w-5 h-5" />, href: "#", label: "YouTube" },
    { icon: <Mail className="w-5 h-5" />, href: "#", label: "Email" }
  ]

  const footerLinks = {
    Product: [
      { label: "Features", href: "#features" },
      { label: "Download", href: "#download" },
      { label: "Pricing", href: "#" },
      { label: "Changelog", href: "#" }
    ],
    Resources: [
      { label: "Documentation", href: "#" },
      { label: "Tutorials", href: "#" },
      { label: "Community", href: "#" },
      { label: "Support", href: "#" }
    ],
    Company: [
      { label: "About", href: "#" },
      { label: "Blog", href: "#" },
      { label: "Careers", href: "#" },
      { label: "Contact", href: "#" }
    ],
    Legal: [
      { label: "Privacy Policy", href: "#" },
      { label: "Terms of Service", href: "#" },
      { label: "License", href: "#" }
    ]
  }

  return (
    <footer className="relative bg-black border-t border-zinc-900 overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-zinc-950 to-black" />
      
      <div className="relative z-10 max-w-7xl mx-auto px-4 py-12 sm:py-16">
        {/* Main footer content */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-8 mb-12">
          {/* Brand section */}
          <div className="col-span-2">
            <h3 className="text-2xl font-bold mb-4">
              <span className="gradient-text">ZapCut</span>
            </h3>
            <p className="text-gray-400 mb-6 max-w-xs">
              AI-powered video generation and editing software for creators, professionals, and teams.
            </p>
            
            {/* Social links */}
            <div className="flex gap-3">
              {socialLinks.map((link, index) => (
                <a
                  key={index}
                  href={link.href}
                  aria-label={link.label}
                  className="w-10 h-10 rounded-lg bg-zinc-900/50 border border-zinc-800 flex items-center justify-center text-gray-400 hover:text-cyan-400 hover:border-cyan-500/50 hover:bg-zinc-800 transition-all duration-300"
                >
                  {link.icon}
                </a>
              ))}
            </div>
          </div>

          {/* Links sections */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h4 className="text-white font-semibold mb-4">{category}</h4>
              <ul className="space-y-2">
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
        <div className="pt-8 border-t border-zinc-900">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
            <p className="text-gray-500 text-sm text-center sm:text-left">
              © {currentYear} ZapCut. All rights reserved.
            </p>
            
            <div className="flex items-center gap-2 text-gray-500 text-sm">
              <span>Made with</span>
              <Heart className="w-4 h-4 text-red-500 fill-red-500 animate-pulse" />
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

