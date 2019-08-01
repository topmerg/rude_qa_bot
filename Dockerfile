FROM python:3.7-slim as builder

WORKDIR /opt/app

COPY ["build", "build"]
RUN build/pip-require.sh build/requirements.txt

COPY ["requirements.txt", "./"]
RUN build/pip-require.sh requirements.txt

COPY ["src", "src"]
RUN build/python-linter.sh src

COPY ["tests", "tests"]
RUN build/unittest.sh

RUN build/cleanup.sh

FROM python:3.7-slim

COPY --from=builder ["/usr/local/lib/python3.7/site-packages", "/usr/local/lib/python3.7/site-packages"]
COPY ["bin", "bin"]
COPY ["src", "src"]

CMD ["bin/app"]
