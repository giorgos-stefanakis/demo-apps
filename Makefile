IMAGE_NAME   := demo-app
IMAGE_TAG    ?= $(shell git rev-parse --short HEAD)
# Login server of the Azure Container Registry, e.g. example.azurecr.io. Empty skips the push.
REGISTRY     ?=
KIND_CLUSTER ?= demo

IMAGE = $(if $(REGISTRY),$(REGISTRY)/)$(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: build push lint smoke

build:
	docker build -t $(IMAGE) .

push: build
ifneq ($(REGISTRY),)
	az acr login --name $(firstword $(subst ., ,$(REGISTRY)))
	docker push $(IMAGE)
endif
	kind load docker-image $(IMAGE) --name $(KIND_CLUSTER)
	@echo "Image: $(IMAGE)"

lint:
	uvx ruff check app
	uvx ruff format --check app
	helm lint chart -f chart/ci/lint-values.yaml

smoke:
	scripts/smoke.sh
