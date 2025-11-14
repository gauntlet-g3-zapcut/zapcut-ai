import { motion } from 'framer-motion'
import { Sparkles, Zap } from 'lucide-react'

export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden px-4">
      {/* Animated background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-black via-zinc-900 to-black">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(6,182,212,0.1),transparent_50%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_20%,rgba(139,92,246,0.15),transparent_50%)]" />
      </div>

      {/* Content */}
      <div className="relative z-10 max-w-6xl mx-auto text-center">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="inline-flex items-center gap-2 px-4 py-2 mb-8 rounded-full bg-zinc-900/50 border border-cyan-500/20 backdrop-blur-sm"
        >
          <Sparkles className="w-4 h-4 text-cyan-400" />
          <span className="text-sm text-cyan-300 font-medium">
            AI-Powered Video Creation
          </span>
        </motion.div>

        {/* Main headline */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-bold mb-6 leading-tight"
        >
          Create Videos
          <br />
          <span className="gradient-text">At Light Speed</span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="text-lg sm:text-xl md:text-2xl text-gray-300 mb-12 max-w-3xl mx-auto leading-relaxed"
        >
          Professional video editing meets artificial intelligence.
          Generate, edit, and export stunning videos in minutes.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.6 }}
          className="flex flex-col sm:flex-row gap-4 justify-center items-center"
        >
          <a
            href="#download"
            className="group relative px-8 py-4 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-lg font-semibold text-white text-lg transition-all hover:scale-105 hover:shadow-[0_0_40px_rgba(6,182,212,0.6)] flex items-center gap-2"
          >
            <Zap className="w-5 h-5" />
            Download Now
            <span className="absolute inset-0 rounded-lg bg-gradient-to-r from-cyan-400 to-purple-500 opacity-0 group-hover:opacity-20 transition-opacity blur-xl" />
          </a>
          
          <a
            href="#features"
            className="px-8 py-4 bg-zinc-900/50 border border-zinc-700 rounded-lg font-semibold text-white text-lg transition-all hover:bg-zinc-800 hover:border-zinc-600 hover:scale-105"
          >
            Learn More
          </a>
        </motion.div>

        {/* Floating elements */}
        <motion.div
          animate={{ y: [0, -20, 0] }}
          transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
          className="absolute top-20 left-10 w-20 h-20 bg-gradient-to-br from-cyan-500/20 to-purple-600/20 rounded-full blur-2xl"
        />
        <motion.div
          animate={{ y: [0, 20, 0] }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
          className="absolute bottom-20 right-10 w-32 h-32 bg-gradient-to-br from-purple-600/20 to-pink-500/20 rounded-full blur-3xl"
        />
      </div>

      {/* Scroll indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.5, duration: 1 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
      >
        <motion.div
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="w-6 h-10 border-2 border-gray-600 rounded-full flex justify-center pt-2"
        >
          <div className="w-1.5 h-3 bg-gradient-to-b from-cyan-400 to-transparent rounded-full" />
        </motion.div>
      </motion.div>
    </section>
  )
}

