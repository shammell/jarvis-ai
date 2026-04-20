#!/bin/bash
# LaTeX Compilation Script for JARVIS Research Paper

echo "=== JARVIS v9.0 Research Paper Compilation ==="
echo ""

# Check if pdflatex is installed
if ! command -v pdflatex &> /dev/null; then
    echo "ERROR: pdflatex not found"
    echo ""
    echo "Install LaTeX distribution:"
    echo "  - Windows: MiKTeX (https://miktex.org/download)"
    echo "  - macOS: MacTeX (https://www.tug.org/mactex/)"
    echo "  - Linux: sudo apt-get install texlive-full"
    echo ""
    exit 1
fi

# Compile LaTeX document
echo "Step 1: First compilation..."
pdflatex -interaction=nonstopmode JARVIS_RESEARCH_PAPER.tex > compile.log 2>&1

if [ $? -eq 0 ]; then
    echo "✓ First pass complete"
else
    echo "✗ Compilation failed - check compile.log"
    exit 1
fi

echo ""
echo "Step 2: Processing bibliography..."
bibtex JARVIS_RESEARCH_PAPER >> compile.log 2>&1
echo "✓ Bibliography processed"

echo ""
echo "Step 3: Second compilation..."
pdflatex -interaction=nonstopmode JARVIS_RESEARCH_PAPER.tex >> compile.log 2>&1
echo "✓ Second pass complete"

echo ""
echo "Step 4: Final compilation..."
pdflatex -interaction=nonstopmode JARVIS_RESEARCH_PAPER.tex >> compile.log 2>&1
echo "✓ Final pass complete"

echo ""
echo "=== Compilation Complete ==="
echo "Output: JARVIS_RESEARCH_PAPER.pdf"
echo "Log: compile.log"
echo ""

# Check if PDF was generated
if [ -f "JARVIS_RESEARCH_PAPER.pdf" ]; then
    SIZE=$(du -h JARVIS_RESEARCH_PAPER.pdf | cut -f1)
    echo "PDF generated successfully ($SIZE)"
    echo ""
    echo "Next steps:"
    echo "  1. Review PDF for formatting issues"
    echo "  2. Add figures (startup latency, architecture diagram)"
    echo "  3. Proofread for typos"
    echo "  4. Submit to target conference"
else
    echo "ERROR: PDF not generated - check compile.log"
    exit 1
fi
