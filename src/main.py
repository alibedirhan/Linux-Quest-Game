#!/usr/bin/env python3
"""
Linux Command Quest - Main Entry Point
======================================

Hacknet-style interactive Linux learning game.

Usage:
    python -m src.main
    python main.py
    ./play.sh
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_requirements():
    """Check system requirements."""
    import shutil
    
    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ Python 3.10 veya üstü gerekli!")
        print(f"   Mevcut: Python {sys.version_info.major}.{sys.version_info.minor}")
        sys.exit(1)
    
    # Check terminal size
    size = shutil.get_terminal_size()
    if size.columns < 80 or size.lines < 24:
        print("❌ Terminal çok küçük!")
        print(f"   Mevcut: {size.columns}x{size.lines}")
        print(f"   Minimum: 80x24")
        print(f"   Önerilen: 120x35")
        sys.exit(1)
    
    # Check if running in a proper terminal
    if not sys.stdin.isatty():
        print("❌ Bu program bir terminal içinde çalıştırılmalı!")
        sys.exit(1)


def main():
    """Main entry point."""
    import curses
    
    check_requirements()
    
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(
        description="Linux Command Quest - İnteraktif Linux Öğrenme Oyunu"
    )
    parser.add_argument(
        "--theme", "-t",
        choices=["default", "matrix", "cyberpunk", "retro"],
        default="matrix",
        help="Renk teması (varsayılan: matrix)"
    )
    parser.add_argument(
        "--no-boot",
        action="store_true",
        help="Boot animasyonunu atla"
    )
    parser.add_argument(
        "--no-sound",
        action="store_true", 
        help="Ses efektlerini kapat"
    )
    parser.add_argument(
        "--user", "-u",
        default="user",
        help="Kullanıcı adı (varsayılan: user)"
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="Linux Command Quest v2.0.0"
    )
    
    args = parser.parse_args()
    
    def run_game(stdscr):
        from src.core.game import Game, GameConfig
        
        config = GameConfig(
            username=args.user,
            theme=args.theme,
            show_boot_animation=not args.no_boot,
            sound_enabled=not args.no_sound,
        )
        
        game = Game(stdscr, config)
        game.run()
    
    try:
        curses.wrapper(run_game)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        # Restore terminal
        print(f"\n❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n👋 Linux Command Quest'ten çıkıldı. Görüşmek üzere!")


if __name__ == "__main__":
    main()
