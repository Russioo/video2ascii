#!/usr/bin/env python3
"""
ASCII Video Converter Backend
Flask API til at konvertere videoer til ASCII med din eksisterende kode
"""

import os
import sys
import uuid
import json
import time
import threading
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Try to import moviepy for audio, fallback to ffmpeg
try:
    from moviepy.editor import VideoFileClip, ImageSequenceClip
    AUDIO_SUPPORT = True
    AUDIO_METHOD = "moviepy"
    AUDIO_ERROR = None
except ImportError as e:
    # Try to use ffmpeg directly
    import subprocess
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            AUDIO_SUPPORT = True
            AUDIO_METHOD = "ffmpeg"
            AUDIO_ERROR = None
        else:
            AUDIO_SUPPORT = False
            AUDIO_METHOD = None
            AUDIO_ERROR = "FFmpeg not found"
    except FileNotFoundError:
        AUDIO_SUPPORT = False
        AUDIO_METHOD = None
        AUDIO_ERROR = "Neither moviepy nor ffmpeg available"
except Exception as e:
    AUDIO_SUPPORT = False
    AUDIO_METHOD = None
    AUDIO_ERROR = f"Unexpected error: {str(e)}"

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = Path('./uploads')
OUTPUT_FOLDER = Path('./outputs')
UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

# Store conversion jobs
conversion_jobs = {}

class ASCIIVideoConverter:
    def __init__(self):
        # ASCII character sets - samme som dit script
        self.charsets = {
            'detailed': '@%#*+=-:. ',
            'simple': '█▓▒░ ',
            'blocks': '████▓▓▓▒▒▒░░░   '
        }
        
    def log_message(self, job_id, message):
        """Log message for specific job"""
        if job_id in conversion_jobs:
            conversion_jobs[job_id]['logs'].append(f"[{time.strftime('%H:%M:%S')}] {message}")
            print(f"[{job_id}] {message}")
        
    def update_progress(self, job_id, progress, status):
        """Update job progress"""
        if job_id in conversion_jobs:
            conversion_jobs[job_id]['progress'] = progress
            conversion_jobs[job_id]['status'] = status
            
    def frame_to_ascii(self, frame, width, charset, contrast):
        """Convert a video frame to ASCII art - samme som dit script"""
        # Resize frame
        height, width_orig = frame.shape[:2]
        aspect_ratio = height / width_orig
        ascii_height = int(width * aspect_ratio * 0.45)
        
        frame_resized = cv2.resize(frame, (width, ascii_height))
        
        # Convert to grayscale
        if len(frame_resized.shape) == 3:
            gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame_resized
            
        # Apply contrast
        gray = cv2.convertScaleAbs(gray, alpha=contrast, beta=0)
        
        # Convert to ASCII
        ascii_lines = []
        for y in range(ascii_height):
            row = []
            for x in range(width):
                pixel_value = gray[y, x]
                char_index = int((pixel_value / 255) * (len(charset) - 1))
                row.append(charset[char_index])
            ascii_lines.append(''.join(row))
            
        return ascii_lines
        
    def ascii_to_image(self, ascii_lines, font_size):
        """Convert ASCII text to image - samme som dit script"""
        # Calculate image size
        max_width = max(len(line) for line in ascii_lines)
        char_width = font_size * 0.6  # Estimate character width
        char_height = font_size * 1.2  # Line height
        
        img_width = int(max_width * char_width) + 20
        img_height = int(len(ascii_lines) * char_height) + 20
        
        # Create image
        img = Image.new('RGB', (img_width, img_height), color='black')
        draw = ImageDraw.Draw(img)
        
        # Try to load font
        try:
            # Try different font names
            for font_name in ["consola.ttf", "cour.ttf", "arial.ttf"]:
                try:
                    font = ImageFont.truetype(font_name, font_size)
                    break
                except:
                    continue
            else:
                font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Draw ASCII text
        y_pos = 10
        for line in ascii_lines:
            draw.text((10, y_pos), line, fill='lime', font=font)
            y_pos += int(char_height)
            
        return np.array(img)
        
    def convert_video(self, job_id, input_path, settings):
        """Convert video to ASCII - baseret på dit script"""
        try:
            self.log_message(job_id, f"Starting conversion of: {Path(input_path).name}")
            
            # Get settings
            ascii_width = settings.get('ascii_width', 80)
            contrast = settings.get('contrast', 1.5)
            font_size = settings.get('font_size', 10)
            charset = self.charsets[settings.get('charset', 'detailed')]
            include_audio = settings.get('include_audio', False) and AUDIO_SUPPORT
            quality = settings.get('quality', 'high')  # 'high' | 'medium' | 'low'
            
            self.log_message(job_id, f"Settings - Width: {ascii_width}, Contrast: {contrast}, Font: {font_size}")
            self.log_message(job_id, f"Output - MP4 Quality: {quality}")
            if include_audio and AUDIO_SUPPORT:
                self.log_message(job_id, "Audio: ENABLED - will include original audio")
            else:
                self.log_message(job_id, "Audio: DISABLED - video only")
            
            # Open video
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                raise Exception("Could not open video file")
                
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            self.log_message(job_id, f"Video info - Frames: {total_frames}, FPS: {fps:.1f}")
            
            if total_frames == 0:
                raise Exception("Video has no frames")
                
            # Create output filename
            input_file = Path(input_path)
            temp_video_path = OUTPUT_FOLDER / f"{job_id}_temp.mp4"
            final_output_path = OUTPUT_FOLDER / f"{job_id}_ascii.mp4"
            
            self.log_message(job_id, f"Output will be: {final_output_path.name}")
            
            # Get first frame to determine output size
            ret, frame = cap.read()
            if not ret:
                raise Exception("Could not read first frame")
                
            ascii_lines = self.frame_to_ascii(frame, ascii_width, charset, contrast)
            ascii_img = self.ascii_to_image(ascii_lines, font_size)
            output_height, output_width = ascii_img.shape[:2]
            
            self.log_message(job_id, f"Output video size: {output_width}x{output_height}")
            
            # Setup video writer (temporary file without audio)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(temp_video_path), fourcc, fps, 
                                (output_width, output_height))
            
            if not out.isOpened():
                raise Exception("Could not create output video file")
            
            # Reset video to beginning
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            frame_count = 0
            
            # Generate ASCII video frames
            self.log_message(job_id, "Generating ASCII video frames...")
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Convert frame to ASCII
                ascii_lines = self.frame_to_ascii(frame, ascii_width, charset, contrast)
                ascii_img = self.ascii_to_image(ascii_lines, font_size)
                
                # Convert RGB to BGR for OpenCV
                ascii_img_bgr = cv2.cvtColor(ascii_img, cv2.COLOR_RGB2BGR)
                
                # Write frame
                out.write(ascii_img_bgr)
                
                frame_count += 1
                progress = (frame_count / total_frames) * 50  # First 50% for video generation
                self.update_progress(job_id, progress, f"Generating ASCII frames {frame_count}/{total_frames}")
                
                if frame_count % 30 == 0:  # Log every 30 frames
                    self.log_message(job_id, f"Generated {frame_count}/{total_frames} ASCII frames ({progress:.1f}%)")
                    
            # Cleanup video capture and writer
            cap.release()
            out.release()
            
            self.log_message(job_id, f"ASCII video frames generated: {temp_video_path.name}")
            
            # Add audio if requested and supported
            if include_audio and AUDIO_SUPPORT:
                self.log_message(job_id, f"Adding original audio using {AUDIO_METHOD}...")
                self.update_progress(job_id, 75, "Adding audio to ASCII video...")
                
                try:
                    if AUDIO_METHOD == "moviepy":
                        # Use moviepy method
                        original_clip = VideoFileClip(input_path)
                        ascii_clip = VideoFileClip(str(temp_video_path))
                        
                        if original_clip.audio is not None:
                            ascii_with_audio = ascii_clip.set_audio(original_clip.audio)
                            ascii_with_audio.write_videofile(
                                str(final_output_path),
                                codec='libx264',
                                audio_codec='aac',
                                verbose=False,
                                logger=None
                            )
                            ascii_with_audio.close()
                            self.log_message(job_id, "✅ Audio successfully added using moviepy!")
                        else:
                            temp_video_path.rename(final_output_path)
                            self.log_message(job_id, "ℹ Original video has no audio")
                            
                        original_clip.close()
                        ascii_clip.close()
                        
                    elif AUDIO_METHOD == "ffmpeg":
                        # Use ffmpeg directly with quality settings
                        self.log_message(job_id, "Using ffmpeg to create MP4 with audio and quality settings...")

                        # Map requested quality to CRF/preset
                        if quality == 'high':
                            video_settings = ['-c:v', 'libx264', '-crf', '18', '-preset', 'medium']
                        elif quality == 'medium':
                            video_settings = ['-c:v', 'libx264', '-crf', '23', '-preset', 'fast']
                        else:
                            video_settings = ['-c:v', 'libx264', '-crf', '28', '-preset', 'ultrafast']

                        ffmpeg_cmd = [
                            'ffmpeg', '-y',
                            '-i', str(temp_video_path),
                            '-i', input_path,
                        ] + video_settings + [
                            '-c:a', 'aac',
                            '-b:a', '128k',
                            '-map', '0:v:0',
                            '-map', '1:a:0',
                            '-shortest',
                            '-movflags', '+faststart',
                            str(final_output_path)
                        ]
                        
                        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                        
                        if result.returncode == 0:
                            self.log_message(job_id, "✅ Audio successfully added using ffmpeg!")
                        else:
                            # Try simpler command if complex one fails
                            self.log_message(job_id, f"⚠ FFmpeg quality pipeline failed, trying simple mapping...")
                            simple_cmd = [
                                'ffmpeg', '-y',
                                '-i', str(temp_video_path),
                                '-i', input_path,
                                '-c:v', 'libx264',
                                '-c:a', 'aac',
                                '-map', '0:v:0',
                                '-map', '1:a:0',
                                '-shortest',
                                str(final_output_path)
                            ]
                            result2 = subprocess.run(simple_cmd, capture_output=True, text=True)
                            if result2.returncode == 0:
                                self.log_message(job_id, "✅ MP4 with audio created using simple ffmpeg!")
                            else:
                                self.log_message(job_id, f"⚠ FFmpeg audio pipeline failed: {result.stderr}")
                                self.log_message(job_id, "Saving video without audio...")
                                temp_video_path.rename(final_output_path)
                    
                    # Remove temporary file
                    if temp_video_path.exists():
                        temp_video_path.unlink()
                        
                except Exception as audio_error:
                    self.log_message(job_id, f"⚠ Audio processing failed: {audio_error}")
                    self.log_message(job_id, "Saving video without audio...")
                    if temp_video_path.exists():
                        temp_video_path.rename(final_output_path)
            else:
                # No audio requested. Re-encode to MP4 with requested quality if ffmpeg is available
                try:
                    import subprocess as _sp
                    self.log_message(job_id, "Re-encoding ASCII MP4 without audio using ffmpeg...")
                    if quality == 'high':
                        video_settings = ['-c:v', 'libx264', '-crf', '18', '-preset', 'medium']
                    elif quality == 'medium':
                        video_settings = ['-c:v', 'libx264', '-crf', '23', '-preset', 'fast']
                    else:
                        video_settings = ['-c:v', 'libx264', '-crf', '28', '-preset', 'ultrafast']

                    cmd = ['ffmpeg', '-y', '-i', str(temp_video_path)] + video_settings + ['-movflags', '+faststart', str(final_output_path)]
                    result = _sp.run(cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        self.log_message(job_id, f"⚠ ffmpeg re-encode failed: {result.stderr}")
                        temp_video_path.rename(final_output_path)
                except Exception as _e:
                    self.log_message(job_id, f"⚠ ffmpeg not available for re-encode: {_e}")
                    temp_video_path.rename(final_output_path)
                if not include_audio:
                    self.log_message(job_id, "Audio not requested - video only")
                
            self.update_progress(job_id, 100, "Conversion completed!")
            conversion_jobs[job_id]['output_file'] = str(final_output_path)
            conversion_jobs[job_id]['completed'] = True
            self.log_message(job_id, f"SUCCESS: ASCII video created!")
            self.log_message(job_id, f"File saved as: {final_output_path}")
            
        except Exception as e:
            error_msg = f"Conversion failed: {str(e)}"
            self.log_message(job_id, f"ERROR: {error_msg}")
            conversion_jobs[job_id]['error'] = error_msg
            conversion_jobs[job_id]['completed'] = True
            
            # Cleanup temp file if it exists
            try:
                if temp_video_path.exists():
                    temp_video_path.unlink()
            except:
                pass

# Create converter instance
converter = ASCIIVideoConverter()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'audio_support': AUDIO_SUPPORT,
        'audio_method': AUDIO_METHOD,
        'audio_error': AUDIO_ERROR
    })

@app.route('/api/upload', methods=['POST'])
def upload_video():
    """Upload video file"""
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    file_path = UPLOAD_FOLDER / f"{job_id}_{filename}"
    file.save(file_path)
    
    # Create job record
    conversion_jobs[job_id] = {
        'id': job_id,
        'filename': filename,
        'file_path': str(file_path),
        'status': 'uploaded',
        'progress': 0,
        'logs': [f"[{time.strftime('%H:%M:%S')}] File uploaded: {filename}"],
        'completed': False,
        'output_file': None,
        'error': None
    }
    
    return jsonify({
        'job_id': job_id,
        'filename': filename,
        'message': 'File uploaded successfully'
    })

@app.route('/api/convert', methods=['POST'])
def start_conversion():
    """Start ASCII video conversion"""
    data = request.get_json()
    job_id = data.get('job_id')
    settings = data.get('settings', {})
    
    if not job_id or job_id not in conversion_jobs:
        return jsonify({'error': 'Invalid job ID'}), 400
    
    if conversion_jobs[job_id]['completed']:
        return jsonify({'error': 'Job already completed'}), 400
    
    # Start conversion in background thread
    def run_conversion():
        converter.convert_video(job_id, conversion_jobs[job_id]['file_path'], settings)
    
    thread = threading.Thread(target=run_conversion)
    thread.daemon = True
    thread.start()
    
    conversion_jobs[job_id]['status'] = 'converting'
    
    return jsonify({
        'message': 'Conversion started',
        'job_id': job_id
    })

@app.route('/api/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get conversion job status"""
    if job_id not in conversion_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = conversion_jobs[job_id]
    return jsonify({
        'job_id': job_id,
        'filename': job['filename'],
        'status': job['status'],
        'progress': job['progress'],
        'completed': job['completed'],
        'error': job['error'],
        'logs': job['logs'][-10:],  # Return last 10 log entries
        'has_output': job['output_file'] is not None
    })

@app.route('/api/download/<job_id>', methods=['GET'])
def download_result(job_id):
    """Download converted ASCII video"""
    if job_id not in conversion_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = conversion_jobs[job_id]
    if not job['completed'] or not job['output_file']:
        return jsonify({'error': 'Conversion not completed or no output file'}), 400
    
    output_path = Path(job['output_file'])
    if not output_path.exists():
        return jsonify({'error': 'Output file not found'}), 404
    
    return send_file(
        output_path,
        as_attachment=True,
        download_name=f"ascii_{job['filename']}"
    )

@app.route('/api/logs/<job_id>', methods=['GET'])
def get_job_logs(job_id):
    """Get full logs for a job"""
    if job_id not in conversion_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify({
        'job_id': job_id,
        'logs': conversion_jobs[job_id]['logs']
    })

if __name__ == '__main__':
    print("🎬 ASCII Video Converter Backend")
    print("=" * 50)
    print(f"Audio support: {'✅ Enabled' if AUDIO_SUPPORT else '❌ Disabled'}")
    if AUDIO_SUPPORT:
        print(f"Audio method: {AUDIO_METHOD}")
    else:
        print(f"Audio error: {AUDIO_ERROR}")
    print("Starting Flask server...")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

