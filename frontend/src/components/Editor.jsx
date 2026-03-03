import React, { useRef, useEffect } from 'react'
import EditorDefault, { useMonaco } from '@monaco-editor/react'

export default function Editor({ value, onChange, markers = [], theme = 'dark' }) {
  const editorRef = useRef(null)
  const monaco = useMonaco()

  function handleMount(editor) {
    editorRef.current = editor
  }

  useEffect(() => {
    if (!monaco || !editorRef.current) return
    const model = editorRef.current.getModel()
    if (!model) return
    try {
      monaco.editor.setModelMarkers(model, 'compiler', markers)
    } catch {}
  }, [markers, monaco])

  const monacoTheme = theme === 'light' ? 'vs' : 'vs-dark'

  return (
    <div className="editor-glass h-full">
      <EditorDefault
        height="100%"
        defaultLanguage="c"
        value={value}
        theme={monacoTheme}
        onMount={handleMount}
        onChange={v => onChange(v || '')}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          lineHeight: 22,
          fontFamily: "'JetBrains Mono', 'Cascadia Code', 'Fira Code', Consolas, monospace",
          fontLigatures: true,
          lineNumbers: 'on',
          renderLineHighlight: 'line',
          scrollBeyondLastLine: false,
          padding: { top: 20, bottom: 20 },
          bracketPairColorization: { enabled: true },
          smoothScrolling: true,
          cursorSmoothCaretAnimation: 'on',
          cursorBlinking: 'smooth',
          wordWrap: 'on',
          renderWhitespace: 'selection',
          guides: {
            bracketPairs: true,
            indentation: true,
          },
        }}
      />
    </div>
  )
}
