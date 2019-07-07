
all: dockerimage

dockerimage:
	docker build -t forestplot .

lint:
	pylint forestplots
	pylint test

test:
	pytest --ignore normami --ignore cephis
