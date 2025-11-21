DOCKER_USER=underwoodsteam
IMAGE=$(DEPLOYMENT)-$(COMPONENT)

.PHONY build
build:
	@docker build -t $(DOCKER_USER)/$(IMAGE):latest $(COMPONENT)/
	@echo $(DOCKER_TOKEN) | docker login -u $(DOCKER_USER) --password-stdin
	@docker push $(DOCKER_USER)/$(IMAGE):latest

.PHONY: pull
pull:
    @ssh -i "$(SSH_KEY_PATH)" ubuntu@vps-fddfb9a0.vps.ovh.net \
        'cd repo && git pull && kubectl apply -f $(COMPONENT)/deployments/ && kubectl rollout restart deployment/$(COMPONENT)-deployment'

.PHONY deploy
deploy: build pull
