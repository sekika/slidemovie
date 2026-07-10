#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import logging
import slidemovie

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    """
    Entry point for the slidemovie command-line tool.

    This function parses command-line arguments to control the `slidemovie.Movie` class,
    which generates narration videos from Markdown and PowerPoint files.

    Workflow:
    1.  Parse arguments (project name, modes, options).
    2.  Initialize the `Movie` class (loads default/config settings).
    3.  Override settings based on CLI arguments (TTS options, debug mode).
    4.  Configure project paths based on structure (flat or subproject).
    5.  Execute the requested action:
        - `--pptx`: Generates a draft PowerPoint from Markdown.
        - `--video`: Generates the full narration video (TTS, images, stitching).

    Usage:
        slidemovie PROJECT_NAME [--pptx] [--video] [options...]
    """
    parser = argparse.ArgumentParser(
        description="Automated tool to generate narration videos from Markdown and PowerPoint."
    )

    # --- Positional Arguments ---
    parser.add_argument(
        "project_name",
        help="Project Name (ID). If in subproject mode (--sub), this is the parent project name."
    )

    # --- Action Control Options ---
    parser.add_argument(
        "-p", "--pptx",
        action="store_true",
        help="Generate PPTX from Markdown (Drafting mode)."
    )
    parser.add_argument(
        "-v", "--video",
        action="store_true",
        help="Generate all video assets from Markdown and PPTX (Build mode)."
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Use a PDF file ({project}.pdf) as the image source instead of PPTX (with --video)."
    )

    # --- Path & Project Structure Options ---
    parser.add_argument(
        "-s", "--source-dir",
        default=".",
        help="Directory containing source files (md, pptx). Default is current directory."
    )
    parser.add_argument(
        "--sub",
        metavar="SUB_NAME",
        help="Subproject name (Child folder name). If specified, runs in hierarchical mode."
    )
    parser.add_argument(
        "-o", "--output-root",
        help="Root directory for video output. If not specified, determined automatically."
    )
    parser.add_argument(
        "-f", "--filename",
        help="Output video filename (without extension). Defaults to project ID."
    )

    # --- TTS Settings Options (CLI Overrides) ---
    parser.add_argument(
        "--tts-provider",
        help="TTS Provider (e.g., google, openai)")
    parser.add_argument("--tts-model", help="TTS Model name")
    parser.add_argument("--tts-voice", help="TTS Voice/Speaker setting")
    parser.add_argument(
        "--tts-voicevox-url",
        help="VOICEVOX engine URL (default: http://127.0.0.1:50021). Only used with --tts-provider voicevox.")
    parser.add_argument(
        "--prompt",
        help="Override TTS system prompt (automatically enables prompt usage)")
    parser.add_argument(
        "--no-prompt",
        action="store_true",
        help="Disable TTS system prompt")
    parser.add_argument(
        "--prompt-separator",
        help="Separator inserted between the style prompt and the spoken text "
             '(e.g. "\\n\\n## 原稿\\n"). Empty by default.')
    parser.add_argument(
        "--chunk-size", type=int,
        help="Max characters per TTS chunk. Enables automatic text splitting when set.")
    parser.add_argument(
        "--split-chars",
        help="Candidate split characters for chunking (default: 。．.!！?？ and newline).")
    parser.add_argument(
        "--chunk-overflow", choices=["extend", "error"],
        help="Behavior when no split candidate is found within chunk-size.")

    # --- Other Options ---
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (Verbose logging, etc)."
    )

    # 1. Initialize Movie instance (Load configuration files)
    try:
        movie = slidemovie.Movie()
    except NameError:
        logger.error(
            "Movie class is not defined. Make sure to import it correctly.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to initialize Movie class: {e}")
        sys.exit(1)

    args = parser.parse_args()

    # Exit if no action is specified
    if not args.pptx and not args.video:
        parser.print_help()
        sys.exit(1)

    # 2. Override settings with CLI options
    if args.tts_provider:
        movie.tts_provider = args.tts_provider
    if args.tts_model:
        movie.tts_model = args.tts_model
    if args.tts_voice:
        movie.tts_voice = args.tts_voice
    if args.tts_voicevox_url:
        movie.tts_voicevox_url = args.tts_voicevox_url
    if args.prompt:
        movie.prompt = args.prompt
        movie.tts_use_prompt = True
    if args.no_prompt:
        movie.tts_use_prompt = False
    # Use `is not None` so that --prompt-separator "" (an explicit empty value)
    # is honored rather than ignored.
    if args.prompt_separator is not None:
        movie.prompt_separator = args.prompt_separator
    # Use `is not None` so that --chunk-size 0 (an explicit value) is not ignored.
    if args.chunk_size is not None:
        movie.chunk_size = args.chunk_size
    if args.split_chars is not None:
        movie.split_chars = args.split_chars
    if args.chunk_overflow is not None:
        movie.chunk_overflow = args.chunk_overflow
    if args.filename:
        movie.output_filename = args.filename
    # Image source selection (PDF instead of PPTX). Only meaningful with --video.
    movie.use_pdf = args.pdf
    if args.pdf and args.pptx and not args.video:
        logger.warning(
            "--pdf has no effect on PPTX generation (-p); it only affects image source during --video.")

    if args.debug:
        movie.ffmpeg_loglevel = 'info'
        movie.show_skip = True
        logging.getLogger("google_genai").setLevel(logging.DEBUG)
        logging.getLogger("httpx").setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.info("Debug mode enabled.")

    # 3. Configure Path Settings
    try:
        if args.sub:
            # Hierarchical Mode (Parent/Child)
            logger.info(
                f"Configuring subproject paths: {args.project_name}/{args.sub}")
            movie.configure_subproject_paths(
                parent_project_name=args.project_name,
                subproject_name=args.sub,
                source_parent_dir=args.source_dir,
                output_root_dir=args.output_root
            )
        else:
            # Standard Mode (Flat)
            logger.info(f"Configuring project paths: {args.project_name}")
            movie.configure_project_paths(
                project_name=args.project_name,
                source_dir=args.source_dir,
                output_root_dir=args.output_root
            )
    except Exception as e:
        logger.error(f"Failed to configure paths: {e}")
        sys.exit(1)

    # 4. Execute Actions

    # Generate PPTX (--pptx)
    if args.pptx:
        logger.info("MODE: Build Slide PPTX")
        movie.build_slide_pptx()
        logger.info("PPTX generation process finished.")
        if not args.video:
            logger.info(
                "Please edit the generated PPTX file and run with --video to create the movie.")

    # Generate Video (--video)
    if args.video:
        logger.info("MODE: Build All Video Assets")
        movie.build_all()

        logger.info("All video processes finished.")


if __name__ == "__main__":
    main()
