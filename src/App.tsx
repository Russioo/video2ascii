import React, { useCallback, useEffect, useState, useRef } from 'react'

type CharsetName = 'detailed' | 'blocks' | 'simple'

interface ConversionJob {
	job_id: string
	filename: string
	status: string
	progress: number
	completed: boolean
	error: string | null
	logs: string[]
	has_output: boolean
}

const API_BASE = 'http://localhost:5000/api'

export const App: React.FC = () => {
	const [selectedFile, setSelectedFile] = useState<File | null>(null)
	const [currentJob, setCurrentJob] = useState<ConversionJob | null>(null)
	const [isUploading, setIsUploading] = useState(false)
	const [isConverting, setIsConverting] = useState(false)
	const [backendStatus, setBackendStatus] = useState<any>(null)
	const logRef = useRef<HTMLDivElement>(null)

	// Settings
	const [asciiWidth, setAsciiWidth] = useState(80)
	const [contrast, setContrast] = useState(1.5)
	const [fontSize, setFontSize] = useState(10)
	const [charset, setCharset] = useState<CharsetName>('detailed')
	const [includeAudio, setIncludeAudio] = useState(true)

	// Check backend status on load
	useEffect(() => {
		checkBackendStatus()
	}, [])

	// Poll job status while converting
	useEffect(() => {
		if (currentJob && !currentJob.completed && isConverting) {
			const interval = setInterval(() => {
				fetchJobStatus(currentJob.job_id)
			}, 1000)
			return () => clearInterval(interval)
		}
	}, [currentJob, isConverting])

	// Auto-scroll logs
	useEffect(() => {
		if (logRef.current) {
			logRef.current.scrollTop = logRef.current.scrollHeight
		}
	}, [currentJob?.logs])

	const checkBackendStatus = async () => {
		try {
			const response = await fetch(`${API_BASE}/health`)
			const status = await response.json()
			setBackendStatus(status)
			console.log('🔗 Backend status:', status)
		} catch (error) {
			console.error('❌ Backend ikke tilgængelig:', error)
			setBackendStatus({ status: 'error', error: 'Backend ikke tilgængelig' })
		}
	}

	const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
		const file = event.target.files?.[0]
		if (file) {
			setSelectedFile(file)
			setCurrentJob(null)
			console.log('📁 Fil valgt:', file.name)
		}
	}

	const uploadAndConvert = async () => {
		if (!selectedFile) return

		setIsUploading(true)
		console.log('⬆️ Uploader fil...')

		try {
			// Step 1: Upload file
			const formData = new FormData()
			formData.append('video', selectedFile)

			const uploadResponse = await fetch(`${API_BASE}/upload`, {
				method: 'POST',
				body: formData
			})

			if (!uploadResponse.ok) {
				throw new Error('Upload failed')
			}

			const uploadResult = await uploadResponse.json()
			console.log('✅ Upload successful:', uploadResult)

			// Step 2: Start conversion
			const conversionSettings = {
				ascii_width: asciiWidth,
				contrast: contrast,
				font_size: fontSize,
				charset: charset,
				include_audio: includeAudio && backendStatus?.audio_support
			}

			const convertResponse = await fetch(`${API_BASE}/convert`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					job_id: uploadResult.job_id,
					settings: conversionSettings
				})
			})

			if (!convertResponse.ok) {
				throw new Error('Conversion start failed')
			}

			const convertResult = await convertResponse.json()
			console.log('🎬 Conversion started:', convertResult)

			setIsUploading(false)
			setIsConverting(true)

			// Start polling for status
			await fetchJobStatus(uploadResult.job_id)

		} catch (error) {
			console.error('❌ Error:', error)
			setIsUploading(false)
			alert(`Fejl: ${error}`)
		}
	}

	const fetchJobStatus = async (jobId: string) => {
		try {
			const response = await fetch(`${API_BASE}/status/${jobId}`)
			if (!response.ok) {
				throw new Error('Status fetch failed')
			}

			const job: ConversionJob = await response.json()
			setCurrentJob(job)

			console.log(`📊 Job status: ${job.status} (${job.progress.toFixed(1)}%)`)

			if (job.completed) {
				setIsConverting(false)
				if (job.error) {
					console.error('❌ Conversion failed:', job.error)
				} else {
					console.log('✅ Conversion completed!')
				}
			}
		} catch (error) {
			console.error('❌ Status fetch error:', error)
		}
	}

	const downloadResult = async () => {
		if (!currentJob?.job_id) return

		try {
			const response = await fetch(`${API_BASE}/download/${currentJob.job_id}`)
			if (!response.ok) {
				throw new Error('Download failed')
			}

			const blob = await response.blob()
			const url = URL.createObjectURL(blob)
			const a = document.createElement('a')
			a.href = url
			a.download = `ascii_${currentJob.filename}`
			document.body.appendChild(a)
			a.click()
			document.body.removeChild(a)
			URL.revokeObjectURL(url)

			console.log('💾 Download completed!')
		} catch (error) {
			console.error('❌ Download error:', error)
			alert(`Download fejl: ${error}`)
		}
	}

	const resetConverter = () => {
		setSelectedFile(null)
		setCurrentJob(null)
		setIsUploading(false)
		setIsConverting(false)
	}

	const getStatusColor = () => {
		if (!currentJob) return '#00ff41'
		if (currentJob.error) return '#ff4444'
		if (currentJob.completed) return '#44ff44'
		return '#ffaa00'
	}

	const getStatusMessage = () => {
		if (!backendStatus) return 'Forbinder til backend...'
		if (backendStatus.status === 'error') return '❌ Backend ikke tilgængelig'
		if (!selectedFile) return 'Vælg en videofil for at starte'
		if (isUploading) return 'Uploader fil...'
		if (isConverting && currentJob) return currentJob.status
		if (currentJob?.completed && !currentJob.error) return '✅ Konvertering færdig!'
		if (currentJob?.error) return `❌ Fejl: ${currentJob.error}`
		return 'Klar til konvertering'
	}

	return (
		<div className="container">
			<div className="header">
				<div>
					<div className="brand">🐍 Python ASCII Video Converter</div>
					<div className="subtitle">Server-baseret video til ASCII konvertering med lyd support</div>
				</div>
			</div>

			{/* Backend Status */}
			<div className="panel" style={{ marginBottom: 16, backgroundColor: backendStatus?.status === 'ok' ? 'rgba(0,255,65,0.1)' : 'rgba(255,68,68,0.1)' }}>
				<div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
					<strong>Backend Status:</strong>
					{backendStatus?.status === 'ok' ? (
						<>
							<span style={{ color: '#44ff44' }}>✅ Online</span>
							<span style={{ marginLeft: 20 }}>
								Audio Support: {backendStatus.audio_support ? 
									<span style={{ color: '#44ff44' }}>✅ {backendStatus.audio_method}</span> : 
									<span style={{ color: '#ff4444' }}>❌ {backendStatus.audio_error}</span>
								}
							</span>
						</>
					) : (
						<span style={{ color: '#ff4444' }}>❌ Offline</span>
					)}
				</div>
			</div>

			{/* File Selection */}
			<div className="panel" style={{ marginBottom: 16 }}>
				<div className="controls">
					<div className="control">
						<label>Vælg Videofil</label>
						<input 
							type="file" 
							accept="video/*" 
							onChange={handleFileSelect}
							disabled={isUploading || isConverting}
						/>
						{selectedFile && (
							<div style={{ marginTop: 8, fontSize: '0.9em', color: '#888' }}>
								Valgt: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
							</div>
						)}
					</div>
				</div>
			</div>

			{/* Settings */}
			<div className="panel" style={{ marginBottom: 16 }}>
				<div className="controls">
					<div className="control">
						<label>ASCII Bredde</label>
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
						<label>Kontrast</label>
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
						<label>Font Størrelse</label>
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
					<div className="control">
						<label>Karaktersæt</label>
						<select 
							value={charset} 
							onChange={(e) => setCharset(e.target.value as CharsetName)}
							disabled={isUploading || isConverting}
						>
							<option value="detailed">Detaljeret (@%#*+=-:. )</option>
							<option value="simple">Simpel (█▓▒░ )</option>
							<option value="blocks">Blokke (████▓▓▓▒▒▒░░░)</option>
						</select>
					</div>
					<div className="control">
						<label>
							<input 
								type="checkbox" 
								checked={includeAudio && backendStatus?.audio_support} 
								onChange={(e) => setIncludeAudio(e.target.checked)}
								disabled={isUploading || isConverting || !backendStatus?.audio_support}
								style={{ marginRight: 8 }}
							/>
							Inkluder Original Lyd
						</label>
						{!backendStatus?.audio_support && (
							<div style={{ fontSize: '0.8em', color: '#ff4444', marginTop: 4 }}>
								Lyd support ikke tilgængelig
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
						onClick={uploadAndConvert}
						disabled={!selectedFile || !backendStatus || backendStatus.status !== 'ok' || isUploading}
					>
						{isUploading ? '⏳ Uploader...' : '🎬 Start ASCII Konvertering'}
					</button>
				)}
				
				{currentJob && !currentJob.completed && (
					<div style={{ color: '#ffaa00' }}>
						⏳ Konverterer... Dette kan tage flere minutter
					</div>
				)}
				
				{currentJob?.completed && !currentJob.error && (
					<div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
						<button className="primary" onClick={downloadResult}>
							💾 Download ASCII Video
						</button>
						<button onClick={resetConverter}>
							🔄 Konverter Ny Video
						</button>
					</div>
				)}
				
				{currentJob?.error && (
					<button onClick={resetConverter}>
						🔄 Prøv Igen
					</button>
				)}
			</div>

			{/* Logs */}
			{currentJob?.logs && (
				<div className="panel">
					<h3>Konvertering Log</h3>
					<div 
						ref={logRef}
						style={{
							backgroundColor: '#000',
							color: '#00ff41',
							fontFamily: 'monospace',
							fontSize: '0.85em',
							padding: 15,
							borderRadius: 5,
							height: 200,
							overflowY: 'auto',
							border: '1px solid #333'
						}}
					>
						{currentJob.logs.map((log, index) => (
							<div key={index}>{log}</div>
						))}
					</div>
				</div>
			)}

			<div className="footer">
				Python-baseret ASCII video konvertering med moviepy/ffmpeg support!
			</div>
		</div>
	)
}