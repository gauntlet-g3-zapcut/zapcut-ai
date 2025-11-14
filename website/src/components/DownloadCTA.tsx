import { motion } from 'framer-motion'
import { useInView } from 'framer-motion'
import { useRef } from 'react'
import { Download, Apple, Monitor } from 'lucide-react'

interface PlatformButtonProps {
  platform: string
  icon: React.ReactNode
  index: number
}

function PlatformButton({ platform, icon, index }: PlatformButtonProps) {
  return (
    <motion.a
      href="#"
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      viewport={{ once: true }}
      whileHover={{ scale: 1.05, y: -5 }}
      whileTap={{ scale: 0.98 }}
      className="group relative flex flex-col items-center gap-4 p-8 bg-gradient-to-br from-zinc-900/80 to-zinc-900/50 backdrop-blur-sm border-2 border-zinc-800 rounded-2xl hover:border-cyan-500/50 transition-all duration-300"
    >
      {/* Glow effect */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-cyan-500/0 to-purple-600/0 group-hover:from-cyan-500/20 group-hover:to-purple-600/20 transition-all duration-300 opacity-0 group-hover:opacity-100" />
      
      <div className="relative">
        {/* Icon */}
        <div className="w-16 h-16 mb-2 rounded-2xl bg-gradient-to-br from-cyan-500/30 to-purple-600/30 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
          <div className="text-cyan-400 group-hover:text-white transition-colors">
            {icon}
          </div>
        </div>

        {/* Platform name */}
        <h3 className="text-2xl font-bold mb-2 text-center group-hover:text-cyan-300 transition-colors">
          {platform}
        </h3>

        {/* Download text */}
        <div className="flex items-center gap-2 text-gray-400 group-hover:text-white transition-colors">
          <Download className="w-4 h-4" />
          <span className="text-sm font-medium">Download</span>
        </div>
      </div>

      {/* Animated border glow */}
      <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300">
        <div className="absolute inset-0 rounded-2xl animate-pulse bg-gradient-to-r from-cyan-500/20 to-purple-600/20 blur-xl" />
      </div>
    </motion.a>
  )
}

export default function DownloadCTA() {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: "-100px" })

  const platforms = [
    {
      name: "Windows",
      icon: <Monitor className="w-8 h-8" />
    },
    {
      name: "macOS",
      icon: <Apple className="w-8 h-8" />
    },
    {
      name: "Linux",
      icon: <Monitor className="w-8 h-8" />
    }
  ]

  return (
    <section id="download" className="relative py-20 sm:py-32 px-4 overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 bg-gradient-to-b from-black via-zinc-950 to-black" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(6,182,212,0.1),transparent_70%)]" />

      <div className="relative z-10 max-w-6xl mx-auto">
        {/* Section header */}
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl sm:text-5xl md:text-6xl font-bold mb-6">
            <span className="gradient-text">Get Started Today</span>
          </h2>
          <p className="text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto mb-4">
            Download ZapCut for your platform and start creating stunning videos in minutes.
          </p>
          <p className="text-sm text-gray-500">
            Version 1.0.0 • Free to download
          </p>
        </motion.div>

        {/* Platform buttons */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 sm:gap-8 max-w-4xl mx-auto">
          {platforms.map((platform, index) => (
            <PlatformButton
              key={platform.name}
              platform={platform.name}
              icon={platform.icon}
              index={index}
            />
          ))}
        </div>

        {/* Additional info */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          viewport={{ once: true }}
          className="mt-12 text-center"
        >
          <p className="text-gray-500 text-sm">
            System requirements: Windows 10+, macOS 11+, or modern Linux distribution
          </p>
        </motion.div>
      </div>

      {/* Decorative elements */}
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
        className="absolute top-20 left-10 w-40 h-40 bg-gradient-to-br from-cyan-500/10 to-purple-600/10 rounded-full blur-3xl"
      />
      <motion.div
        animate={{ rotate: -360 }}
        transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
        className="absolute bottom-20 right-10 w-60 h-60 bg-gradient-to-br from-purple-600/10 to-pink-500/10 rounded-full blur-3xl"
      />
    </section>
  )
}

