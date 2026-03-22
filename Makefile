SUBFOLDERS := $(wildcard */pyproject.toml)
PACKAGES   := $(patsubst %/pyproject.toml,%,$(SUBFOLDERS))
BIN_DIR    := $(CURDIR)/bin

.PHONY: all clean $(PACKAGES)

all: $(PACKAGES)
	@echo "Done. Binaries in $(BIN_DIR)"

$(PACKAGES):
	@echo "==> Installing $@"
	cd $@ && VIRTUAL_ENV= uv sync
	@mkdir -p $(BIN_DIR)
	@# Link any [project.scripts] entries into .bin/
	@cd $@ && \
	scripts=$$(python3 -c " \
	import tomllib, pathlib; \
	d = tomllib.loads(pathlib.Path('pyproject.toml').read_text()); \
	scripts = d.get('project', {}).get('scripts', {}); \
	[print(k) for k in scripts] \
	" 2>/dev/null); \
	for cmd in $$scripts; do \
	  target="$(BIN_DIR)/$$cmd"; \
	  src="$$(pwd)/.venv/bin/$$cmd"; \
	  ln -sf "$$src" "$$target" && echo "  linked $$cmd -> $$target"; \
	done

clean:
	@for pkg in $(PACKAGES); do \
	  echo "==> Cleaning $$pkg"; \
	  rm -rf $$pkg/.venv; \
	done
	@rm -rf $(BIN_DIR)
	@echo "Cleaned."
