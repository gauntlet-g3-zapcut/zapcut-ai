export function EditorFrame() {
  // Point to the built Electron app in app/dist
  // The dist folder contains index.html with relative asset paths
  const editorEntryUrl = "/editor-app/index.html"

  return (
    <iframe
      src={editorEntryUrl}
      title="Zapcut Editor"
      className="h-full w-full border-0"
      allow="clipboard-read; clipboard-write; camera; microphone"
      allowFullScreen
    />
  )
}

