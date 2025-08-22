#!/usr/bin/env python3
"""
ASCII Video Converter - Med lyd support
Konverterer videofiler til ASCII art videoer med original lyd
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import sys
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading

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

class ASCIIVideoConverter:
    def __init__(self):
        # ASCII character sets
        self.charsets = {
            'detailed': '@%#*+=-:. ',
            'simple': '█▓▒░ ',
            'blocks': '████▓▓▓▒▒▒░░░   '
        }
        
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the GUI"""
        self.root = tk.Tk()
        self.root.title("ASCII Video Converter")
        self.root.geometry("600x500")
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎬 ASCII Video Converter 🎬", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="Select Video File", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.file_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_var, width=50)
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_btn = ttk.Button(file_frame, text="Browse", command=self.browse_file)
        browse_btn.pack(side=tk.RIGHT)
        
        # Settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 20))
        
        # ASCII Width
        width_frame = ttk.Frame(settings_frame)
        width_frame.pack(fill=tk.X, pady=5)
        ttk.Label(width_frame, text="ASCII Width:").pack(side=tk.LEFT)
        self.width_var = tk.IntVar(value=80)
        self.width_scale = ttk.Scale(width_frame, from_=30, to=120, variable=self.width_var, 
                                    orient=tk.HORIZONTAL, length=200)
        self.width_scale.pack(side=tk.LEFT, padx=10)
        self.width_label = ttk.Label(width_frame, text="80")
        self.width_label.pack(side=tk.LEFT)
        self.width_scale.configure(command=self.update_width_label)
        
        # Contrast
        contrast_frame = ttk.Frame(settings_frame)
        contrast_frame.pack(fill=tk.X, pady=5)
        ttk.Label(contrast_frame, text="Contrast:").pack(side=tk.LEFT)
        self.contrast_var = tk.DoubleVar(value=1.5)
        self.contrast_scale = ttk.Scale(contrast_frame, from_=0.5, to=3.0, variable=self.contrast_var,
                                       orient=tk.HORIZONTAL, length=200)
        self.contrast_scale.pack(side=tk.LEFT, padx=10)
        self.contrast_label = ttk.Label(contrast_frame, text="1.5")
        self.contrast_label.pack(side=tk.LEFT)
        self.contrast_scale.configure(command=self.update_contrast_label)
        
        # Font Size
        font_frame = ttk.Frame(settings_frame)
        font_frame.pack(fill=tk.X, pady=5)
        ttk.Label(font_frame, text="Font Size:").pack(side=tk.LEFT)
        self.font_var = tk.IntVar(value=10)
        self.font_scale = ttk.Scale(font_frame, from_=6, to=16, variable=self.font_var,
                                   orient=tk.HORIZONTAL, length=200)
        self.font_scale.pack(side=tk.LEFT, padx=10)
        self.font_label = ttk.Label(font_frame, text="10")
        self.font_label.pack(side=tk.LEFT)
        self.font_scale.configure(command=self.update_font_label)
        
        # Character Set
        charset_frame = ttk.Frame(settings_frame)
        charset_frame.pack(fill=tk.X, pady=5)
        ttk.Label(charset_frame, text="Character Set:").pack(side=tk.LEFT)
        self.charset_var = tk.StringVar(value='detailed')
        charset_combo = ttk.Combobox(charset_frame, textvariable=self.charset_var, 
                                    values=list(self.charsets.keys()), state="readonly")
        charset_combo.pack(side=tk.LEFT, padx=10)
        charset_combo.set('detailed')
        
        # Video Quality
        quality_frame = ttk.Frame(settings_frame)
        quality_frame.pack(fill=tk.X, pady=5)
        ttk.Label(quality_frame, text="MP4 Quality:").pack(side=tk.LEFT)
        self.quality_var = tk.StringVar(value='high')
        quality_combo = ttk.Combobox(quality_frame, textvariable=self.quality_var, 
                                    values=['high', 'medium', 'low'], state="readonly")
        quality_combo.pack(side=tk.LEFT, padx=10)
        quality_combo.set('high')
        
        # Audio option
        audio_frame = ttk.Frame(settings_frame)
        audio_frame.pack(fill=tk.X, pady=5)
        self.include_audio = tk.BooleanVar(value=AUDIO_SUPPORT)
        audio_check = ttk.Checkbutton(audio_frame, text="Include Original Audio", 
                                     variable=self.include_audio)
        audio_check.pack(side=tk.LEFT)
        
        if not AUDIO_SUPPORT:
            audio_check.config(state='disabled')
            if AUDIO_ERROR:
                audio_info = ttk.Label(audio_frame, text=f"(Install moviepy or ffmpeg for audio)", 
                                      foreground='red', font=('Arial', 8))
            else:
                audio_info = ttk.Label(audio_frame, text="(Install moviepy or ffmpeg for audio)", 
                                      foreground='red', font=('Arial', 8))
            audio_info.pack(side=tk.LEFT, padx=10)
        else:
            # Show which method is being used
            method_info = ttk.Label(audio_frame, text=f"(using {AUDIO_METHOD})", 
                                   foreground='green', font=('Arial', 8))
            method_info.pack(side=tk.LEFT, padx=10)
        
        # Convert button - ALWAYS enabled
        self.convert_btn = ttk.Button(main_frame, text="🎬 Convert to ASCII Video", 
                                     command=self.start_conversion)
        self.convert_btn.pack(pady=20)
        
        # Progress frame
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          maximum=100)
        self.progress_bar.pack(fill=tk.X)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready to convert video")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_label.pack(pady=5)
        
        # Result label
        self.result_var = tk.StringVar()
        self.result_label = ttk.Label(main_frame, textvariable=self.result_var, 
                                     foreground='green', font=('Arial', 10, 'bold'))
        self.result_label.pack(pady=5)
        
        # Log text
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.log_text = tk.Text(log_frame, height=8, width=60, bg='black', fg='lime', 
                               font=('Courier', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        self.log("ASCII Video Converter ready!")
        self.log("📹 Output format: High-quality MP4")
        if AUDIO_SUPPORT:
            self.log(f"✅ Audio support enabled using {AUDIO_METHOD}")
        else:
            self.log("⚠ Audio support disabled")
            if AUDIO_ERROR:
                self.log(f"   Audio error: {AUDIO_ERROR}")
            self.log("   Install moviepy OR ffmpeg for audio support")
        self.log("1. Select a video file")
        self.log("2. Adjust settings & MP4 quality")
        self.log("3. Enable audio if available")
        self.log("4. Click Convert")
        
    def log(self, message):
        """Add message to log"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def update_width_label(self, value):
        self.width_label.config(text=str(int(float(value))))
        
    def update_contrast_label(self, value):
        self.contrast_label.config(text=f"{float(value):.1f}")
        
    def update_font_label(self, value):
        self.font_label.config(text=str(int(float(value))))
        
    def browse_file(self):
        """Browse for video file"""
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.m4v"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.file_var.set(file_path)
            self.log(f"Selected: {os.path.basename(file_path)}")
            
    def frame_to_ascii(self, frame, width, charset, contrast):
        """Convert a video frame to ASCII art"""
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
        """Convert ASCII text to image"""
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
        
    def convert_video(self):
        """Convert video to ASCII"""
        input_path = self.file_var.get().strip()
        
        if not input_path:
            messagebox.showerror("Error", "Please select a video file first!")
            self.log("ERROR: No file selected")
            return
            
        if not os.path.exists(input_path):
            messagebox.showerror("Error", f"File not found: {input_path}")
            self.log(f"ERROR: File not found: {input_path}")
            return
            
        try:
            self.log(f"Starting conversion of: {os.path.basename(input_path)}")
            
            # Get settings
            ascii_width = int(self.width_var.get())
            contrast = float(self.contrast_var.get())
            font_size = int(self.font_var.get())
            charset = self.charsets[self.charset_var.get()]
            include_audio = self.include_audio.get()
            quality = self.quality_var.get()
            
            self.log(f"Settings - Width: {ascii_width}, Contrast: {contrast}, Font: {font_size}")
            self.log(f"Output - MP4 Quality: {quality}")
            if include_audio and AUDIO_SUPPORT:
                self.log("Audio: ENABLED - will include original audio")
            else:
                self.log("Audio: DISABLED - video only")
            
            # Open video
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                raise Exception("Could not open video file")
                
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            self.log(f"Video info - Frames: {total_frames}, FPS: {fps:.1f}")
            
            if total_frames == 0:
                raise Exception("Video has no frames")
                
            # Create output filename
            input_file = Path(input_path)
            temp_video_path = input_file.parent / f"{input_file.stem}_ascii_temp.mp4"
            final_output_path = input_file.parent / f"{input_file.stem}_ascii.mp4"
            
            self.log(f"Output will be: {final_output_path.name}")
            
            # Get first frame to determine output size
            ret, frame = cap.read()
            if not ret:
                raise Exception("Could not read first frame")
                
            ascii_lines = self.frame_to_ascii(frame, ascii_width, charset, contrast)
            ascii_img = self.ascii_to_image(ascii_lines, font_size)
            output_height, output_width = ascii_img.shape[:2]
            
            self.log(f"Output video size: {output_width}x{output_height}")
            
            # Setup video writer with automatic codec fallback
            self.log(f"Creating MP4 video with {quality} quality...")
            
            # Choose FPS based on quality
            if quality == 'high':
                actual_fps = fps
            elif quality == 'medium':
                actual_fps = min(fps, 25)
            else:  # low
                actual_fps = min(fps, 20)
            
            # Try different codecs in order of preference
            codecs_to_try = [
                ('mp4v', 'MP4V-ES'),  # Most compatible on Windows
                ('XVID', 'XVID'),     # Good fallback
                ('MJPG', 'MJPG'),     # Always works
            ]
            
            out = None
            used_codec = None
            
            for codec_fourcc, codec_name in codecs_to_try:
                try:
                    fourcc = cv2.VideoWriter_fourcc(*codec_fourcc)
                    out = cv2.VideoWriter(str(temp_video_path), fourcc, actual_fps, 
                                        (output_width, output_height))
                    
                    if out.isOpened():
                        used_codec = codec_name
                        self.log(f"✅ Using {codec_name} codec for MP4 video")
                        break
                    else:
                        out.release()
                        out = None
                        self.log(f"⚠ {codec_name} codec failed, trying next...")
                        
                except Exception as e:
                    self.log(f"⚠ {codec_name} codec error: {e}")
                    if out:
                        out.release()
                        out = None
            
            if not out or not out.isOpened():
                raise Exception("Could not create MP4 video file - no compatible codec found")
                
            self.log(f"MP4 video writer ready: {output_width}x{output_height} @ {actual_fps:.1f} FPS using {used_codec}")
            
            # Reset video to beginning
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            frame_count = 0
            
            # Generate ASCII video frames
            self.log("Generating ASCII video frames...")
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
                self.progress_var.set(progress)
                self.status_var.set(f"Generating ASCII frames {frame_count}/{total_frames} ({progress:.1f}%)")
                
                if frame_count % 30 == 0:  # Log every 30 frames
                    self.log(f"Generated {frame_count}/{total_frames} ASCII frames ({progress:.1f}%)")
                    
                self.root.update()
                
            # Cleanup video capture and writer
            cap.release()
            out.release()
            
            self.log(f"ASCII video frames generated: {temp_video_path.name}")
            
            # Add audio if requested and supported
            if include_audio and AUDIO_SUPPORT:
                self.log(f"Adding original audio using {AUDIO_METHOD}...")
                self.status_var.set("Adding audio to ASCII video...")
                self.progress_var.set(75)
                self.root.update()
                
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
                            self.log("✅ Audio successfully added using moviepy!")
                        else:
                            temp_video_path.rename(final_output_path)
                            self.log("ℹ Original video has no audio")
                            
                        original_clip.close()
                        ascii_clip.close()
                        
                    elif AUDIO_METHOD == "ffmpeg":
                        # Use ffmpeg directly with high-quality MP4 settings
                        self.log("Using ffmpeg to create high-quality MP4 with audio...")
                        
                        # Quality settings based on user choice
                        if quality == 'high':
                            video_settings = ['-c:v', 'libx264', '-crf', '18', '-preset', 'medium']
                        elif quality == 'medium':
                            video_settings = ['-c:v', 'libx264', '-crf', '23', '-preset', 'fast']
                        else:  # low
                            video_settings = ['-c:v', 'libx264', '-crf', '28', '-preset', 'ultrafast']
                        
                        ffmpeg_cmd = [
                            'ffmpeg', '-y',  # -y to overwrite output
                            '-i', str(temp_video_path),  # ASCII video input
                            '-i', input_path,  # Original video with audio
                        ] + video_settings + [
                            '-c:a', 'aac',   # AAC audio codec
                            '-b:a', '128k',  # Audio bitrate
                            '-map', '0:v:0',  # Take video from first input (ASCII)
                            '-map', '1:a:0',  # Take audio from second input (original)
                            '-shortest',  # Match shortest stream
                            '-movflags', '+faststart',  # Optimize for web playback
                            str(final_output_path)
                        ]
                        
                        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                        
                        if result.returncode == 0:
                            self.log("✅ High-quality MP4 with audio created using ffmpeg!")
                        else:
                            # Try simpler command if complex one fails
                            self.log(f"⚠ Advanced FFmpeg failed, trying simple method...")
                            simple_cmd = [
                                'ffmpeg', '-y',
                                '-i', str(temp_video_path),
                                '-i', input_path,
                                '-c:v', 'libx264',  # Force H.264 in ffmpeg
                                '-c:a', 'aac',
                                '-map', '0:v:0',
                                '-map', '1:a:0',
                                '-shortest',
                                str(final_output_path)
                            ]
                            result = subprocess.run(simple_cmd, capture_output=True, text=True)
                            
                            if result.returncode == 0:
                                self.log("✅ MP4 with audio created using simple ffmpeg!")
                            else:
                                self.log(f"⚠ FFmpeg audio failed: {result.stderr}")
                                self.log("Saving video without audio...")
                                temp_video_path.rename(final_output_path)
                    
                    # Remove temporary file
                    if temp_video_path.exists():
                        temp_video_path.unlink()
                        
                except Exception as audio_error:
                    self.log(f"⚠ Audio processing failed: {audio_error}")
                    self.log("Saving video without audio...")
                    if temp_video_path.exists():
                        temp_video_path.rename(final_output_path)
            else:
                # No audio requested, just rename temp file
                temp_video_path.rename(final_output_path)
                if not include_audio:
                    self.log("Audio not requested - video only")
                
            self.progress_var.set(100)
            self.status_var.set("Conversion completed!")
            self.result_var.set(f"✅ ASCII video saved: {final_output_path.name}")
            self.log(f"SUCCESS: ASCII video created!")
            self.log(f"File saved as: {final_output_path}")
            
            # Show result message
            audio_msg = " with original audio" if (include_audio and AUDIO_SUPPORT) else ""
            quality_msg = f" ({quality} quality MP4)"
            messagebox.showinfo("Success", f"ASCII video created successfully{audio_msg}!\n\nSaved as: {final_output_path.name}{quality_msg}")
            
            # Show file info
            if final_output_path.exists():
                file_size = final_output_path.stat().st_size / (1024 * 1024)  # MB
                self.log(f"Final MP4 file size: {file_size:.1f} MB")
            
        except Exception as e:
            error_msg = f"Conversion failed: {str(e)}"
            self.log(f"ERROR: {error_msg}")
            messagebox.showerror("Error", error_msg)
            self.status_var.set("Conversion failed")
            
            # Cleanup temp file if it exists
            try:
                if 'temp_video_path' in locals() and temp_video_path.exists():
                    temp_video_path.unlink()
            except:
                pass
            
        finally:
            self.convert_btn.config(state='normal')
            
    def start_conversion(self):
        """Start conversion in separate thread"""
        if not self.file_var.get().strip():
            messagebox.showwarning("Warning", "Please select a video file first!")
            return
            
        self.convert_btn.config(state='disabled')
        self.progress_var.set(0)
        self.result_var.set("")
        
        # Run conversion in thread
        thread = threading.Thread(target=self.convert_video)
        thread.daemon = True
        thread.start()
        
    def run(self):
        """Run the application"""
        self.root.mainloop()

def main():
    """Main function"""
    print("🎬 ASCII Video Converter with Audio Support")
    print("=" * 50)
    
    # Check if running as script
    if len(sys.argv) > 1:
        # Command line mode
        input_file = sys.argv[1]
        if not os.path.exists(input_file):
            print(f"❌ File not found: {input_file}")
            return
            
        print(f"Converting: {input_file}")
        # Simple conversion with default settings
        
    else:
        # GUI mode
        try:
            import cv2
            import PIL
            print("✅ Core packages found (opencv-python, pillow)")
        except ImportError as e:
            print(f"❌ Missing required package: {e}")
            print("\nInstall required packages with:")
            print("pip install opencv-python pillow")
            input("Press Enter to exit...")
            return
        
        if AUDIO_SUPPORT:
            print(f"✅ Audio support available using {AUDIO_METHOD}")
        else:
            print("⚠ Audio support disabled")
            if AUDIO_ERROR:
                print(f"   Error details: {AUDIO_ERROR}")
            print("For audio support:")
            print("  Option 1: pip install moviepy")
            print("  Option 2: Install ffmpeg (https://ffmpeg.org/)")
            print("\nContinuing with video-only mode...")
        
        print("\nStarting GUI...")
        
        # Create and run converter
        converter = ASCIIVideoConverter()
        converter.run()

if __name__ == "__main__":
    main()