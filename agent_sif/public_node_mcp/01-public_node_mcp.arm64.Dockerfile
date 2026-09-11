FROM docker.io/library/node:18-alpine AS builder

WORKDIR /build

COPY alphafold-db /build/alphafold-db
COPY kegg /build/kegg
COPY ncbi-datasets /build/ncbi-datasets
COPY open-targets /build/open-targets
COPY pdb /build/pdb
COPY protein-atlas /build/protein-atlas
COPY string-db /build/string-db
COPY uniprot /build/uniprot

RUN set -eux; \
    for server in alphafold-db kegg ncbi-datasets open-targets pdb protein-atlas string-db uniprot; do \
        cd "/build/${server}"; \
        npm install --no-audit --no-fund; \
        npm run build; \
        npm prune --omit=dev; \
    done

FROM docker.io/library/node:18-alpine

WORKDIR /opt/mcps
COPY --from=builder /build /opt/mcps
RUN printf '%s\n' \
    '#!/bin/sh' \
    'set -eu' \
    'server=${1:-}' \
    'test -n "$server" || { echo "usage: public_node_mcp.sif SERVER" >&2; exit 2; }' \
    'shift' \
    'case "$server" in' \
    '  alphafold-db|kegg|ncbi-datasets|open-targets|pdb|protein-atlas|string-db|uniprot)' \
    '    exec node "/opt/mcps/${server}/build/index.js" "$@" ;;' \
    '  *) echo "unknown MCP server: $server" >&2; exit 2 ;;' \
    'esac' \
    > /usr/local/bin/run-public-mcp && chmod 755 /usr/local/bin/run-public-mcp

ENTRYPOINT ["/usr/local/bin/run-public-mcp"]
