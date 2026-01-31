.PHONY: build install clean dev

# Default build (uses uv for dependency management)
build:
	uv run build.py

# Install dependencies (creates venv automatically)
install:
	uv sync

# Build with specific class/build
monk:
	uv run build.py --build monk-sunwuko-tr

# Clean generated files
clean:
	rm -f index.html index-tailwind.html

# Watch for changes (requires entr: brew install entr)
dev:
	ls *.yaml | entr -r uv run build.py

# List available builds
list:
	@echo "Available builds:"
	@ls -1 *.yaml | grep -v 'd3-static-data\|season-journey-template' | sed 's/.yaml//'

# Help
help:
	@echo "Usage:"
	@echo "  make build    - Build with default (monk-sunwuko-tr)"
	@echo "  make install  - Install Python dependencies"
	@echo "  make monk     - Build monk guide"
	@echo "  make list     - List available builds"
	@echo "  make clean    - Remove generated HTML files"
	@echo "  make dev      - Watch mode (requires entr)"
