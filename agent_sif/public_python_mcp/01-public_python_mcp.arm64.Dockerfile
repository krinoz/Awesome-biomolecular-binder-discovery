FROM docker.io/library/python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates perl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/mcps
COPY interpro_mcp /opt/mcps/interpro_mcp
COPY msa_mcp /opt/mcps/msa_mcp
COPY protein-sol_mcp /opt/mcps/protein-sol_mcp
COPY pymol /opt/mcps/pymol
COPY pubmed /opt/mcps/pubmed

RUN pip install --no-cache-dir \
    fastmcp loguru click pandas numpy tqdm requests httpx \
    'mcp[cli]>=1.1.0' 'pydantic>=2.0.0' 'pydantic-settings>=2.0.0' \
    python-dotenv uvicorn

# The PyMOL server targets an older MCP constructor that accepted a
# description keyword. The keyword is metadata-only and was removed upstream.
RUN sed -i '/description="PyMOL integration with advanced command parsing"/d' \
    /opt/mcps/pymol/pymol_mcp_server.py

# The published InterPro repository references jobs.manager but omits that
# package. Reuse its sibling MCP's generic subprocess job manager and add the
# one metadata method expected by the InterPro server.
RUN mkdir -p /opt/mcps/interpro_mcp/jobs \
    && cp /opt/mcps/protein-sol_mcp/src/jobs/__init__.py /opt/mcps/interpro_mcp/jobs/__init__.py \
    && cp /opt/mcps/protein-sol_mcp/src/jobs/manager.py /opt/mcps/interpro_mcp/jobs/manager.py \
    && sed -i 's/parent.parent.parent \/ "jobs"/parent.parent \/ "jobs"/' /opt/mcps/interpro_mcp/jobs/manager.py \
    && printf '%s\n' \
       '' \
       'def _get_server_info(self):' \
       '    jobs = self.list_jobs()' \
       '    return {"status": "success", "jobs_dir": str(self.jobs_dir), "total_jobs": jobs["total"]}' \
       '' \
       'JobManager.get_server_info = _get_server_info' \
       >> /opt/mcps/interpro_mcp/jobs/manager.py

RUN mkdir -p \
    /opt/mcps/interpro_mcp/jobs /opt/mcps/interpro_mcp/results /opt/mcps/interpro_mcp/tmp \
    /opt/mcps/msa_mcp/tmp/inputs /opt/mcps/msa_mcp/tmp/outputs \
    /opt/mcps/protein-sol_mcp/jobs /opt/mcps/protein-sol_mcp/results /opt/mcps/protein-sol_mcp/tmp \
    && chmod -R a+rX /opt/mcps \
    && chmod -R a+rwX \
       /opt/mcps/interpro_mcp/jobs /opt/mcps/interpro_mcp/results /opt/mcps/interpro_mcp/tmp \
       /opt/mcps/msa_mcp/tmp \
       /opt/mcps/protein-sol_mcp/jobs /opt/mcps/protein-sol_mcp/results /opt/mcps/protein-sol_mcp/tmp

RUN printf '%s\n' \
    '#!/bin/sh' \
    'set -eu' \
    'server=${1:-}' \
    'test -n "$server" || { echo "usage: public_python_mcp.sif SERVER" >&2; exit 2; }' \
    'shift' \
    'case "$server" in' \
    '  interpro_mcp) cd /opt/mcps/interpro_mcp; export PYTHONPATH=/opt/mcps/interpro_mcp:/opt/mcps/interpro_mcp/src:/opt/mcps/interpro_mcp/scripts; exec python src/server.py "$@" ;;' \
    '  msa_mcp) cd /opt/mcps/msa_mcp; export PYTHONPATH=/opt/mcps/msa_mcp/src; exec python src/server.py "$@" ;;' \
    '  protein-sol_mcp) cd /opt/mcps/protein-sol_mcp; export PYTHONPATH=/opt/mcps/protein-sol_mcp/src; exec python src/server.py "$@" ;;' \
    '  pymol) cd /opt/mcps/pymol; exec python pymol_mcp_server.py "$@" ;;' \
    '  pubmed) cd /opt/mcps/pubmed; exec python pubmed_server.py "$@" ;;' \
    '  *) echo "unknown MCP server: $server" >&2; exit 2 ;;' \
    'esac' \
    > /usr/local/bin/run-public-python-mcp \
    && chmod 755 /usr/local/bin/run-public-python-mcp

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENTRYPOINT ["/usr/local/bin/run-public-python-mcp"]
