import fs from 'node:fs'
import fsp from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawnSync } from 'node:child_process'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const projectRoot = path.resolve(__dirname, '..')
const editorRoot = path.resolve(projectRoot, 'app')
const editorDist = path.join(editorRoot, 'dist')
const publicRoot = path.join(projectRoot, 'public')
const targetDir = path.join(publicRoot, 'editor-app')

const log = (message) => console.log(`[editor-sync] ${message}`)
const warn = (message) => console.warn(`[editor-sync] ${message}`)

const hasFile = (filePath) => fs.existsSync(filePath)

const ensureEditorProject = () => {
  if (!hasFile(path.join(editorRoot, 'package.json'))) {
    warn('Editor project not found. Skipping asset sync.')
    process.exit(0)
  }
}

const run = (command, args, options = {}) => {
  const result = spawnSync(command, args, {
    stdio: 'inherit',
    ...options,
  })

  if (result.status !== 0) {
    throw new Error(`Command failed: ${command} ${args.join(' ')}`)
  }
}

const hasEditorBuild = () => hasFile(path.join(editorDist, 'index.html'))

const copyDir = async (src, dest) => {
  await fsp.mkdir(dest, { recursive: true })
  const entries = await fsp.readdir(src, { withFileTypes: true })

  for (const entry of entries) {
    const srcPath = path.join(src, entry.name)
    const destPath = path.join(dest, entry.name)

    if (entry.isDirectory()) {
      await copyDir(srcPath, destPath)
    } else if (entry.isSymbolicLink()) {
      const linkTarget = await fsp.readlink(srcPath)
      await fsp.symlink(linkTarget, destPath)
    } else {
      await fsp.copyFile(srcPath, destPath)
    }
  }
}

const removeDir = async (dir) => {
  await fsp.rm(dir, { recursive: true, force: true })
}

const prepareEditorAssets = () => {
  const forceRebuild = process.env.EDITOR_FORCE_REBUILD === '1'
  const skipInstall = process.env.EDITOR_SKIP_INSTALL === '1'

  if (!forceRebuild && hasFile(editorDist) && hasEditorBuild()) {
    log('Existing editor build detected. Skipping rebuild.')
    return
  }

  if (!skipInstall && !hasFile(path.join(editorRoot, 'node_modules'))) {
    log('Installing editor dependencies...')
    run('npm', ['install'], { cwd: editorRoot })
  }

  log('Building editor web bundle...')
  run('npm', ['run', 'build:web'], { cwd: editorRoot })
}

const main = async () => {
  ensureEditorProject()

  prepareEditorAssets()

  if (!hasFile(editorDist) || !hasEditorBuild()) {
    throw new Error('Editor build artifacts not found after build step.')
  }

  log('Syncing editor assets into frontend/public/editor-app...')
  await removeDir(targetDir)
  await copyDir(editorDist, targetDir)
  log('Editor assets synced successfully.')
}

main().catch((error) => {
  console.error('[editor-sync] Failed to prepare editor assets.')
  console.error(error)
  process.exit(1)
})

