# Logging

UID ?= 2000
GID ?= 2000
LOG_DIR ?= ./logs

.PHONY: fix-logs-perms check-logs-perms

fix-logs-perms:
	mkdir -p $(LOG_DIR)
	chown -R $(UID):$(GID) $(LOG_DIR)

check-logs-perms:
	@mkdir -p $(LOG_DIR)
	@owner="$$(stat -c '%u:%g' $(LOG_DIR))"; \
	if [ "$$owner" != "$(UID):$(GID)" ]; then \
		echo ""; \
		echo "==================== PERMISSION ERROR ===================="; \
		echo "LOG_DIR: $(LOG_DIR)"; \
		echo "Current owner:  $$owner"; \
		echo "Expected owner: $(UID):$(GID)"; \
		echo ""; \
		echo "PLEASE RUN:"; \
		echo "  sudo make fix-logs-perms"; \
		echo "=========================================================="; \
		echo ""; \
		exit 1; \
	fi


# Docker

IMAGE_NAME=fabulon/vredanol_inference

.PHONY: build push

build:
	docker build -t $(IMAGE_NAME) .

push:
	docker push $(IMAGE_NAME)


# Docker compose

.PHONY: up up-no-build restart down ps restart

BUILD_FLAG ?=

up:
	@$(MAKE) up-no-build BUILD_FLAG=--build

up-no-build: check-logs-perms
	docker compose up $(BUILD_FLAG) -d

down:
	@args="$(filter-out $@,$(MAKECMDGOALS))"; \
	docker compose down $$args

ps:
	@args="$(filter-out $@,$(MAKECMDGOALS))"; \
	docker compose ps $$args

restart:
	docker compose down
	docker compose up --build -d

ifneq (,$(filter down ps,$(firstword $(MAKECMDGOALS))))
%:
	@:
endif