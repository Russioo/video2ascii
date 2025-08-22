import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import FFmpeg from '@ffmpeg/ffmpeg'

type CharsetName = 'detailed' | 'blocks' | 'simple'

interface ConversionJob {
	job_id: string
	filename: string
	status: string
	progress: number
	completed: boolean
	error: string | null
	has_output: boolean
}

const CHARSETS: Record<CharsetName, string> = {
  detailed: '@%#*+=-:. ',
  simple: '█▓▒░ ',
  blocks: '████▓▓▓▒▒▒░░░   '
}

const COLOR_SCHEMES = [
  { id: 'matrix', name: 'Matrix (green/black)', fg: '#00ff41', bg: '#000000' },
  { id: 'amber', name: 'Amber (amber/black)', fg: '#ffbf00', bg: '#000000' },
  { id: 'gray', name: 'Gray (light gray/black)', fg: '#cdd6f4', bg: '#000000' },
  { id: 'cyan', name: 'Cyan (cyan/black)', fg: '#00ffff', bg: '#000000' },
  { id: 'purple', name: 'Purple (magenta/black)', fg: '#c678dd', bg: '#000000' },
  { id: 'mono', name: 'Monochrome (white/black)', fg: '#ffffff', bg: '#000000' }
]

const PRESETS = [
	{ id: 'classic', label: 'Classic', asciiWidth: 80, contrast: 1.5, fontSize: 10, charset: 'detailed' as CharsetName, schemeId: 'matrix' },
	{ id: 'retro', label: 'Retro', asciiWidth: 60, contrast: 2.0, fontSize: 12, charset: 'blocks' as CharsetName, schemeId: 'amber' },
	{ id: 'highdef', label: 'High Detail', asciiWidth: 120, contrast: 1.2, fontSize: 8, charset: 'detailed' as CharsetName, schemeId: 'gray' }
]

export const App: React.FC = () => {
	const [selectedFile, setSelectedFile] = useState<File | null>(null)
	const [currentJob, setCurrentJob] = useState<ConversionJob | null>(null)
	const [isUploading, setIsUploading] = useState(false)
	const [isConverting, setIsConverting] = useState(false)
  const [clientStatus, setClientStatus] = useState<{ status: 'ok' | 'error'; audio_support: boolean; error?: string } | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
	const [dragActive, setDragActive] = useState(false)
	const dragCounterRef = useRef(0)
	const [splitPct, setSplitPct] = useState(50)
	const mediaRef = useRef<HTMLDivElement>(null)
  const [videoAspect, setVideoAspect] = useState(16 / 9)

	// Settings
	const [asciiWidth, setAsciiWidth] = useState(80)
	const [contrast, setContrast] = useState(1.5)
	const [fontSize, setFontSize] = useState(10)
	const [charset, setCharset] = useState<CharsetName>('detailed')
	const [includeAudio, setIncludeAudio] = useState(true)
  const [schemeId, setSchemeId] = useState('matrix')
  const [asciiFgColor, setAsciiFgColor] = useState('#00ff41')
  const [asciiBgColor, setAsciiBgColor] = useState('#000000')
  const [mp4Quality, setMp4Quality] = useState<'high' | 'medium' | 'low'>('high')

  // Refs for client-side rendering/recording
  const videoRef = useRef<HTMLVideoElement>(null)
  const srcCanvasRef = useRef<HTMLCanvasElement>(null) // to sample original frames
  const asciiCanvasRef = useRef<HTMLCanvasElement>(null) // to render ASCII frames
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const recordedChunksRef = useRef<BlobPart[]>([])
  const animationFrameRef = useRef<number | null>(null)
  const previewAnimationRef = useRef<number | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const ffmpegRef = useRef<any | null>(null)

  const canUseMediaRecorder = useMemo(() => typeof MediaRecorder !== 'undefined', [])

  // Initialize client mode status
	useEffect(() => {
    const audioSupport = canUseMediaRecorder && 'captureStream' in HTMLCanvasElement.prototype && 'captureStream' in HTMLVideoElement.prototype
    setClientStatus({ status: 'ok', audio_support: !!audioSupport })
  }, [canUseMediaRecorder])

  // Update colors when scheme changes
	useEffect(() => {
    const s = COLOR_SCHEMES.find(s => s.id === schemeId)
    if (s) { setAsciiFgColor(s.fg); setAsciiBgColor(s.bg) }
  }, [schemeId])

  // Revoke object URL when replaced
	useEffect(() => {
    return () => { if (previewUrl) URL.revokeObjectURL(previewUrl) }
  }, [previewUrl])

	const acceptFile = (file: File) => {
		setSelectedFile(file)
		setCurrentJob(null)
		if (previewUrl) URL.revokeObjectURL(previewUrl)
		const url = URL.createObjectURL(file)
		setPreviewUrl(url)
		if (videoRef.current) {
			const v = videoRef.current
			v.src = url
			v.muted = true
			v.playsInline = true
      const onMeta = () => setVideoAspect((v.videoWidth || 16) / (v.videoHeight || 9))
      v.addEventListener('loadedmetadata', onMeta, { once: true } as any)
			v.play().catch(() => {})
		}
		// eslint-disable-next-line no-console
		console.log('File selected:', file.name)
	}

	const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
		const file = event.target.files?.[0]
		if (file) acceptFile(file)
	}

	// Drag & drop handlers
	const onDragEnter = (e: React.DragEvent<HTMLDivElement>) => {
		e.preventDefault()
		dragCounterRef.current += 1
		setDragActive(true)
	}
	const onDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
		e.preventDefault()
		dragCounterRef.current -= 1
		if (dragCounterRef.current <= 0) setDragActive(false)
	}
	const onDragOver = (e: React.DragEvent<HTMLDivElement>) => {
		e.preventDefault()
	}
	const onDrop = (e: React.DragEvent<HTMLDivElement>) => {
		e.preventDefault()
		setDragActive(false)
		dragCounterRef.current = 0
		const files = e.dataTransfer.files
		if (files && files[0]) acceptFile(files[0])
	}

	// Preset apply
	const applyPreset = (id: string) => {
		const p = PRESETS.find(x => x.id === id)
		if (!p) return
		setAsciiWidth(p.asciiWidth)
		setContrast(p.contrast)
		setFontSize(p.fontSize)
		setCharset(p.charset)
		setSchemeId(p.schemeId)
	}

  // Utility: apply contrast to grayscale value
  const applyContrast = (gray: number, contrastFactor: number) => {
    const mean = 128
    const value = mean + (gray - mean) * contrastFactor
    return Math.max(0, Math.min(255, value))
  }

  // Convert one frame to ASCII lines calculated with precise char metrics
  const frameToAscii = (
    srcCtx: CanvasRenderingContext2D,
    sourceWidth: number,
    sourceHeight: number,
    targetAsciiWidth: number,
    charsetString: string,
    contrastFactor: number,
    charWidth: number,
    charHeight: number
  ): string[] => {
    // Compute height so that visual aspect (in pixels) matches the video
    const videoAspect = sourceWidth / Math.max(1, sourceHeight)
    const asciiPixelWidth = targetAsciiWidth * charWidth
    const asciiPixelHeight = asciiPixelWidth / videoAspect
    const targetAsciiHeight = Math.max(1, Math.round(asciiPixelHeight / charHeight))

    const tmp = document.createElement('canvas')
    tmp.width = targetAsciiWidth
    tmp.height = targetAsciiHeight
    const tmpCtx = tmp.getContext('2d', { willReadFrequently: true })!

    tmpCtx.drawImage(srcCtx.canvas, 0, 0, sourceWidth, sourceHeight, 0, 0, targetAsciiWidth, targetAsciiHeight)

    const imgData = tmpCtx.getImageData(0, 0, targetAsciiWidth, targetAsciiHeight)
    const { data } = imgData
    const lines: string[] = []
    const lastIndex = charsetString.length - 1

    for (let y = 0; y < targetAsciiHeight; y++) {
      const rowChars: string[] = []
      for (let x = 0; x < targetAsciiWidth; x++) {
        const idx = (y * targetAsciiWidth + x) * 4
        const r = data[idx]
        const g = data[idx + 1]
        const b = data[idx + 2]
        const gray = 0.299 * r + 0.587 * g + 0.114 * b
        const adjusted = applyContrast(gray, contrastFactor)
        const charIndex = Math.floor((adjusted / 255) * lastIndex)
        rowChars.push(charsetString[charIndex])
      }
      lines.push(rowChars.join(''))
    }
    return lines
  }

  const drawAsciiToCanvas = (
    asciiCtx: CanvasRenderingContext2D,
    asciiLines: string[],
    fontPx: number,
    fgColor: string,
    bgColor: string
  ) => {
    // Measure precise character cell metrics
    asciiCtx.font = `${fontPx}px monospace`
    const metrics = asciiCtx.measureText('M')
    const measuredCharWidth = metrics.width || fontPx * 0.6
    const measuredCharHeight = (metrics.actualBoundingBoxAscent && metrics.actualBoundingBoxDescent)
      ? Math.ceil(metrics.actualBoundingBoxAscent + metrics.actualBoundingBoxDescent)
      : Math.ceil(fontPx * 1.2)

    const maxWidth = asciiLines.reduce((m, l) => Math.max(m, l.length), 0)
    const width = Math.ceil(maxWidth * measuredCharWidth)
    const height = Math.ceil(asciiLines.length * measuredCharHeight)

    if (asciiCtx.canvas.width !== width || asciiCtx.canvas.height !== height) {
      asciiCtx.canvas.width = width
      asciiCtx.canvas.height = height
    }

    asciiCtx.fillStyle = bgColor
    asciiCtx.fillRect(0, 0, asciiCtx.canvas.width, asciiCtx.canvas.height)

    asciiCtx.font = `${fontPx}px monospace`
    asciiCtx.fillStyle = fgColor
    asciiCtx.textBaseline = 'top'

    let yPos = 0
    for (const line of asciiLines) {
      asciiCtx.fillText(line, 0, yPos)
      yPos += measuredCharHeight
    }
  }

  // Live preview loop when not converting
  useEffect(() => {
    const video = videoRef.current
    const srcCanvas = srcCanvasRef.current
    const asciiCanvas = asciiCanvasRef.current
    if (!video || !srcCanvas || !asciiCanvas) return
    if (!selectedFile || isConverting) return

    const srcCtx = srcCanvas.getContext('2d', { willReadFrequently: true })!
    const asciiCtx = asciiCanvas.getContext('2d', { willReadFrequently: true })!

    const loop = () => {
      if (video.videoWidth && video.videoHeight) {
        srcCanvas.width = video.videoWidth
        srcCanvas.height = video.videoHeight
        const ar = (video.videoWidth || 16) / (video.videoHeight || 9)
        if (Math.abs(ar - videoAspect) > 0.001) setVideoAspect(ar)

        srcCtx.drawImage(video, 0, 0, video.videoWidth, video.videoHeight)

        // Measure char sizes for consistent aspect
        asciiCtx.font = `${fontSize}px monospace`
        const m = asciiCtx.measureText('M')
        const cW = m.width || fontSize * 0.6
        const cH = (m.actualBoundingBoxAscent && m.actualBoundingBoxDescent)
          ? Math.ceil(m.actualBoundingBoxAscent + m.actualBoundingBoxDescent)
          : Math.ceil(fontSize * 1.2)

        const asciiLines = frameToAscii(
          srcCtx,
          video.videoWidth,
          video.videoHeight,
          asciiWidth,
          CHARSETS[charset],
          contrast,
          cW,
          cH
        )
        drawAsciiToCanvas(asciiCtx, asciiLines, fontSize, asciiFgColor, asciiBgColor)
      }
      previewAnimationRef.current = requestAnimationFrame(loop)
    }
    previewAnimationRef.current = requestAnimationFrame(loop)

    return () => {
      if (previewAnimationRef.current) cancelAnimationFrame(previewAnimationRef.current)
    }
  }, [selectedFile, isConverting, asciiWidth, contrast, fontSize, charset, asciiFgColor, asciiBgColor, videoAspect])

  const runClientConversion = useCallback(async () => {
    if (!selectedFile || !videoRef.current || !asciiCanvasRef.current || !srcCanvasRef.current) return
    if (!canUseMediaRecorder) {
      alert('Your browser does not support MediaRecorder. Try Chrome/Edge.')
      return
    }

    // Stop preview loop while converting
    if (previewAnimationRef.current) cancelAnimationFrame(previewAnimationRef.current)

    // Prepare job
    const filename = selectedFile.name
    setCurrentJob({
      job_id: 'local',
      filename,
      status: 'Preparing...',
      progress: 0,
      completed: false,
      error: null,
      has_output: false
    })

			setIsUploading(false)
			setIsConverting(true)

    const video = videoRef.current
    const srcCanvas = srcCanvasRef.current
    const srcCtx = srcCanvas.getContext('2d', { willReadFrequently: true })!
    const asciiCanvas = asciiCanvasRef.current
    const asciiCtx = asciiCanvas.getContext('2d', { willReadFrequently: true })!

    // Load video
    const fileUrl = previewUrl ?? URL.createObjectURL(selectedFile)
    video.src = fileUrl
    video.muted = !includeAudio
    video.playsInline = true

    await new Promise<void>((resolve, reject) => {
      const onLoaded = () => resolve()
      const onError = () => reject(new Error('Could not load video'))
      video.addEventListener('loadedmetadata', onLoaded, { once: true })
      video.addEventListener('error', onError, { once: true })
    })

    const duration = Math.max(0.001, video.duration || 0)
    const sourceWidth = video.videoWidth
    const sourceHeight = video.videoHeight

    // Prepare source canvas to hold original frames for sampling
    srcCanvas.width = sourceWidth
    srcCanvas.height = sourceHeight

    console.log(`Video: ${sourceWidth}x${sourceHeight}, duration: ${duration.toFixed(2)}s`)

    // Prepare recording stream from ASCII canvas
    const fps = 30
    const canvasStream = asciiCanvas.captureStream(fps)
    // Try to attach audio track from the playing video
    let mixedStream = new MediaStream([canvasStream.getVideoTracks()[0]])
    try {
      if (includeAudio && clientStatus?.audio_support) {
        const audioStream = (video as any).captureStream?.() as MediaStream | undefined
        const audioTrack = audioStream?.getAudioTracks()[0]
        if (audioTrack) {
          mixedStream.addTrack(audioTrack)
          console.log('Audio: enabled (MediaStream)')
				} else {
          console.log('Audio: track not found in source')
        }
      } else if (!includeAudio) {
        console.log('Audio: disabled by user')
      }
    } catch (e) {
      console.log('Audio: failed to attach, continuing without audio')
    }

    // Prepare MediaRecorder
    recordedChunksRef.current = []
    const mimeCandidates = [
      'video/webm;codecs=vp9,opus',
      'video/webm;codecs=vp8,opus',
      'video/webm'
    ]
    const mimeType = mimeCandidates.find(type => MediaRecorder.isTypeSupported(type)) || ''
    const recorder = new MediaRecorder(mixedStream, mimeType ? { mimeType } : undefined)
    mediaRecorderRef.current = recorder

    recorder.ondataavailable = (ev) => {
      if (ev.data && ev.data.size > 0) recordedChunksRef.current.push(ev.data)
    }
    recorder.onstop = () => {
      const blob = new Blob(recordedChunksRef.current, { type: mimeType || 'video/webm' })
			const url = URL.createObjectURL(blob)
      setCurrentJob(prev => prev ? { ...prev, completed: true, has_output: true, status: 'Done!' } : prev)
      // Auto-download
			const a = document.createElement('a')
			a.href = url
      a.download = `ascii_${filename.replace(/\.[^.]+$/, '')}.webm`
			document.body.appendChild(a)
			a.click()
			document.body.removeChild(a)
			URL.revokeObjectURL(url)
      if (!previewUrl) URL.revokeObjectURL(fileUrl)
      setIsConverting(false)
      console.log('Download started')
    }

    // Draw loop: convert current frame to ASCII and render
    const charsetString = CHARSETS[charset]
    const step = () => {
      if (video.paused || video.ended) return
      srcCtx.drawImage(video, 0, 0, sourceWidth, sourceHeight)

      // measure char metrics
      asciiCtx.font = `${fontSize}px monospace`
      const m = asciiCtx.measureText('M')
      const cW = m.width || fontSize * 0.6
      const cH = (m.actualBoundingBoxAscent && m.actualBoundingBoxDescent)
        ? Math.ceil(m.actualBoundingBoxAscent + m.actualBoundingBoxDescent)
        : Math.ceil(fontSize * 10)

      const asciiLines = frameToAscii(
        srcCtx,
        sourceWidth,
        sourceHeight,
        asciiWidth,
        charsetString,
        contrast,
        cW,
        cH
      )
      drawAsciiToCanvas(asciiCtx, asciiLines, fontSize, asciiFgColor, asciiBgColor)
      const progress = (video.currentTime / duration) * 100
      setCurrentJob(prev => prev ? { ...prev, progress, status: `Converting... ${progress.toFixed(1)}%` } : prev)
      animationFrameRef.current = requestAnimationFrame(step)
    }

    // Start playback + recording
    try {
      recorder.start(1000)
      await video.play()
      console.log('Conversion started')
      animationFrameRef.current = requestAnimationFrame(step)
    } catch (e: any) {
      setCurrentJob(prev => prev ? { ...prev, error: e?.message || String(e), completed: true, status: 'Error' } : prev)
      setIsConverting(false)
      console.log(`Error: ${e?.message || e}`)
      return
    }

    const onEnded = () => {
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current)
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop()
      }
      video.removeEventListener('ended', onEnded)
    }
    video.addEventListener('ended', onEnded)
  }, [selectedFile, includeAudio, asciiWidth, contrast, fontSize, charset, canUseMediaRecorder, clientStatus, previewUrl, asciiFgColor, asciiBgColor])

  const startClientConversion = async () => {
    if (!selectedFile) return
    await runClientConversion()
  }

  const downloadResult = async () => {
    // No-op: auto-download on stop
	}

	const resetConverter = () => {
		setSelectedFile(null)
		setCurrentJob(null)
		setIsUploading(false)
		setIsConverting(false)
    if (previewUrl) { URL.revokeObjectURL(previewUrl); setPreviewUrl(null) }
    if (previewAnimationRef.current) cancelAnimationFrame(previewAnimationRef.current)
    if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current)
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
	}

	const getStatusColor = () => {
		if (!currentJob) return '#00ff41'
		if (currentJob.error) return '#ff4444'
		if (currentJob.completed) return '#44ff44'
		return '#ffaa00'
	}

	const getStatusMessage = () => {
    if (!clientStatus) return 'Initializing client mode...'
    if (clientStatus.status === 'error') return '[ERR] Client error'
		if (!selectedFile) return 'Select a video file to begin'
    if (isUploading) return 'Preparing...'
		if (isConverting && currentJob) return currentJob.status
		if (currentJob?.completed && !currentJob.error) return '[OK] Conversion complete'
		if (currentJob?.error) return `[ERR] ${currentJob.error}`
		return 'Ready to convert'
	}

	// Split handle interactions
	const onMouseDownHandle = (e: React.MouseEvent<HTMLDivElement>) => {
		e.preventDefault()
		const container = mediaRef.current
		if (!container) return
		const rect = container.getBoundingClientRect()
		const onMove = (ev: MouseEvent) => {
			const x = ev.clientX - rect.left
			const pct = Math.max(15, Math.min(85, (x / rect.width) * 100))
			setSplitPct(pct)
		}
		const onUp = () => {
			window.removeEventListener('mousemove', onMove)
			window.removeEventListener('mouseup', onUp)
		}
		window.addEventListener('mousemove', onMove)
		window.addEventListener('mouseup', onUp)
	}

	const ensureFFmpegLoaded = useCallback(async () => {
		if (!ffmpegRef.current) {
			const ffmpeg = FFmpeg.createFFmpeg({ log: false })
			await ffmpeg.load()
			ffmpegRef.current = ffmpeg
		}
		return ffmpegRef.current
	}, [])

	return (
		<div className="container">
			<div className="header">
				<div>
					<div className="brand">[ASCII] Video Converter</div>
					<div className="subtitle">Client-side conversion in your browser</div>
				</div>
			</div>

			{/* Quick Presets */}
			<div className="panel" style={{ marginBottom: 16 }}>
				<div className="presetRow" style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
					{PRESETS.map((p) => (
						<button key={p.id} className="primary" onClick={() => applyPreset(p.id)}>{'[>]'} {p.label}</button>
					))}
				</div>
			</div>

			{/* File Selection + Dropzone */}
			<div className="panel" style={{ marginBottom: 16 }}>
				<div className="controls">
					<div className="control">
						<label>Select Video File</label>
						<div className="fileRow">
						<input 
								ref={fileInputRef}
								className="fileInputHidden"
							type="file" 
							accept="video/*" 
							onChange={handleFileSelect}
							disabled={isUploading || isConverting}
						/>
							<button
								type="button"
								className="primary fileButton"
								onClick={() => fileInputRef.current?.click()}
								disabled={isUploading || isConverting}
							>
								{'[*]'} Choose file
							</button>
							<span className="filenameMeta">{selectedFile ? `${selectedFile.name} (${(selectedFile.size/1024/1024).toFixed(2)} MB)` : 'No file selected'}</span>
						</div>
					</div>
				</div>

				<div
					className={`dropzone${dragActive ? ' dragging' : ''}`}
					onDragEnter={onDragEnter}
					onDragLeave={onDragLeave}
					onDragOver={onDragOver}
					onDrop={onDrop}
					style={{ marginTop: 12 }}
				>
					<div className="dropzone-inner">Drop video here or click Choose file</div>
				</div>
			</div>

			{/* Live Preview with adjustable split */}
			<div className="panel" style={{ marginBottom: 16 }}>
				<div ref={mediaRef} className="media" style={{ display: 'grid', gridTemplateColumns: `${splitPct}% 8px ${100 - splitPct}%`, alignItems: 'stretch' }}>
					<div>
						<div className="stack"><strong>Original</strong><span className="time">preview</span></div>
						<div className="frame" style={{ aspectRatio: videoAspect as any }}>
							<video ref={videoRef} controls style={{ width:'100%', height:'100%' }} />
						</div>
					</div>
					<div className="splitHandle" onMouseDown={onMouseDownHandle} title="Drag to resize" />
					<div>
						<div className="stack"><strong>ASCII Preview</strong><span className="time">live</span></div>
						<div className="frame" style={{ aspectRatio: videoAspect as any }}>
							<canvas ref={asciiCanvasRef} className="asciiCanvas" style={{ width:'100%', height:'100%' }} />
							</div>
					</div>
				</div>
			</div>

			{/* Settings */}
			<div className="panel" style={{ marginBottom: 16 }}>
				<div className="controls">
					<div className="control">
						<label>Quality</label>
						<input 
							type="range" 
							min={30} 
							max={120} 
							value={asciiWidth} 
							onChange={(e) => setAsciiWidth(Number(e.target.value))}
							disabled={isUploading || isConverting}
						/>
						<div className="value">{asciiWidth}</div>
					</div>
					<div className="control">
						<label>Contrast</label>
						<input 
							type="range" 
							min={0.5} 
							max={3} 
							step={0.1} 
							value={contrast} 
							onChange={(e) => setContrast(Number(e.target.value))}
							disabled={isUploading || isConverting}
						/>
						<div className="value">{contrast.toFixed(1)}</div>
					</div>
					<div className="control">
						<label>Font Size</label>
						<input 
							type="range" 
							min={6} 
							max={16} 
							value={fontSize} 
							onChange={(e) => setFontSize(Number(e.target.value))}
							disabled={isUploading || isConverting}
						/>
						<div className="value">{fontSize}</div>
					</div>
					<div className="control" style={{ gridColumn: 'span 2' as any }}>
						<label>Color Scheme</label>
						<div className="chips">
							{COLOR_SCHEMES.map(s => (
								<button key={s.id} type="button" className={`chip${schemeId === s.id ? ' active' : ''}`} onClick={() => setSchemeId(s.id)}>
									<span className="dot" style={{ background: s.fg }} /> {s.id}
								</button>
							))}
						</div>
					</div>
					<div className="control">
						<label>Foreground</label>
						<input type="color" value={asciiFgColor} onChange={(e) => setAsciiFgColor(e.target.value)} disabled={isUploading || isConverting} />
						<div className="value">{asciiFgColor}</div>
					</div>
					<div className="control">
						<label>Background</label>
						<input type="color" value={asciiBgColor} onChange={(e) => setAsciiBgColor(e.target.value)} disabled={isUploading || isConverting} />
						<div className="value">{asciiBgColor}</div>
					</div>
					<div className="control">
						<label>MP4 Quality</label>
						<select value={mp4Quality} onChange={(e) => setMp4Quality(e.target.value as any)} disabled={isUploading || isConverting}>
							<option value="high">high</option>
							<option value="medium">medium</option>
							<option value="low">low</option>
						</select>
					</div>
					<div className="control">
						<label>
							<input 
								type="checkbox" 
								checked={includeAudio && !!clientStatus?.audio_support} 
								onChange={(e) => setIncludeAudio(e.target.checked)}
								disabled={isUploading || isConverting || !clientStatus?.audio_support}
								style={{ marginRight: 8 }}
							/>
							Include Original Audio
						</label>
						{!clientStatus?.audio_support && (
							<div style={{ fontSize: '0.8em', color: '#ff4444', marginTop: 4 }}>
								Audio capture not available
							</div>
						)}
					</div>
				</div>
			</div>

			{/* Status */}
			<div className="panel" style={{ marginBottom: 16, textAlign: 'center' }}>
				<div style={{ color: getStatusColor(), fontWeight: 'bold', fontSize: '1.1em', marginBottom: 10 }}>
					{getStatusMessage()}
				</div>
				{currentJob && (
					<div className="progress-container" style={{ margin: '10px 0' }}>
						<div className="progress-bar" style={{ 
							width: '100%', 
							height: '20px', 
							backgroundColor: '#333', 
							borderRadius: '10px',
							overflow: 'hidden'
						}}>
							<div style={{
								width: `${currentJob.progress}%`,
								height: '100%',
								backgroundColor: currentJob.error ? '#ff4444' : '#00ff41',
								transition: 'width 0.3s ease'
							}} />
						</div>
						<div style={{ marginTop: 5, fontSize: '0.9em' }}>
							{currentJob.progress.toFixed(1)}%
						</div>
					</div>
				)}
			</div>

			{/* Action Buttons */}
			<div className="panel" style={{ marginBottom: 16, textAlign: 'center' }}>
				{!currentJob && (
					<button 
						className="primary" 
						onClick={startClientConversion}
						disabled={!selectedFile || !clientStatus || clientStatus.status !== 'ok' || isUploading}
					>
						{isUploading ? '[..] Preparing...' : '[>] Start ASCII Conversion'}
					</button>
				)}
				
				{currentJob && !currentJob.completed && (
					<div style={{ color: '#ffaa00' }}>
						Converting... This may take a few minutes
					</div>
				)}
				
				{currentJob?.completed && !currentJob.error && (
					<div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
						<button className="primary" onClick={downloadResult}>
							{'[*]'} Download again
						</button>
						<button onClick={resetConverter}>
							{'[/]'} Convert another
						</button>
					</div>
				)}
				
				{currentJob?.error && (
					<button onClick={resetConverter}>
						{'[/]'} Try again
					</button>
				)}
			</div>

      {/* hidden processing canvas for sampling */}
      <canvas ref={srcCanvasRef} style={{ display: 'none' }} />

			<div className="footer">ASCII video conversion in-browser (serverless)</div>
		</div>
	)
}