# Same Playwright release as the reference build. Use on any machine where `make verify` is not zero.
# NOT YET TESTED: no Docker daemon was available where this bundle was made.
# Apple Silicon: add --platform linux/amd64 to match the reference machine.
#   docker build --platform linux/amd64 -t pour-sheets .
#   docker run --rm --platform linux/amd64 -v "$PWD":/work -w /work pour-sheets make verify PY=python
FROM mcr.microsoft.com/playwright/python:v1.63.0-noble
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
