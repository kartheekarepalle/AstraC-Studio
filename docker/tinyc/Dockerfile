FROM debian:bookworm-slim

ARG ADD_LOCAL_TINYC=0
ARG LOCAL_TINYC_PATH=./tinyc

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git build-essential wget pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp/build

# If the user provides a local tinyc binary in the build context at ./tinyc,
# copy it into /usr/local/bin/tinyc. Otherwise, try to build tinycc from source
# as a reasonable substitute.
COPY tinyc /tmp/build/tinyc
RUN if [ -f /tmp/build/tinyc ]; then \
    install -m 0755 /tmp/build/tinyc /usr/local/bin/tinyc; \
    else \
    echo "No local tinyc provided; attempting to build tinycc from source"; \
    git clone https://repo.or.cz/tinycc.git /tmp/build/tinycc && cd /tmp/build/tinycc && ./configure && make -j2 && make install; \
    if [ -f /usr/local/bin/tcc ]; then ln -s /usr/local/bin/tcc /usr/local/bin/tinyc; fi; \
    fi

WORKDIR /work
VOLUME ["/work"]
ENTRYPOINT ["tinyc"]
