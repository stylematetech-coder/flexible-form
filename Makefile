.PHONY: mongo dev stop
mongo:
	docker compose up -d
dev:
	python3 scripts/dev.py
stop:
	python3 scripts/stop.py
