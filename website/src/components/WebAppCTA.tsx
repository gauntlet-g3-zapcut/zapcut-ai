import { motion } from 'framer-motion'
import { useInView } from 'framer-motion'
import { useRef } from 'react'
import { Zap, Sparkles, Play } from 'lucide-react'

export default function WebAppCTA() {
    const ref = useRef(null)
    const isInView = useInView(ref, { once: true, margin: "-100px" })

    return (
        <section
            id="get-started"
            className="relative flex w-full flex-col items-center justify-center py-24 sm:py-32 lg:py-40 px-6 overflow-hidden text-center"
        >
            {/* Background effects */}
            <div className="absolute inset-0 bg-gradient-to-b from-black via-zinc-950 to-black" />
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(6,182,212,0.1),transparent_70%)]" />

            <div className="relative z-10 mx-auto flex w-full max-w-5xl flex-col items-center justify-center">
                {/* Section header */}
                <motion.div
                    ref={ref}
                    initial={{ opacity: 0, y: 30 }}
                    animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
                    transition={{ duration: 0.8 }}
                    className="mx-auto mb-16 flex w-full max-w-3xl flex-col items-center justify-center space-y-8 text-center sm:mb-20 py-10"
                >
                    <h2 className="w-full text-4xl font-bold text-center sm:text-5xl md:text-6xl">
                        <span className="gradient-text">Ready to Create?</span>
                    </h2>
                    <p className="w-full mx-auto mb-10 max-w-2xl text-lg leading-relaxed text-center text-gray-400 sm:text-xl">
                        Launch ZapCut in your browser and start creating stunning video ads in minutes. No downloads required.
                    </p>
                </motion.div>

                {/* Main CTA Card */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.5 }}
                    viewport={{ once: true }}
                    className="relative mx-auto w-full max-w-3xl rounded-3xl border-2 border-zinc-800 bg-gradient-to-br from-zinc-900/80 to-zinc-900/50 p-10 transition-all duration-300 hover:border-cyan-500/50 sm:p-12 lg:p-16"
                >
                    {/* Glow effect */}
                    <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-cyan-500/10 to-purple-600/10 opacity-50" />

                    <div className="relative z-10 flex flex-col items-center justify-center text-center">
                        {/* Icon */}
                        <div className="mx-auto mb-8 flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-500/30 to-purple-600/30">
                            <Play className="h-10 w-10 text-cyan-400" />
                        </div>

                        {/* Heading */}
                        <h3 className="mb-6 text-3xl font-bold text-white text-center sm:text-4xl">
                            Start Creating Now
                        </h3>

                        {/* Description */}
                        <p className="mx-auto mb-10 max-w-xl text-lg leading-relaxed text-center text-gray-300 py-10">
                            Access the full power of ZapCut directly in your browser.
                            Create professional video ads with AI assistance: no installation needed.
                        </p>

                        {/* Launch Button */}
                        <a
                            href="https://app.zapcut.video"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="group relative mx-auto flex items-center justify-center gap-3 rounded-xl bg-gradient-to-r from-cyan-500 to-purple-600 px-12 py-5 text-xl font-semibold text-white transition-all hover:scale-105 hover:shadow-[0_0_40px_rgba(6,182,212,0.6)]"
                        >
                            <Zap className="h-6 w-6" />
                            Launch ZapCut
                            <span className="absolute inset-0 rounded-xl bg-gradient-to-r from-cyan-400 to-purple-500 opacity-0 blur-xl transition-opacity group-hover:opacity-20" />
                        </a>

                        {/* Feature badges */}
                        <div className="mt-10 flex w-full flex-wrap items-center justify-center gap-4 py-10">
                            <div className="flex items-center justify-center gap-2 rounded-full bg-zinc-800/50 px-4 py-2">
                                <Sparkles className="h-4 w-4 text-cyan-400" />
                                <span className="text-sm text-gray-300">Web-Based</span>
                            </div>
                            <div className="flex items-center justify-center gap-2 rounded-full bg-zinc-800/50 px-4 py-2">
                                <Zap className="h-4 w-4 text-cyan-400" />
                                <span className="text-sm text-gray-300">Instant Access</span>
                            </div>
                            <div className="flex items-center justify-center gap-2 rounded-full bg-zinc-800/50 px-4 py-2">
                                <Play className="h-4 w-4 text-cyan-400" />
                                <span className="text-sm text-gray-300">No Download</span>
                            </div>
                        </div>
                    </div>

                    {/* Animated border glow */}
                    <div className="absolute inset-0 rounded-3xl opacity-100 transition-opacity duration-300">
                        <div className="absolute inset-0 rounded-3xl animate-pulse bg-gradient-to-r from-cyan-500/20 to-purple-600/20 blur-xl" />
                    </div>
                </motion.div>
            </div>

            {/* Decorative elements */}
            <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                className="absolute top-20 left-1/2 h-40 w-40 -translate-x-1/2 rounded-full bg-gradient-to-br from-cyan-500/10 to-purple-600/10 blur-3xl"
            />
            <motion.div
                animate={{ rotate: -360 }}
                transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
                className="absolute bottom-20 left-1/2 h-60 w-60 -translate-x-1/2 rounded-full bg-gradient-to-br from-purple-600/10 to-pink-500/10 blur-3xl"
            />
        </section>
    )
}

