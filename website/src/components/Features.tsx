import { motion } from 'framer-motion'
import { useInView } from 'framer-motion'
import { useRef } from 'react'
import {
  Wand2,
  Video,
  Scissors,
  Sparkles,
  Layers,
  Zap,
  Brain,
  Palette,
  Film
} from 'lucide-react'

interface FeatureCardProps {
  icon: React.ReactNode
  title: string
  description: string
  index: number
}

function FeatureCard({ icon, title, description, index }: FeatureCardProps) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: "-100px" })

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 50 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 50 }}
      transition={{ duration: 0.6, delay: index * 0.1 }}
      className="group relative w-full max-w-sm mx-auto p-7 sm:p-9 bg-gradient-to-br from-zinc-900/50 to-zinc-900/30 backdrop-blur-sm border border-zinc-800 rounded-2xl hover:border-cyan-500/50 transition-all duration-300 hover:scale-105 text-center"
    >
      {/* Glow effect on hover */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-cyan-500/0 to-purple-600/0 group-hover:from-cyan-500/10 group-hover:to-purple-600/10 transition-all duration-300" />

      <div className="relative flex flex-col items-center gap-2 text-center">
        {/* Icon */}
        <div className="mb-4 w-14 h-14 rounded-xl bg-gradient-to-br from-cyan-500/20 to-purple-600/20 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
          <div className="text-cyan-400 group-hover:text-cyan-300 transition-colors">
            {icon}
          </div>
        </div>

        {/* Content */}
        <h3 className="text-xl sm:text-2xl font-bold mb-3 text-white group-hover:text-cyan-300 transition-colors">
          {title}
        </h3>
        <p className="text-gray-400 leading-relaxed">
          {description}
        </p>
      </div>
    </motion.div>
  )
}

export default function Features() {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: "-100px" })

  const mainFeatures = [
    {
      icon: <Brain className="w-8 h-8" />,
      title: "AI-Powered",
      description: "Let our Creative Director AI guide you through the process. Chat with our AI to define your ad style, and watch it create a complete video production."
    },
    {
      icon: <Film className="w-8 h-8" />,
      title: "4K Quality",
      description: "Generate 4K video ads with matching soundtracks, ready for any platform. Professional-grade video output that stands out."
    },
    {
      icon: <Zap className="w-8 h-8" />,
      title: "Fast & Easy",
      description: "From concept to video in under 5 minutes. No video editing skills required. Just describe your vision and we'll bring it to life."
    }
  ]

  const additionalFeatures = [
    {
      icon: <Wand2 className="w-7 h-7" />,
      title: "AI Video Generation",
      description: "Generate professional videos from text prompts using cutting-edge AI technology. Transform ideas into reality instantly."
    },
    {
      icon: <Scissors className="w-7 h-7" />,
      title: "Precision Tools",
      description: "Professional-grade editing tools with frame-perfect accuracy. Cut, trim, and splice with surgical precision."
    },
    {
      icon: <Layers className="w-7 h-7" />,
      title: "Multi-Track Timeline",
      description: "Unlimited video, audio, and effect layers. Build complex compositions with ease and flexibility."
    },
    {
      icon: <Palette className="w-7 h-7" />,
      title: "Effects & Filters",
      description: "Extensive library of visual effects, color grading, and filters. Make every frame look cinematic."
    },
    {
      icon: <Video className="w-7 h-7" />,
      title: "All Formats",
      description: "Support for every major video, audio, and image format. Import and export without conversion hassles."
    },
    {
      icon: <Sparkles className="w-7 h-7" />,
      title: "Motion Graphics",
      description: "Create stunning animations and motion graphics. Bring your videos to life with dynamic movement."
    }
  ]

  return (
    <section id="features" className="relative py-24 sm:py-32 lg:py-40 px-6 overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 bg-gradient-to-b from-black via-zinc-950 to-black" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-to-br from-cyan-500/5 to-purple-600/5 rounded-full blur-3xl" />

      <div className="relative z-10 flex flex-col items-center">
        {/* Section header */}
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-20 sm:mb-24 w-full flex flex-col items-center"
        >
          <h2 className="text-4xl sm:text-5xl md:text-6xl font-bold mb-8">
            <span className="gradient-text">Why Choose ZapCut</span>
          </h2>
          <p className="text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed text-center" style={{ marginBottom: '40px' }}>
            Everything you need to create professional video ads. No compromises.
          </p>
        </motion.div>

        {/* Main Features - Larger cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 lg:gap-10 w-full max-w-7xl mx-auto px-6 mb-24 justify-items-center">
          {mainFeatures.map((feature, index) => (
            <motion.div
              key={index}
              ref={ref}
              initial={{ opacity: 0, y: 50 }}
              animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 50 }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              className="group relative w-full max-w-sm mx-auto p-10 sm:p-12 bg-gradient-to-br from-zinc-900/70 to-zinc-900/40 backdrop-blur-sm border-2 border-zinc-700 rounded-3xl hover:border-cyan-500/70 transition-all duration-300 hover:scale-105 text-center"
            >
              {/* Enhanced glow effect on hover */}
              <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-cyan-500/0 to-purple-600/0 group-hover:from-cyan-500/15 group-hover:to-purple-600/15 transition-all duration-300" />

              <div className="relative flex flex-col items-center gap-2 text-center">
                {/* Larger icon */}
                <div className="mb-6 w-20 h-20 rounded-2xl bg-gradient-to-br from-cyan-500/30 to-purple-600/30 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                  <div className="text-cyan-400 group-hover:text-cyan-300 transition-colors">
                    {feature.icon}
                  </div>
                </div>

                {/* Content */}
                <h3 className="text-2xl sm:text-3xl font-bold mb-4 text-white group-hover:text-cyan-300 transition-colors">
                  {feature.title}
                </h3>
                <p className="text-gray-400 text-base leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Additional Features heading */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="text-center mb-16 w-full"
        >
          <h3 className="text-3xl sm:text-4xl font-bold mb-4 py-10">
            <span className="gradient-text">Plus Even More Features</span>
          </h3>
        </motion.div>

        {/* Additional Features grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-7 sm:gap-8 lg:gap-10 w-full max-w-7xl mx-auto px-6 justify-items-center">
          {additionalFeatures.map((feature, index) => (
            <FeatureCard key={index} {...feature} index={index + 3} />
          ))}
        </div>
      </div>
    </section>
  )
}

