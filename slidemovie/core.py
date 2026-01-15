import json
import os
import hashlib
import multiai_tts
import subprocess
import tempfile
import time
import wave
import sys
import logging
import shutil
from datetime import datetime

# Configure module logger
logger = logging.getLogger(__name__)

class Movie():
    """
    A class to automatically generate narration videos based on PowerPoint slides and Markdown notes.

    It performs Text-to-Speech (TTS) synthesis, converts slides to images, and stitches them together
    into video files. It supports incremental builds by detecting changes in source files (Markdown,
    PPTX) and configuration settings.

    Usage:
        1. Initialize the class (loads configuration).
        2. Configure paths using `configure_project_paths` or `configure_subproject_paths`.
        3. Run `build_slide_pptx()` to generate the PPTX file from Markdown (optional/drafting).
        4. Run `build_all()` to generate the audio, slide images, and the final video.
    """

    def __init__(self):
        """
        Initializes the Movie instance.

        This method checks for required external tools and loads the configuration settings.
        Settings are loaded in the following order of precedence (highest to lowest):
        1. ./config.json (Current directory)
        2. ~/.config/slidemovie/config.json (User home directory)
        3. Default settings defined in `_get_default_settings()`
        """
        self._check_external_tools()
        self._load_settings()

    def _check_external_tools(self):
        """
        Checks if required external command-line tools are installed.
        Exits the program if any tool is missing.

        Required tools:
            - ffmpeg
            - ffprobe
            - pandoc
        """
        required_tools = ['ffmpeg', 'ffprobe', 'pandoc']
        missing_tools = [tool for tool in required_tools if not shutil.which(tool)]
        
        if missing_tools:
            logger.error(f"Required external commands not found: {', '.join(missing_tools)}")
            logger.error("Please install them before running this tool.")
            sys.exit(1)

    def _get_default_settings(self):
        """
        Returns the default configuration dictionary.

        Settings:
            tts_provider (str): TTS provider (e.g., 'google', 'openai'). Default: 'google'.
            tts_model (str): TTS model name. Default: 'gemini-2.5-flash-preview-tts'.
            tts_voice (str): Voice setting for TTS. Default: 'sadaltager'.
            tts_use_prompt (bool): Whether to use a system prompt for TTS. Default: True.
            prompt (str): System prompt for TTS generation.
            screen_size (list): Video resolution [width, height]. Default: [1280, 720].
            video_fps (int): Video frame rate. Default: 30.
            video_timescale (int): Video timescale. Default: 90000.
            video_pix_fmt (str): Pixel format. Default: 'yuv420p'.
            video_codec (str): Video codec. Default: 'libx264'.
            audio_codec (str): Audio codec. Default: 'aac'.
            sample_rate (int): Audio sample rate. Default: 44100.
            audio_bitrate (str): Audio bitrate. Default: '192k'.
            audio_channels (int): Audio channels. Default: 2 (Stereo).
            ffmpeg_loglevel (str): Log level for ffmpeg. Default: 'error'.
            silence_sec (float): Silence duration inserted at the start of each slide (seconds). Default: 2.5.
            show_skip (bool): Whether to log skipped tasks. Default: False.
            max_retry (int): Max retries for TTS API errors. Default: 2.
            output_root (str): Root directory for video output. Default: None.
        """
        return {
            # TTS settings
            "tts_provider": 'google',
            "tts_model": 'gemini-2.5-flash-preview-tts',
            "tts_voice": 'sadaltager',
            "tts_use_prompt": True,
            "prompt": 'Please speak the following.',

            # Screen settings (Defined as list for JSON serialization)
            "screen_size": [1280, 720],

            # Video format settings
            "video_fps": 30,
            "video_timescale": 90000,
            "video_pix_fmt": 'yuv420p',
            "video_codec": 'libx264',

            # Audio settings
            "audio_codec": 'aac',
            "sample_rate": 44100,
            "audio_bitrate": '192k',
            "audio_channels": 2,

            # Other settings
            "ffmpeg_loglevel": 'error',
            "silence_sec": 2.5,
            "show_skip": False,
            "max_retry": 2,

            # Output path setting (Used if not provided via CLI)
            "output_root": None
        }

    def _load_settings(self):
        """
        Loads settings from JSON files and merges them with defaults.
        
        It looks for configuration in:
        1. ~/.config/slidemovie/config.json
        2. ./config.json
        
        Finally, it sets the configuration values as instance attributes.
        """
        # 1. Get default settings
        config = self._get_default_settings()

        # 2. Process ~/.config/slidemovie/config.json
        config_dir = os.path.expanduser("~/.config/slidemovie")
        if not os.path.exists(config_dir):
            try:
                os.makedirs(config_dir, exist_ok=True)
            except OSError as e:
                logger.warning(f"Failed to create config directory {config_dir}: {e}")

        home_config_path = os.path.join(config_dir, "config.json")
        
        if not os.path.exists(home_config_path):
            # Create default config file if it doesn't exist
            try:
                with open(home_config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
                logger.info(f"Created default config file: {home_config_path}")
            except IOError as e:
                logger.warning(f"Failed to create {home_config_path}: {e}")
        else:
            # Load and merge if exists
            try:
                with open(home_config_path, 'r', encoding='utf-8') as f:
                    home_config = json.load(f)
                    config.update(home_config)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load {home_config_path}: {e}")

        # 3. Process ./config.json (Current directory)
        local_config_path = "./config.json"
        
        if os.path.exists(local_config_path):
            try:
                with open(local_config_path, 'r', encoding='utf-8') as f:
                    local_config = json.load(f)
                    config.update(local_config)
                logger.info(f"Loaded local config: {local_config_path}")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load {local_config_path}: {e}")

        # 4. Set attributes
        
        # Special handling: Convert screen_size from list to tuple
        if "screen_size" in config and isinstance(config["screen_size"], list):
            config["screen_size"] = tuple(config["screen_size"])

        # Set dictionary values as instance attributes
        for key, value in config.items():
            setattr(self, key, value)

    def configure_project_paths(self, project_name, source_dir, output_root_dir=None, output_filename=None):
        """
        Configures paths for a standard (flat) project structure.
        
        Args:
            project_name (str): The name/ID of the project.
            source_dir (str): The directory containing source files (.md, .pptx).
            output_root_dir (str, optional): Root directory for video output. 
                                             Defaults to `self.output_root` or `{source_dir}/movie`.
            output_filename (str, optional): Filename for the output video (without extension).
                                             Defaults to `project_name`.
        """
        # Determine output root directory
        if output_root_dir:
            target_root = output_root_dir
        elif self.output_root:
            target_root = self.output_root
        else:
            target_root = f'{source_dir}/movie'
        
        # Expand path and check existence
        target_root = os.path.expanduser(target_root)
        if not os.path.isdir(target_root):
            logger.error(f'Directory {target_root} does not exist.')
            sys.exit(1)

        # Set member variables
        self.source_dir = source_dir
        self.project_id = project_name
        
        if not output_filename:
            output_filename = project_name

        # Construct file paths
        self.md_file = f'{self.source_dir}/{project_name}.md'
        self.status_file = f'{self.source_dir}/status.json'
        self.video_length_file = f'{self.source_dir}/video_length.csv'
        
        # Create intermediate/output directories
        self.movie_dir = f'{target_root}/{project_name}'
        if not os.path.isdir(self.movie_dir):
            os.mkdir(self.movie_dir)

        self.slide_file = f'{self.source_dir}/{project_name}.pptx'
        self.video_file = f'{self.movie_dir}/{output_filename}.mp4'


    def configure_subproject_paths(self, parent_project_name, subproject_name, source_parent_dir, output_root_dir=None, output_filename=None):
        """
        Configures paths for a nested project structure (Parent Folder -> Child Folder).
        
        Args:
            parent_project_name (str): The name of the parent project.
            subproject_name (str): The name of the subproject (child folder name).
            source_parent_dir (str): The directory containing the parent project folder.
            output_root_dir (str, optional): Root directory for video output.
            output_filename (str, optional): Filename for the output video (without extension).
        """
        # Determine output root directory
        if output_root_dir:
            target_root = output_root_dir
        elif self.output_root:
            target_root = self.output_root
        else:
            target_root = f'{source_parent_dir}/movie'
        
        # Expand path and check existence
        target_root = os.path.expanduser(target_root)
        if not os.path.isdir(target_root):
            logger.error(f'Directory {target_root} does not exist.')
            sys.exit(1)

        # Source directory is "Parent/Child"
        self.source_dir = f'{source_parent_dir}/{subproject_name}'
        
        # Project ID format: "Parent-Child"
        self.project_id = f'{parent_project_name}-{subproject_name}'
        
        if not output_filename:
            output_filename = self.project_id

        # Construct file paths
        self.md_file = f'{self.source_dir}/{subproject_name}.md'
        self.status_file = f'{self.source_dir}/status.json'
        self.video_length_file = f'{self.source_dir}/video_length.csv'
        
        # Create output directory hierarchy (movie/parent/child)
        parent_movie_dir = f'{target_root}/{parent_project_name}'
        self.movie_dir = f'{parent_movie_dir}/{subproject_name}'
        
        if not os.path.isdir(parent_movie_dir):
            os.mkdir(parent_movie_dir)
        if not os.path.isdir(self.movie_dir):
            os.mkdir(self.movie_dir)

        self.slide_file = f'{self.source_dir}/{subproject_name}.pptx'
        self.video_file = f'{self.movie_dir}/{output_filename}.mp4'

    def build_all(self):
        """
        Orchestrates the creation of the complete video from Markdown and PPTX files.
        
        Note: This does not update the PPTX file from Markdown. 
        Run `build_slide_pptx()` beforehand if necessary.
        """
        self._check_external_tools()
        if not os.path.isfile(self.md_file):
            logger.error(f'{self.md_file} does not exist.')
            sys.exit(1)
            
        # 1. Generate narration audio from Markdown notes
        self.build_slide_audio()
        # 2. Generate slide images from PPTX
        self.build_slide_images()
        # 3. Create individual video clips for each slide
        self.build_slide_videos()
        # 4. Concatenate clips into the final video
        self.build_final_video()

    def build_slide_audio(self):
        """
        Synthesizes audio (TTS) from Markdown notes and saves as WAV files.
        Skips slides that have a pre-defined video file.
        """
        self._ensure_slide_ids()
        state = self._load_audio_state()
        slides_list = self._extract_slides_list()

        # 1. Sync metadata and sort
        self._sync_slide_metadata(state, slides_list)

        # 2. Audio generation loop
        for slide in slides_list:
            slide_id = slide["id"]

            # Skip TTS if a video file is specified
            if slide.get("video_file"):
                if self.show_skip:
                    logger.info(
                        f"[SKIP] {slide_id} (Movie Mode: {slide['video_file']})")
                continue

            raw_notes = slide["notes"]

            norm = self._normalize_notes(raw_notes)
            current_notes_hash = self._hash_notes(norm)

            slide_state = state["slides"][slide_id]
            audio_state = slide_state["audio"]

            saved_notes_hash = slide_state.get("notes_hash")
            audio_status = audio_state.get("status")

            # Determine file path
            wav_path = os.path.join(
                self.movie_dir,
                audio_state["wav_file"]
            )

            # Regeneration check (Status mismatch OR Hash mismatch OR File missing)
            if (audio_status != "generated" or
                saved_notes_hash != current_notes_hash or
                    not os.path.isfile(wav_path)):

                logger.info(f"[TTS] regenerate {slide_id}")

                add_prompt = audio_state.get("additional_prompt", "")
                if norm == "":
                    logger.error(f'Error: "::: notes" not found in {slide_id}.')
                    sys.exit()
                self._speak_to_wav(
                    norm, wav_path, additional_prompt=add_prompt)
                self.prepend_silence(wav_path)
                duration = self._get_wav_duration(wav_path)

                slide_state["notes_hash"] = current_notes_hash
                slide_state["notes_length"] = len(norm)

                audio_state["status"] = "generated"
                audio_state["generated_at"] = self._now()
                audio_state["duration_sec"] = duration

                state["last_checked"] = self._now()
                self._save_audio_state(state)
            else:
                if self.show_skip:
                    logger.info(f"[SKIP] {slide_id} (Audio: Unchanged)")

    def build_slide_images(self):
        """
        Converts PPTX slides to images and renames them based on Markdown slide-ids.
        Uses a state file to detect PPTX changes and skip unnecessary processing.

        Prerequisites:
            - `self.slide_file` (pptx) must exist.
            - External tool `pptxtoimages` (LibreOffice + Poppler) must be available.
        """
        from pptxtoimages.tools import PPTXToImageConverter
        import glob

        if not os.path.isfile(self.slide_file):
            logger.error(f"Slide file does not exist: {self.slide_file}")
            return

        # 1. Change detection (Check PPTX hash)
        state = self._load_audio_state()
        current_pptx_hash = self._hash_file(self.slide_file)

        # Get existing state
        images_task = state.get("images_task", {})

        if (images_task.get("status") == "generated" and
                images_task.get("source_hash") == current_pptx_hash):
            if self.show_skip:
                logger.info(f"[SKIP] Images (PPTX unchanged)")
            return

        # --- Start Generation ---

        # Create output directory
        os.makedirs(self.movie_dir, exist_ok=True)

        # Remove existing slide_*.png
        for f in glob.glob(os.path.join(self.movie_dir, "slide_*.png")):
            os.remove(f)

        logger.info(f"Starting PPTX -> Image conversion.")

        # PPTX -> PNG
        converter = PPTXToImageConverter(self.slide_file, self.movie_dir)
        converter.convert()

        # Get generated filenames (slide_1.png, slide_2.png...)
        generated_files = sorted(
            glob.glob(os.path.join(self.movie_dir, "slide_*.png")),
            key=lambda x: int(os.path.splitext(
                os.path.basename(x))[0].split("_")[1])
        )

        # Get list of slide_ids
        slide_notes = self._extract_slide_notes()
        slide_ids = list(slide_notes.keys())

        if len(slide_ids) != len(generated_files):
            logger.warning(
                f"Generated image count ({len(generated_files)}) does not match slide_id count ({len(slide_ids)}).")

        # Rename using slide_id
        for i, slide_id in enumerate(slide_ids):
            if i >= len(generated_files):
                break
            old_path = generated_files[i]
            new_path = os.path.join(self.movie_dir, f"{slide_id}.png")
            os.rename(old_path, new_path)

        # 2. Save state
        state["images_task"] = {
            "status": "generated",
            "source_file": os.path.basename(self.slide_file),
            "source_hash": current_pptx_hash,
            "generated_at": self._now()
        }
        state["last_checked"] = self._now()
        self._save_audio_state(state)

        logger.info(f"Image conversion completed.")

    def build_slide_videos(self):
        """
        Generates individual video files for each slide.
        - Normal slide: Image (PNG) + Audio (WAV) -> MP4
        - Video slide: Source Video (MP4) -> Resize & Padding -> MP4
        """
        import subprocess

        width, height = self.screen_size
        state = self._load_audio_state()
        slides_list = self._extract_slides_list()
        self._sync_slide_metadata(state, slides_list)

        # Generation loop
        for slide in slides_list:
            slide_id = slide["id"]
            video_file_src = slide.get("video_file")

            output_mp4 = os.path.join(self.movie_dir, f"{slide_id}.mp4")

            # Get state
            if slide_id not in state["slides"]:
                state["slides"][slide_id] = self._init_slide_state(slide_id)

            slide_state = state["slides"][slide_id]

            # --- Branch: If video file is specified ---
            if video_file_src:
                src_path = os.path.join(self.movie_dir, video_file_src)

                if not os.path.isfile(src_path):
                    logger.error(
                        f"Original video not found: {src_path} (Slide: {slide_id})")
                    continue

                # Calculate hash
                current_src_hash = self._hash_file(src_path)

                # Check state
                video_state = slide_state["video"]

                # Regeneration check
                if (video_state.get("status") == "generated" and
                    video_state.get("source_hash") == current_src_hash and
                        os.path.isfile(output_mp4)):
                    if self.show_skip:
                        logger.info(
                            f"[SKIP] {slide_id} (Video: unchanged/Source:{video_file_src})")
                    continue

                logger.info(f"Converting video: {video_file_src} -> {slide_id}.mp4")

                # FFmpeg command: Resize + Audio re-encode
                cmd = [
                    "ffmpeg", "-y",
                    "-v", self.ffmpeg_loglevel,
                    "-i", src_path,
                    "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",

                    # --- Video settings ---
                    "-c:v", self.video_codec,
                    "-pix_fmt", self.video_pix_fmt,
                    "-r", str(self.video_fps),
                    "-video_track_timescale", str(self.video_timescale),

                    # --- Audio settings ---
                    "-c:a", self.audio_codec,
                    "-ar", str(self.sample_rate),
                    "-ac", str(self.audio_channels),
                    "-b:a", self.audio_bitrate,
                    output_mp4
                ]

                try:
                    subprocess.run(cmd, check=True)
                    duration = self._get_mp4_duration(output_mp4)

                    # Update state
                    slide_state["video"] = {
                        "status": "generated",
                        "source_video": video_file_src,
                        "source_hash": current_src_hash,
                        "duration_sec": duration,
                        "generated_at": self._now()
                    }
                    state["last_checked"] = self._now()
                    self._save_audio_state(state)
                    logger.info(f"Done: {output_mp4} ({duration:.2f}s)")

                except subprocess.CalledProcessError:
                    logger.error(f"Video conversion failed: {slide_id}")

            # --- Branch: Normal slide (TTS + Image) ---
            else:
                png_file = os.path.join(self.movie_dir, f"{slide_id}.png")
                wav_file = os.path.join(self.movie_dir, f"{slide_id}.wav")

                if not os.path.isfile(png_file) or not os.path.isfile(wav_file):
                    # Skip if assets are missing
                    logger.warning(f"Material missing, skipping: {slide_id}")
                    continue

                current_png_hash = self._hash_file(png_file)
                current_wav_hash = self._hash_file(wav_file)

                video_state = slide_state["video"]

                if (video_state.get("status") == "generated" and
                    video_state.get("wav_hash") == current_wav_hash and
                    video_state.get("png_hash") == current_png_hash and
                        os.path.isfile(output_mp4)):
                    if self.show_skip:
                        logger.info(f"[SKIP] {slide_id} (Video: unchanged)")
                    continue

                # Generate video from still image
                cmd = [
                    "ffmpeg", "-y",
                    "-v", self.ffmpeg_loglevel,
                    "-loop", "1",
                    "-i", png_file,
                    "-i", wav_file,

                    # --- Video settings ---
                    "-c:v", self.video_codec,
                    "-tune", "stillimage",
                    "-pix_fmt", self.video_pix_fmt,
                    "-r", str(self.video_fps),
                    "-video_track_timescale", str(self.video_timescale),
                    "-vf", f"scale={width}:{height}",

                    # --- Audio settings ---
                    "-c:a", self.audio_codec,
                    "-ar", str(self.sample_rate),
                    "-ac", str(self.audio_channels),
                    "-b:a", self.audio_bitrate,

                    "-shortest",
                    output_mp4
                ]

                logger.info(f"Generating {slide_id}.mp4...")
                try:
                    subprocess.run(cmd, check=True)
                    duration = self._get_mp4_duration(output_mp4)

                    slide_state["video"] = {
                        "status": "generated",
                        "wav_hash": current_wav_hash,
                        "png_hash": current_png_hash,
                        "duration_sec": duration,
                        "generated_at": self._now()
                    }
                    state["last_checked"] = self._now()
                    self._save_audio_state(state)
                    logger.info(f"Done: {output_mp4} ({duration:.2f}s)")

                except subprocess.CalledProcessError:
                    logger.error(f"MP4 creation failed: {slide_id}")

    def build_final_video(self):
        """
        Concatenates all generated slide videos (MP4) into a final movie.

        Process:
        1. Identify target slides based on Markdown order.
        2. Calculate a source hash from all target MP4 files.
        3. Check JSON "final_movie" entry; skip if unchanged.
        4. Use ffmpeg concat demuxer to merge.
        5. Save results to JSON.
        """
        import subprocess

        state = self._load_audio_state()

        # Get correct order from Markdown
        slides_list = self._extract_slides_list()
        slide_ids = [s["id"] for s in slides_list]

        if not slide_ids:
            logger.error("No Slide IDs found.")
            return

        # 1. Calculate source hash
        current_source_hash = self._calculate_source_hash(slide_ids)

        # 2. Skip check
        final_movie_state = state.get("final_movie", {})

        if (final_movie_state.get("status") == "generated" and
            final_movie_state.get("source_hash") == current_source_hash and
                os.path.isfile(self.video_file)):
            if self.show_skip:
                logger.info(f"[SKIP] Final Video (unchanged)")
            return

        # 3. Create concatenation list
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            concat_list = f.name
            found_count = 0
            for slide_id in slide_ids:
                mp4_path = os.path.join(self.movie_dir, f"{slide_id}.mp4")
                if os.path.isfile(mp4_path):
                    # ffmpeg concat demuxer format
                    # Use abspath for Windows path compatibility
                    f.write(f"file '{os.path.abspath(mp4_path)}'\n")
                    found_count += 1
                else:
                    logger.warning(f"MP4 not found: {mp4_path} (Skipping)")

        if found_count == 0:
            logger.error("No MP4s found for concatenation.")
            os.remove(concat_list)
            return

        logger.info("Starting final video concatenation...")

        # 4. Run FFmpeg
        cmd = [
            "ffmpeg",
            "-v", self.ffmpeg_loglevel,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list,
            "-c", "copy",
            self.video_file
        ]

        try:
            subprocess.run(cmd, check=True)

            # 5. Save results
            duration_sec = self._get_mp4_duration(self.video_file)

            state["final_movie"] = {
                "status": "generated",
                "file_name": os.path.basename(self.video_file),
                "generated_at": self._now(),
                "duration_min": duration_sec / 60.0,
                "slides": found_count,
                "source_hash": current_source_hash
            }

            state["last_checked"] = self._now()
            self._save_audio_state(state)

            logger.info(
                f"Final video created and saved: {self.video_file} ({duration_sec/60.0:.2f} min)")

        except subprocess.CalledProcessError:
            logger.error("MP4 concatenation failed.")
        finally:
            if os.path.exists(concat_list):
                os.remove(concat_list)

    def _get_build_config(self):
        """
        Returns a dictionary of current build configuration for consistency checks.
        """
        return {
            "screen": {
                "width": self.screen_size[0],
                "height": self.screen_size[1]
            },
            "video": {
                "fps": self.video_fps,
                "timescale": self.video_timescale,
                "pix_fmt": self.video_pix_fmt,
                "codec": self.video_codec
            },
            "audio": {
                "codec": self.audio_codec,
                "sample_rate": self.sample_rate,
                "bitrate": self.audio_bitrate,
                "channels": self.audio_channels
            },
            "common": {
                "silence_sec": self.silence_sec
            }
        }

    def _ensure_slide_ids(self):
        """
        Scans the Markdown file and inserts `<!-- slide-id: ... -->` for headers that lack them.
        Also checks for duplicate slide IDs.

        Format:
            <!-- slide-id: {project_id}-{seq} -->
        """
        import re

        # 1. Read current file content
        if not os.path.exists(self.md_file):
            return

        with open(self.md_file, encoding="utf-8") as f:
            lines = f.readlines()

        # 2. Extract existing slide-ids to prevent duplicates
        # Pattern: <!-- slide-id: {project_id}-XX -->
        id_pattern = re.compile(r'<!--\s*slide-id:\s*(.+?)\s*-->')
        existing_ids = set()
        max_seq = 0

        for line in lines:
            m = id_pattern.search(line)
            if m:
                sid = m.group(1).strip()

                if sid in existing_ids:
                    logger.error(f"Duplicate slide_id detected: {sid}")
                    sys.exit(1)

                existing_ids.add(sid)

                # Track max sequence number for auto-numbering
                prefix = f"{self.project_id}-"
                if sid.startswith(prefix):
                    try:
                        num_part = sid[len(prefix):]
                        val = int(num_part)
                        if val > max_seq:
                            max_seq = val
                    except ValueError:
                        pass

        # 3. Insert IDs for headers missing them
        new_lines = []

        for i, line in enumerate(lines):
            stripped_line = line.strip()

            # If it's a header line
            if stripped_line.startswith("#"):

                # Check if the previous non-empty line was an ID
                has_id = False
                check_index = len(new_lines) - 1
                while check_index >= 0:
                    prev = new_lines[check_index].strip()
                    if prev == "":
                        check_index -= 1
                        continue
                    if id_pattern.match(prev):
                        has_id = True
                    break

                # If no ID, generate and insert one
                if not has_id:
                    while True:
                        max_seq += 1
                        new_id = f"{self.project_id}-{max_seq:02d}"
                        if new_id not in existing_ids:
                            existing_ids.add(new_id)
                            break

                    new_lines.append(f"<!-- slide-id: {new_id} -->\n")

            new_lines.append(line)

        # 4. Write back if changes occurred
        if new_lines != lines:
            logger.info("Adding missing slide-ids...")
            with open(self.md_file, "w", encoding="utf-8") as f:
                f.writelines(new_lines)

    def _sync_slide_metadata(self, state, slides_list):
        """
        Syncs Markdown information (titles, order, video_files) with the JSON state.
        """
        is_updated = False

        for i, slide in enumerate(slides_list):
            slide_id = slide["id"]

            if slide_id not in state["slides"]:
                state["slides"][slide_id] = self._init_slide_state(slide_id)
                is_updated = True

            slide_state = state["slides"][slide_id]

            # index
            new_index = i + 1
            if slide_state.get("slide_index") != new_index:
                slide_state["slide_index"] = new_index
                is_updated = True

            # title
            if slide_state.get("title") != slide["title"]:
                slide_state["title"] = slide["title"]
                is_updated = True

            # video_file sync
            new_video_file = slide.get("video_file")
            if slide_state.get("video_file") != new_video_file:
                slide_state["video_file"] = new_video_file
                is_updated = True

            # audio/additional_prompt backfill
            if "audio" in slide_state:
                if "additional_prompt" not in slide_state["audio"]:
                    slide_state["audio"]["additional_prompt"] = ""
                    is_updated = True

            # video init
            if "video" not in slide_state:
                slide_state["video"] = {
                    "status": "missing"
                }
                is_updated = True

        if is_updated:
            state["last_checked"] = self._now()
            self._save_audio_state(state)
            logger.info("Slide order and metadata updated.")

    def _extract_slide_notes(self):
        """
        Parses the Markdown file to extract slide-ids and corresponding notes.
        Exits if duplicate slide_ids are found.

        Returns:
            dict: {slide_id (str): notes_text (str)}
        """
        slides = {}
        current_id = None
        in_notes = False
        buffer = []

        with open(self.md_file, encoding="utf-8") as f:
            for line in f:
                if line.startswith("<!-- slide-id:"):
                    current_id = line.strip()[len(
                        "<!-- slide-id:"): -3].strip()

                    if current_id in slides:
                        logger.error(
                            f"Duplicate slide_id detected: {current_id}")
                        sys.exit(1)

                    slides[current_id] = ""
                    continue

                if line.strip() == "::: notes":
                    in_notes = True
                    buffer = []
                    continue

                if line.strip() == ":::" and in_notes:
                    slides[current_id] = "".join(buffer).strip()
                    in_notes = False
                    continue

                if in_notes:
                    buffer.append(line)

        return slides

    def _extract_slides_list(self):
        """
        Parses Markdown to extract a list of slides containing:
        slide-id, video-file, title, and notes.
        Exits on duplicate slide_ids.
        """
        slides = []
        seen_ids = set()

        current_data = {
            "id": None,
            "title": "",
            "video_file": None,
            "notes_buffer": [],
            "in_notes": False
        }

        def _save_current(data):
            if data["id"]:
                notes_text = "".join(data["notes_buffer"]).strip()
                slides.append({
                    "id": data["id"],
                    "title": data["title"],
                    "video_file": data["video_file"],
                    "notes": notes_text
                })

        with open(self.md_file, encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()

                # slide-id
                if line.startswith("<!-- slide-id:"):
                    _save_current(current_data)
                    new_id = line.strip()[len("<!-- slide-id:"): -3].strip()

                    if new_id in seen_ids:
                        logger.error(f"Duplicate slide_id detected: {new_id}")
                        sys.exit(1)
                    seen_ids.add(new_id)

                    current_data = {
                        "id": new_id,
                        "title": "",
                        "video_file": None,
                        "notes_buffer": [],
                        "in_notes": False
                    }
                    continue

                # video-file
                if line.startswith("<!-- video-file:"):
                    v_file = line.strip()[len("<!-- video-file:"): -3].strip()
                    current_data["video_file"] = v_file
                    continue

                # Title
                if (current_data["id"] and not current_data["title"]
                        and line.startswith("# ") and not line.startswith("##")):
                    current_data["title"] = line[2:].strip()
                    continue

                # notes block
                if stripped == "::: notes":
                    current_data["in_notes"] = True
                    current_data["notes_buffer"] = []
                    continue

                if stripped == ":::" and current_data["in_notes"]:
                    current_data["in_notes"] = False
                    continue

                if current_data["in_notes"]:
                    current_data["notes_buffer"].append(line)

            _save_current(current_data)

        return slides

    def _load_audio_state(self):
        """
        Loads the audio generation state file (JSON).

        Validation:
        1. build_config: If inconsistent with current settings (e.g., resolution change), exits with error.
        2. tts_config: If inconsistent, prompts the user to continue or abort.
        """
        if not os.path.isfile(self.status_file):
            return self._init_audio_state(self.status_file)

        with open(self.status_file, encoding="utf-8") as f:
            state = json.load(f)

        # --- build_config check ---
        stored_config = state.get("build_config")
        current_config = self._get_build_config()

        if stored_config is None:
            logger.info("No build_config in state file. Applying current settings.")
            state["build_config"] = current_config
            self._save_audio_state(state)
            stored_config = current_config

        if stored_config != current_config:
            import pprint
            logger.error("build_config inconsistency detected.")
            logger.error("Changing resolution/FPS mid-process is not supported. Aborting.")
            logger.error("-" * 40)
            logger.error("[Stored Config]")
            logger.error(pprint.pformat(stored_config))
            logger.error("-" * 40)
            logger.error("[Current Config]")
            logger.error(pprint.pformat(current_config))
            logger.error("-" * 40)
            sys.exit(1)

        # --- tts_config check ---
        stored_tts = state.get("tts_config")
        current_tts = self._get_tts_config()

        # Auto-fill if missing (Migration)
        if stored_tts is None:
            logger.info("No TTS config in state file. Applying current settings.")
            state["tts_config"] = current_tts
            self._save_audio_state(state)

        # Confirmation prompt if mismatched
        elif stored_tts != current_tts:
            import pprint
            logger.warning("=" * 60)
            logger.warning("TTS config change detected.")
            logger.warning("=" * 60)
            logger.warning("[Stored Config (Previous)]")
            logger.warning(pprint.pformat(stored_tts))
            logger.warning("-" * 40)
            logger.warning("[Current Config (Now)]")
            logger.warning(pprint.pformat(current_tts))
            logger.warning("=" * 60)
            logger.warning("Generating audio with different settings may result in inconsistent audio in the video.")

            while True:
                choice = input(
                    "Select action: 1) Ignore and Continue (Overwrite config)  2) Abort [1/2]: ").strip()
                if choice == '1':
                    logger.info("Applying new settings and continuing. Updating state file.")
                    state["tts_config"] = current_tts
                    self._save_audio_state(state)
                    break
                elif choice == '2':
                    logger.info("Aborted by user.")
                    sys.exit(0)
                else:
                    logger.warning("Please enter 1 or 2.")

        return state

    def _save_audio_state(self, state):
        """
        Saves the audio generation state to the JSON file.
        Sorts slides by `slide_index` before saving to ensure order in the file.
        """
        if "slides" in state:
            # Sort dictionary by slide_index
            sorted_slides = dict(sorted(
                state["slides"].items(),
                key=lambda item: item[1].get("slide_index", 999999)
            ))
            state["slides"] = sorted_slides

        with open(self.status_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def _init_audio_state(self, path):
        """
        Creates and returns a new state management dictionary.
        Records current build_config and tts_config.
        """
        return {
            "schema_version": "1.0",
            "project_id": self.project_id,
            "last_checked": None,
            "build_config": self._get_build_config(),
            "tts_config": self._get_tts_config(),
            "pptx_task": {
                "status": "missing",
                "source_file": os.path.basename(self.md_file) if hasattr(self, 'md_file') else "",
                "source_hash": None,
                "generated_at": None
            },
            "images_task": {
                "status": "missing",
                "source_file": os.path.basename(self.slide_file) if hasattr(self, 'slide_file') else "",
                "source_hash": None,
                "generated_at": None
            },
            "tts_engine": {  # Kept for legacy compatibility
                "provider": self.tts_provider,
                "model": self.tts_model,
                "voice": self.tts_voice
            },
            "slides": {}
        }

    def _get_tts_config(self):
        """
        Returns a dictionary of current TTS configuration.
        """
        return {
            "provider": self.tts_provider,
            "model": self.tts_model,
            "voice": self.tts_voice,
            "use_prompt": self.tts_use_prompt,
            "prompt": self.prompt
        }

    def _get_wav_duration(self, wav_path):
        """
        Gets the duration (seconds) of a WAV file.
        """
        if not os.path.isfile(wav_path):
            return 0.0
        try:
            with wave.open(wav_path, 'rb') as f:
                frames = f.getnframes()
                rate = f.getframerate()
                if rate > 0:
                    return frames / float(rate)
        except Exception as e:
            logger.warning(f"WAV duration check failed: {e}")
        return 0.0

    def prepend_silence(self, wav_file):
        """
        Inserts a silence period at the beginning of the specified WAV file.
        The duration is defined by `self.silence_sec`.

        Args:
            wav_file (str): Path to the target WAV file.
        """
        tmp = tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False, dir=os.path.dirname(wav_file)
        )
        tmp.close()

        cmd = [
            "ffmpeg", "-y",
            "-v", self.ffmpeg_loglevel,
            "-f", "lavfi",
            "-t", str(self.silence_sec),
            "-i", f"anullsrc=r={self.sample_rate}:cl=mono",
            "-i", wav_file,
            "-filter_complex", "[0:a][1:a]concat=n=2:v=0:a=1",
            tmp.name
        ]

        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)

        os.replace(tmp.name, wav_file)

    def build_slide_pptx(self):
        """
        Generates a PowerPoint file (.pptx) from Markdown using Pandoc.
        Checks hash to skip generation if Markdown hasn't changed.

        Prerequisites:
            - `pandoc` must be installed.
        """
        if not os.path.exists(self.md_file):
            logger.error(f"Markdown file does not exist: {self.md_file}")
            return

        # 1. Change detection
        state = self._load_audio_state()
        current_md_hash = self._hash_file(self.md_file)

        pptx_task = state.get("pptx_task", {})

        # Skip if PPTX exists and hash matches
        if (pptx_task.get("status") == "generated" and
            pptx_task.get("source_hash") == current_md_hash and
                os.path.isfile(self.slide_file)):

            logger.info(f"[SKIP] PPTX Create (Markdown unchanged)")
            return

        # --- Start Generation ---

        command = (
            f'pandoc {self.md_file} '
            f'--slide-level=1 '
            f'--resource-path={self.source_dir} '
            f'-o {self.slide_file}'
        )

        logger.info(f'Starting Markdown -> PPTX conversion.')

        try:
            subprocess.check_call(command, shell=True)

            # 2. Save state
            state["pptx_task"] = {
                "status": "generated",
                "source_file": os.path.basename(self.md_file),
                "source_hash": current_md_hash,
                "generated_at": self._now()
            }
            state["last_checked"] = self._now()
            self._save_audio_state(state)

            logger.info(f"PPTX conversion completed and state saved.")

        except subprocess.CalledProcessError:
            logger.error(f'PPTX conversion error')
            sys.exit(0)

    def _init_slide_state(self, slide_id):
        """
        Returns the initial state dictionary for a single slide.
        """
        return {
            "slide_index": None,
            "title": "",
            "notes_hash": None,
            "notes_length": 0,
            "audio": {
                "status": "missing",
                "wav_file": f"{slide_id}.wav",
                "generated_at": None,
                "duration_sec": None,
                "additional_prompt": ""
            }
        }

    def _speak_to_wav(self, text, wav_path, additional_prompt=""):
        """
        Synthesizes text to speech using the configured TTS client and saves as WAV.

        Args:
            text (str): Text to synthesize.
            wav_path (str): Output WAV file path.
            additional_prompt (str): Additional prompt for specific slides.
        """
        client = multiai_tts.Prompt()
        client.set_tts_model(self.tts_provider, self.tts_model)
        if self.tts_provider == 'openai':
            client.tts_voice_openai = self.tts_voice
        if self.tts_provider == 'google':
            client.tts_voice_google = self.tts_voice

        if self.tts_use_prompt:
            full_prompt_text = f'{self.prompt}{additional_prompt}\n{text}'
        else:
            full_prompt_text = text

        for attempt in range(self.max_retry):
            client.save_tts(full_prompt_text, wav_path)

            if not client.error:
                return

            if attempt > 0 or 'RESOURCE_EXHAUSTED' in client.error_message:
                logger.error(client.error_message)
                sys.exit()
            else:
                logger.error(
                    f'{full_prompt_text}\n{client.error_message}\nWaiting for 3 minutes and retry...')
                time.sleep(180)

    def _normalize_notes(self, text):
        """
        Normalizes note text by stripping whitespace and empty lines.
        """
        return "\n".join(
            line.strip()
            for line in text.strip().splitlines()
            if line.strip()
        )

    def _hash_notes(self, text):
        """
        Calculates SHA-256 hash of the text.
        """
        return "sha256:" + hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest()

    def _hash_file(self, filepath):
        """
        Calculates SHA-256 hash of a file.
        """
        if not os.path.isfile(filepath):
            return None
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return "sha256:" + h.hexdigest()

    def _calculate_source_hash(self, slide_ids):
        """
        Calculates a unique hash representing the entire sequence of source MP4s.
        Reads MP4 files in the order of `slide_ids`.
        """
        h = hashlib.sha256()

        for sid in slide_ids:
            mp4_path = os.path.join(self.movie_dir, f"{sid}.mp4")

            if os.path.isfile(mp4_path):
                # Update hash with file content
                with open(mp4_path, "rb") as f:
                    while chunk := f.read(8192):
                        h.update(chunk)
            else:
                # Mark as missing in hash
                h.update(f"{sid}:missing".encode("utf-8"))

        return "sha256:" + h.hexdigest()

    def _now(self):
        """
        Returns current datetime in ISO format (seconds precision).
        """
        return datetime.now().isoformat(timespec="seconds")

    def write_video_length_csv(self):
        """
        Generates a CSV report comparing Markdown slide structure and generated videos.

        Columns:
            - slide_id
            - title
            - notes_length
            - duration_sec

        Output: `self.video_length_file`
        """
        import csv

        slides = []  # [(slide_id, title, notes_length)]

        current_id = None
        current_title = ""
        in_notes = False
        notes_buffer = []

        with open(self.md_file, encoding="utf-8") as f:
            for line in f:
                # slide-id
                if line.startswith("<!-- slide-id:"):
                    current_id = line.strip()[len(
                        "<!-- slide-id:"): -3].strip()
                    current_title = ""
                    notes_buffer = []
                    in_notes = False
                    continue

                # Title
                if current_id and not current_title and line.startswith("# "):
                    current_title = line[2:].strip()
                    continue

                # notes start
                if line.strip() == "::: notes":
                    in_notes = True
                    notes_buffer = []
                    continue

                # notes end
                if line.strip() == ":::" and in_notes:
                    notes_text = "".join(notes_buffer)
                    notes_length = len(
                        self._normalize_notes(notes_text)
                    )
                    slides.append(
                        (current_id, current_title, notes_length)
                    )
                    in_notes = False
                    current_id = None
                    continue

                # notes body
                if in_notes:
                    notes_buffer.append(line)

        os.makedirs(os.path.dirname(self.video_length_file), exist_ok=True)

        # Use utf-8-sig for Excel compatibility
        with open(
            self.video_length_file,
            "w",
            encoding="utf-8-sig",
            newline=""
        ) as f:
            writer = csv.writer(f)
            writer.writerow(
                ["slide_id", "title", "notes_length", "duration_sec"]
            )

            for slide_id, title, notes_length in slides:
                mp4 = os.path.join(self.movie_dir, f"{slide_id}.mp4")

                if not os.path.isfile(mp4):
                    logger.warning(f"mp4 does not exist: {mp4}")
                    continue

                duration = self._get_mp4_duration(mp4)
                writer.writerow(
                    [slide_id, title, notes_length, f"{duration:.2f}"]
                )

    def _get_mp4_duration(self, mp4_path):
        """
        Uses ffprobe to get the duration of an MP4 file in seconds.
        """
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            mp4_path,
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        return float(result.stdout.strip())
