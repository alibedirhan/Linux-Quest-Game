#!/bin/bash
#
# Linux Command Quest - Başlatıcı
# ===============================
#
# Kullanım:
#   ./play.sh              # Normal başlat
#   ./play.sh --no-boot    # Boot animasyonu olmadan
#   ./play.sh -t cyberpunk # Farklı tema ile
#

set -e

# Renk tanımları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script dizini
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Banner
echo -e "${CYAN}"
echo "  _     _                    ___                  _   "
echo " | |   (_)_ __  _   ___  __ / _ \ _   _  ___  ___| |_ "
echo " | |   | | '_ \| | | \ \/ / | | | | | |/ _ \/ __| __|"
echo " | |___| | | | | |_| |>  <| |_| | |_| |  __/\__ \ |_ "
echo " |_____|_|_| |_|\__,_/_/\_\\___/ \__,_|\___||___/\__|"
echo -e "${NC}"
echo -e "${GREEN}Command Quest v2.0.0${NC}"
echo ""

# Python kontrolü
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON=python3
    elif command -v python &> /dev/null; then
        PYTHON=python
    else
        echo -e "${RED}❌ Python bulunamadı!${NC}"
        echo "   Python 3.10+ yükleyin: sudo apt install python3"
        exit 1
    fi
    
    # Versiyon kontrolü
    PY_VERSION=$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PY_MAJOR=$($PYTHON -c 'import sys; print(sys.version_info.major)')
    PY_MINOR=$($PYTHON -c 'import sys; print(sys.version_info.minor)')
    
    if [[ $PY_MAJOR -lt 3 ]] || [[ $PY_MAJOR -eq 3 && $PY_MINOR -lt 10 ]]; then
        echo -e "${RED}❌ Python 3.10+ gerekli!${NC}"
        echo "   Mevcut: Python $PY_VERSION"
        exit 1
    fi
    
    echo -e "${GREEN}✓${NC} Python $PY_VERSION"
}

# Terminal boyut kontrolü
check_terminal() {
    COLS=$(tput cols 2>/dev/null || echo 80)
    ROWS=$(tput lines 2>/dev/null || echo 24)
    
    if [[ $COLS -lt 80 ]] || [[ $ROWS -lt 24 ]]; then
        echo -e "${YELLOW}⚠ Terminal küçük: ${COLS}x${ROWS}${NC}"
        echo "   Minimum: 80x24"
        echo "   Önerilen: 120x35"
        echo ""
        read -p "Devam etmek istiyor musun? (e/h) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Ee]$ ]]; then
            exit 0
        fi
    else
        echo -e "${GREEN}✓${NC} Terminal boyutu: ${COLS}x${ROWS}"
    fi
}

# Curses kontrolü
check_curses() {
    if $PYTHON -c "import curses" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Curses modülü"
    else
        echo -e "${RED}❌ Curses modülü bulunamadı!${NC}"
        echo "   Yükleyin: sudo apt install python3-curses"
        exit 1
    fi
}

echo -e "${CYAN}Sistem kontrolleri...${NC}"
check_python
check_terminal
check_curses
echo ""

# Oyunu başlat
echo -e "${GREEN}Oyun başlatılıyor...${NC}"
echo ""

# Python modül olarak çalıştır
$PYTHON -m src.main "$@"

# Çıkış mesajı
EXIT_CODE=$?
if [[ $EXIT_CODE -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}Tekrar görüşmek üzere!${NC}"
else
    echo ""
    echo -e "${RED}Oyun hata ile sonlandı (kod: $EXIT_CODE)${NC}"
fi

exit $EXIT_CODE
