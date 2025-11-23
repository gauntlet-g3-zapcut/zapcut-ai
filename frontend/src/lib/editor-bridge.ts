const PROJECT_STORAGE_KEY = "zapcut-project-storage"
const STORAGE_VERSION = 0
const DEFAULT_VIDEO_WIDTH = 1920
const DEFAULT_VIDEO_HEIGHT = 1080
const SECONDARY_VIDEO_WIDTH = 480
const SECONDARY_VIDEO_HEIGHT = 270
const AUDIO_PANEL_WIDTH = 200
const AUDIO_PANEL_HEIGHT = 150
const FALLBACK_VIDEO_DURATION_MS = 5000
const FALLBACK_AUDIO_DURATION_MS = 5000
const MIN_CLIP_DURATION_MS = 500

type EditorAssetType = "video" | "audio" | "image"

export interface EditorVideoSource {
    url: string
    name: string
    order?: number
    sceneNumber?: number
}

export interface EditorAudioSource {
    url: string
    name: string
}

export interface EditorProjectInput {
    projectName: string
    videos: EditorVideoSource[]
    audio?: EditorAudioSource | null
    includeFinalComposite?: {
        url: string
        name?: string
    } | null
}

interface EditorAsset {
    id: string
    type: EditorAssetType
    name: string
    url: string
    duration: number
    metadata: {
        width: number
        height: number
    }
    thumbnailUrl?: string
    fileSize?: number
}

interface EditorTrack {
    id: string
    name: string
    type: "video" | "audio"
    clips: string[]
    locked: boolean
    visible: boolean
}

interface EditorClip {
    id: string
    assetId: string
    trackId: string
    startMs: number
    endMs: number
    trimStartMs: number
    trimEndMs: number
    zIndex: number
}

interface EditorCanvasNode {
    id: string
    clipId: string
    x: number
    y: number
    width: number
    height: number
    rotation: number
    opacity: number
}

type EditorPersistedState = {
    state: {
        id: string
        projectName: string
        assets: EditorAsset[]
        tracks: EditorTrack[]
        clips: Record<string, EditorClip>
        canvasNodes: Record<string, EditorCanvasNode>
        selectedClipIds: string[]
    }
    version: number
}

interface MediaMetadata {
    durationMs: number
    width: number
    height: number
}

const isBrowser = () => typeof window !== "undefined" && typeof document !== "undefined"

const createId = (prefix: string) => {
    const base =
        typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
            ? crypto.randomUUID()
            : `${Math.random().toString(36).slice(2)}-${Date.now()}`

    return `${prefix}-${base}`
}

const ensureDuration = (value: number, fallback: number) => {
    if (!Number.isFinite(value) || value <= 0) {
        return Math.max(fallback, MIN_CLIP_DURATION_MS)
    }

    return Math.max(Math.round(value), MIN_CLIP_DURATION_MS)
}

const loadVideoMetadata = async (url: string): Promise<MediaMetadata> => {
    if (!isBrowser()) {
        return {
            durationMs: FALLBACK_VIDEO_DURATION_MS,
            width: DEFAULT_VIDEO_WIDTH,
            height: DEFAULT_VIDEO_HEIGHT
        }
    }

    return new Promise((resolve) => {
        const video = document.createElement("video")
        video.preload = "metadata"
        video.crossOrigin = "anonymous"

        const cleanup = () => {
            video.removeAttribute("src")
            video.load()
        }

        const handleResolve = () => {
            const durationMs = ensureDuration(video.duration * 1000, FALLBACK_VIDEO_DURATION_MS)
            const width = video.videoWidth || DEFAULT_VIDEO_WIDTH
            const height = video.videoHeight || DEFAULT_VIDEO_HEIGHT
            cleanup()

            resolve({
                durationMs,
                width,
                height
            })
        }

        const handleError = () => {
            cleanup()
            resolve({
                durationMs: FALLBACK_VIDEO_DURATION_MS,
                width: DEFAULT_VIDEO_WIDTH,
                height: DEFAULT_VIDEO_HEIGHT
            })
        }

        video.onloadedmetadata = handleResolve
        video.onerror = handleError

        // Start loading after handlers are registered
        video.src = url
    })
}

const loadAudioMetadata = async (url: string): Promise<{ durationMs: number }> => {
    if (!isBrowser()) {
        return { durationMs: FALLBACK_AUDIO_DURATION_MS }
    }

    return new Promise((resolve) => {
        const audio = document.createElement("audio")
        audio.preload = "metadata"
        audio.crossOrigin = "anonymous"

        const cleanup = () => {
            audio.removeAttribute("src")
            audio.load()
        }

        const handleResolve = () => {
            const durationMs = ensureDuration(audio.duration * 1000, FALLBACK_AUDIO_DURATION_MS)
            cleanup()
            resolve({ durationMs })
        }

        const handleError = () => {
            cleanup()
            resolve({ durationMs: FALLBACK_AUDIO_DURATION_MS })
        }

        audio.onloadedmetadata = handleResolve
        audio.onerror = handleError

        audio.src = url
    })
}

const createBaseTracks = (): EditorTrack[] => [
    { id: "track-1", name: "Video Track 1", type: "video", clips: [], locked: false, visible: true },
    { id: "track-2", name: "Video Track 2", type: "video", clips: [], locked: false, visible: true },
    { id: "track-3", name: "Audio Track 1", type: "audio", clips: [], locked: false, visible: true }
]

const createCanvasNode = (
    track: EditorTrack,
    clipId: string,
    metadata: MediaMetadata,
    isPrimaryVideoTrack: boolean
): EditorCanvasNode => {
    const nodeId = createId("canvas")

    if (track.type === "video" && isPrimaryVideoTrack) {
        return {
            id: nodeId,
            clipId,
            x: 0,
            y: 0,
            width: metadata.width || DEFAULT_VIDEO_WIDTH,
            height: metadata.height || DEFAULT_VIDEO_HEIGHT,
            rotation: 0,
            opacity: 1
        }
    }

    if (track.type === "video") {
        let width = SECONDARY_VIDEO_WIDTH
        let height = SECONDARY_VIDEO_HEIGHT

        if (metadata.width && metadata.height) {
            const assetAspect = metadata.width / metadata.height
            const frameAspect = SECONDARY_VIDEO_WIDTH / SECONDARY_VIDEO_HEIGHT

            if (assetAspect > frameAspect) {
                width = SECONDARY_VIDEO_WIDTH
                height = Math.round(width / assetAspect)
            } else {
                height = SECONDARY_VIDEO_HEIGHT
                width = Math.round(height * assetAspect)
            }
        }

        return {
            id: nodeId,
            clipId,
            x: DEFAULT_VIDEO_WIDTH - width - 40,
            y: DEFAULT_VIDEO_HEIGHT - height - 40,
            width,
            height,
            rotation: 0,
            opacity: 1
        }
    }

    return {
        id: nodeId,
        clipId,
        x: 0,
        y: 0,
        width: AUDIO_PANEL_WIDTH,
        height: AUDIO_PANEL_HEIGHT,
        rotation: 0,
        opacity: 1
    }
}

export const buildEditorProjectSnapshot = async (
    input: EditorProjectInput
): Promise<EditorPersistedState> => {
    if (!input.videos.length) {
        throw new Error("No generated videos were provided for the editor project.")
    }

    const sortedVideos = [...input.videos].sort((a, b) => {
        const aOrder = a.order ?? a.sceneNumber ?? 0
        const bOrder = b.order ?? b.sceneNumber ?? 0
        return aOrder - bOrder
    })

    const tracks = createBaseTracks()
    const primaryVideoTrack = tracks.find((track) => track.type === "video")!
    const audioTrack = tracks.find((track) => track.type === "audio")!

    const assets: EditorAsset[] = []
    const clips: Record<string, EditorClip> = {}
    const canvasNodes: Record<string, EditorCanvasNode> = {}

    let timelineCursor = 0

    for (const video of sortedVideos) {
        const metadata = await loadVideoMetadata(video.url)
        const duration = ensureDuration(metadata.durationMs, FALLBACK_VIDEO_DURATION_MS)
        const assetId = createId("asset")
        const clipId = createId("clip")

        assets.push({
            id: assetId,
            type: "video",
            name: video.name,
            url: video.url,
            duration,
            metadata: {
                width: metadata.width || DEFAULT_VIDEO_WIDTH,
                height: metadata.height || DEFAULT_VIDEO_HEIGHT
            }
        })

        clips[clipId] = {
            id: clipId,
            assetId,
            trackId: primaryVideoTrack.id,
            startMs: timelineCursor,
            endMs: timelineCursor + duration,
            trimStartMs: 0,
            trimEndMs: duration,
            zIndex: 0
        }

        const canvasNode = createCanvasNode(primaryVideoTrack, clipId, metadata, true)
        canvasNodes[canvasNode.id] = canvasNode

        primaryVideoTrack.clips.push(clipId)
        timelineCursor += duration
    }

    const totalVideoDuration = Math.max(timelineCursor, MIN_CLIP_DURATION_MS)

    if (input.audio?.url) {
        const audioMetadata = await loadAudioMetadata(input.audio.url)
        const audioDuration = Math.max(audioMetadata.durationMs, totalVideoDuration)
        const assetId = createId("asset")
        const clipId = createId("clip")

        assets.push({
            id: assetId,
            type: "audio",
            name: input.audio.name,
            url: input.audio.url,
            duration: audioDuration,
            metadata: {
                width: 0,
                height: 0
            }
        })

        clips[clipId] = {
            id: clipId,
            assetId,
            trackId: audioTrack.id,
            startMs: 0,
            endMs: audioDuration,
            trimStartMs: 0,
            trimEndMs: audioDuration,
            zIndex: 0
        }

        const canvasNode = createCanvasNode(audioTrack, clipId, {
            durationMs: audioDuration,
            width: 0,
            height: 0
        }, false)

        canvasNodes[canvasNode.id] = canvasNode
        audioTrack.clips.push(clipId)
    }

    if (input.includeFinalComposite?.url) {
        const compositeMetadata = await loadVideoMetadata(input.includeFinalComposite.url)
        const assetId = createId("asset")

        assets.push({
            id: assetId,
            type: "video",
            name: input.includeFinalComposite.name ?? "Final Composite",
            url: input.includeFinalComposite.url,
            duration: ensureDuration(compositeMetadata.durationMs, totalVideoDuration),
            metadata: {
                width: compositeMetadata.width || DEFAULT_VIDEO_WIDTH,
                height: compositeMetadata.height || DEFAULT_VIDEO_HEIGHT
            }
        })
    }

    return {
        state: {
            id: createId("project"),
            projectName: input.projectName,
            assets,
            tracks,
            clips,
            canvasNodes,
            selectedClipIds: []
        },
        version: STORAGE_VERSION
    }
}

export const persistEditorProject = (snapshot: EditorPersistedState) => {
    if (!isBrowser()) {
        console.warn("[editorBridge] Attempted to persist editor project outside the browser environment.")
        return
    }

    try {
        window.localStorage.setItem(PROJECT_STORAGE_KEY, JSON.stringify(snapshot))
    } catch (error) {
        console.error("[editorBridge] Failed to persist editor project snapshot:", error)
        throw error
    }
}

export const prepareEditorProject = async (input: EditorProjectInput) => {
    const snapshot = await buildEditorProjectSnapshot(input)
    persistEditorProject(snapshot)
    return snapshot
}


