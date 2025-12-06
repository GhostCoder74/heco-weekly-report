# -----------------------------------------------------------------------------------------
# Project:        "hcwr - heco Weekly Report" for Wochenfazit from Bernhard Reiter
# File:           Makefile
# Authors:        Christian Klose <cklose@intevation.de>
#                 Raimund Renkert <rrenkert@intevation.de>
# GitHub:         https://github.com/GhostCoder74/heco-weekly-report (GhostCoder74)
# Copyright (c) 2024-2026 by Intevation GmbH
# SPDX-License-Identifier: GPL-2.0-or-later
#
# This file is part of "hcwr - heco Weekly Report"
# Do not remove this header.
# Wochenfazit URL:
# https://heptapod.host/intevation/getan/-/blob/branch/default/getan/templates/wochenfazit
# Header added by https://github.com/GhostCoder74/Set-Project-Headers
# -----------------------------------------------------------------------------------------

# ============================================================
# hcwr – Makefile
# Installiert:
#   /opt/hcwr/bin/hcwr
#   /opt/hcwr/modules/hcwr_*_mod.py
#
# License: GPL-3.0-or-later
# ============================================================

NAME	      := hcwr

PREFIX        := /
BASE_DIR      := opt/$(NAME)

SHARE_DIR     := $(PREFIX)/share/$(NAME)

BIN_DIR       := $(BASE_DIR)/bin
MOD_DIR       := $(BASE_DIR)/modules

INSTALL_BIN   := install -m 755
INSTALL_MOD   := install -m 644

# ------------------------------------------------------------
# Default target
# ------------------------------------------------------------
all:
	@echo "Use 'make install', 'make uninstall', or 'make tree'."

showvars:
	@echo "PREFIX     = $(PREFIX)"
	@echo "BASE_DIR   = $(BASE_DIR)"
	@echo "BIN_DIR    = $(BIN_DIR)"
	@echo "MOD_DIR    = $(MOD_DIR)"
	@echo "SHARE_DIR  = $(SHARE_DIR)"

# ------------------------------------------------------------
# Installation
# ------------------------------------------------------------
install:
	@echo "📦 Installing hcwr - heco Weekly Report..."
	@mkdir -p "$(PREFIX)/$(BIN_DIR)"
	@mkdir -p "$(PREFIX)/$(MOD_DIR)"
	@mkdir -p "$(PREFIX)/$(SHARE_DIR)"

	@$(INSTALL_BIN) "$(BIN_DIR)/$(NAME)"            "$(PREFIX)$(BIN_DIR)/"
	@$(INSTALL_MOD) "$(MOD_DIR)/$(NAME)_*_mod.py"   "$(PREFIX)/$(MOD_DIR)/"
	@$(INSTALL_MOD) "$(SHARE_DIR)/$(NAME)-Logo.jpg" "$(PREFIX)$(SHARE_DIR)/"

	@echo "✔ Installation complete!"
	@echo "→ Binary:   $(PREFIX)/$(BIN_DIR)/certtool-summary"
	@echo "→ Modules:  $(PREFIX)/$(MOD_DIR)/$(NAME)_*_mod.py"
	@echo "→ Logo:     $(PREFIX)/$(SHAR_DIR)/$(NAME)-Logo.jpeg"

# ------------------------------------------------------------
# Install geaCal plugin into hcwr
# ------------------------------------------------------------
install2hcwr:
	@echo "📦 Installing geaCal plugin into hcwr..."

	@if [ ! -d ./GaussEasterAlgorithm ]; then
		echo "❌ ERROR: No ./GaussEasterAlgorithm repo found!"
		@command -v git >/dev/null 2>&1 || { \
			echo "❌ ERROR: git is not installed!"; \
			exit 1; \
		}

		@echo "✔ git found"
		@echo "Trying to clone it from github.com"

		git clone https://github.com/GhostCoder74/GaussEasterAlgorithm.git
		@echo "✔ Successfully cloned from GitHub!"
	fi
	# Ensure plugin directory exists
	@mkdir -p "$(PREFIX)/$(MOD_DIR)/"

	@$(INSTALL_BIN) "usr/local/bin/geaCal*" "$(PREFIX)$(BIN_DIR)/"
	# Copy Python plugin modules (*.py)
	@cp -v ./GaussEasterAlgorithm/modules/geaCal_*_mod.py "$(PREFIX)/$(MOD_DIR)/"

	# Optional: copy README or data files
	@if [ -f GaussEasterAlgorithm/README.md ]; then \
		cp -v ./GaussEasterAlgorithm/README.md "$(PREFIX)/$(MOD_DIR)/"; \
	fi

	@echo "✔ geaCal plugin installed successfully into:"
	@echo "  $(PREFIX)/$(BIN_DIR)"
	@echo "  $(PREFIX)/$(MOD_DIR)"
# ------------------------------------------------------------
# Uninstall
# ------------------------------------------------------------
uninstall:
	@echo "🗑 Removing hcwr - heco Weekly Report..."

	@rm -v "$(BIN_DIR)/$(NAME)" 2>/dev/null || true
	@rm -v "$(MOD_DIR)/$(NAME)_*_mod.py" 2>/dev/null || true
	@rm -v "$(SHARE_DIR)/$(NAME)-Logo.jpg" 2>/dev/null || true

	@echo "🔍 Checking directories before removal..."

	@for d in "$(BIN_DIR)" "$(MOD_DIR)" "$(SHARE_DIR)" ; do \
		if [ -d "$$d" ]; then \
			if [ "$$(find "$$d" -mindepth 1 -maxdepth 1 | wc -l)" -gt 0 ]; then \
				echo "⚠️  WARNING: Directory $$d is NOT empty!"; \
				echo "   Remaining files:"; \
				find "$$d" -mindepth 1 -maxdepth 1 -printf "   - %f\n"; \
				echo "   → Directory will NOT be removed."; \
			else \
				echo "🗑  Removing empty directory $$d"; \
				rmdir "$$d"; \
			fi; \
		fi; \
	done

	@echo "✔ Removal complete!"

# ------------------------------------------------------------
# Show install tree (preview)
# ------------------------------------------------------------
tree:
	@echo "$(PREFIX)"
	@echo "└── opt"
	@echo "    └── hcwr"
	@echo "        ├── bin"
	@echo "        │   └── hcwr"
	@echo "        ├── modules"
	@echo "        │   ├── hcwr_config_mod.py"
	@echo "        │   ├── hcwr_dbg_mod.py"
	@echo "        │   ├── hcwr_dbms_mod.py"
	@echo "        │   ├── hcwr_extexec_mod.py"
	@echo "        │   ├── hcwr_globals_mod.py"
	@echo "        │   ├── hcwr_hcwrd_mod.py"
	@echo "        │   ├── hcwr_json_mod.py"
	@echo "        │   ├── hcwr_pg_queries_sql.py"
	@echo "        │   ├── hcwr_plugins_mod.py"
	@echo "        │   ├── hcwr_remote_mod.py"
	@echo "        │   ├── hcwr_sqlite_queries_sql.py"
	@echo "        │   ├── hcwr_tasks_mod.py"
	@echo "        │   ├── hcwr_utils_mod.py"
	@echo "        │   └── hcwr_wfout_mod.py"
	@echo "        └── share"
	@echo "            ├── hcwr-Logo.jpeg"
	@echo "            └── hcwr-Logo.xcf"

# ------------------------------------------------------------
# Show local project structure
# ------------------------------------------------------------
show:
	@echo "."
	@echo "└── opt"
	@echo "    └── hcwr"
	@echo "        ├── bin"
	@echo "        │   └── hcwr"
	@echo "        ├── modules"
	@echo "        │   ├── hcwr_config_mod.py"
	@echo "        │   ├── hcwr_dbg_mod.py"
	@echo "        │   ├── hcwr_dbms_mod.py"
	@echo "        │   ├── hcwr_extexec_mod.py"
	@echo "        │   ├── hcwr_globals_mod.py"
	@echo "        │   ├── hcwr_hcwrd_mod.py"
	@echo "        │   ├── hcwr_json_mod.py"
	@echo "        │   ├── hcwr_pg_queries_sql.py"
	@echo "        │   ├── hcwr_plugins_mod.py"
	@echo "        │   ├── hcwr_remote_mod.py"
	@echo "        │   ├── hcwr_sqlite_queries_sql.py"
	@echo "        │   ├── hcwr_tasks_mod.py"
	@echo "        │   ├── hcwr_utils_mod.py"
	@echo "        │   └── hcwr_wfout_mod.py"
	@echo "        └── share"
	@echo "            ├── hcwr-Logo.jpeg"
	@echo "            └── hcwr-Logo.xcf"

# ------------------------------------------------------------
# Dry-run test
# ------------------------------------------------------------
test:
	@echo "Running dry-run test:"
	@make -n install

# ------------------------------------------------------------
# Clean (nothing needed)
# ------------------------------------------------------------
clean:
	@echo "Nothing to clean."
