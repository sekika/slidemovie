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
    parser.add_argument("--tts-provider", help="TTS Provider (e.g., google, openai)")
    parser.add_argument("--tts-model", help="TTS Model name")
    parser.add_argument("--tts-voice", help="TTS Voice/Speaker setting")
    parser.add_argument("--prompt", help="Override TTS system prompt (automatically enables prompt usage)")
    parser.add_argument("--no-prompt", action="store_true", help="Disable TTS system prompt")

    # --- Other Options ---
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (Verbose logging, etc)."
    )

    args = parser.parse_args()

    # Exit if no action is specified
    if not args.pptx and not args.video:
        parser.print_help()
        sys.exit(1)

    # 1. Initialize Movie instance (Load configuration files)
    try:
        movie = slidemovie.Movie()
    except NameError:
        logger.error("Movie class is not defined. Make sure to import it correctly.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to initialize Movie class: {e}")
        sys.exit(1)

    # 2. Override settings with CLI options
    if args.tts_provider:
        movie.tts_provider = args.tts_provider
    if args.tts_model:
        movie.tts_model = args.tts_model
    if args.tts_voice:
        movie.tts_voice = args.tts_voice
    if args.prompt:
        movie.prompt = args.prompt
        movie.tts_use_prompt = True
    if args.no_prompt:
        movie.tts_use_prompt = False
    
    if args.debug:
        movie.ffmpeg_loglevel = 'info'
        movie.show_skip = True
        logger.setLevel(logging.DEBUG)
        logger.info("Debug mode enabled.")

    # 3. Configure Path Settings
    try:
        if args.sub:
            # Hierarchical Mode (Parent/Child)
            logger.info(f"Configuring subproject paths: {args.project_name}/{args.sub}")
            movie.configure_subproject_paths(
                parent_project_name=args.project_name,
                subproject_name=args.sub,
                source_parent_dir=args.source_dir,
                output_root_dir=args.output_root,
                output_filename=args.filename
            )
        else:
            # Standard Mode (Flat)
            logger.info(f"Configuring project paths: {args.project_name}")
            movie.configure_project_paths(
                project_name=args.project_name,
                source_dir=args.source_dir,
                output_root_dir=args.output_root,
                output_filename=args.filename
            )
    except Exception as e:
        logger.error(f"Failed to configure paths: {e}")
        sys.exit(1)

    # 4. Execute Actions

    # Generate PPTX (--pptx)
    if args.pptx:
        logger.info("=" * 60)
        logger.info("MODE: Build Slide PPTX")
        logger.info("=" * 60)
        movie.build_slide_pptx()
        logger.info("PPTX generation process finished.")
        if not args.video:
            logger.info("Please edit the generated PPTX file and run with --video to create the movie.")

    # Generate Video (--video)
    if args.video:
        logger.info("=" * 60)
        logger.info("MODE: Build All Video Assets")
        logger.info("=" * 60)
        movie.build_all()
        
        logger.info("All video processes finished.")

if __name__ == "__main__":
    main()
