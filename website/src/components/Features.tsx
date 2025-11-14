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
      className="group relative p-6 sm:p-8 bg-gradient-to-br from-zinc-900/50 to-zinc-900/30 backdrop-blur-sm border border-zinc-800 rounded-2xl hover:border-cyan-500/50 transition-all duration-300 hover:scale-105"
    >
      {/* Glow effect on hover */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-cyan-500/0 to-purple-600/0 group-hover:from-cyan-500/10 group-hover:to-purple-600/10 transition-all duration-300" />
      
      <div className="relative">
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

  const features = [
    {
      icon: <Wand2 className="w-7 h-7" />,
      title: "AI Video Generation",
      description: "Generate professional videos from text prompts using cutting-edge AI technology. Transform ideas into reality instantly."
    },
    {
      icon: <Brain className="w-7 h-7" />,
      title: "Smart Editing",
      description: "AI-powered editing suggestions and automatic enhancements. Let intelligence guide your creative process."
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
      icon: <Film className="w-7 h-7" />,
      title: "4K Export",
      description: "Export in stunning 4K resolution with multiple format options. Professional quality, every time."
    },
    {
      icon: <Zap className="w-7 h-7" />,
      title: "Lightning Fast",
      description: "GPU-accelerated rendering and real-time preview. No more waiting for renders to complete."
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
    <section id="features" className="relative py-20 sm:py-32 px-4 overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 bg-gradient-to-b from-black via-zinc-950 to-black" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-to-br from-cyan-500/5 to-purple-600/5 rounded-full blur-3xl" />

      <div className="relative z-10 max-w-7xl mx-auto">
        {/* Section header */}
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16 sm:mb-20"
        >
          <h2 className="text-4xl sm:text-5xl md:text-6xl font-bold mb-6">
            <span className="gradient-text">Powerful Features</span>
          </h2>
          <p className="text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto">
            Everything you need to create, edit, and export professional videos. No compromises.
          </p>
        </motion.div>

        {/* Features grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
          {features.map((feature, index) => (
            <FeatureCard key={index} {...feature} index={index} />
          ))}
        </div>
      </div>
    </section>
  )
}

