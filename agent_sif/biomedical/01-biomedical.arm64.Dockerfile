FROM docker.io/library/rust:1.88-bookworm AS builder

WORKDIR /src
COPY biomedical /src
RUN cargo build --locked --release --bin biomcp

FROM docker.io/library/debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /src/target/release/biomcp /usr/local/bin/biomcp
RUN chmod 755 /usr/local/bin/biomcp \
    && mkdir -p /work /tmp/biomcp \
    && chmod 777 /work /tmp/biomcp
WORKDIR /work
ENV XDG_CACHE_HOME=/tmp/biomcp
ENTRYPOINT ["/usr/local/bin/biomcp"]
