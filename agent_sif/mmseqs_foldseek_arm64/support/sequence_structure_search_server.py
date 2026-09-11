"""Unified MMseqs2 and Foldseek-family MCP server for Isambard ARM64.

The MMseqs2 endpoints run against a caller-supplied local MMseqs database.
The Foldseek web endpoints use the public search.foldseek.com API so that the
large public structure databases are not copied into project storage.  The
container also carries the native ARM64 command line programs for small local
file/directory searches; those programs are documented but intentionally not
added to PATH.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from contextlib import ExitStack
from pathlib import Path
from typing import Any, Literal, Optional

import requests
from fastmcp import FastMCP


mcp = FastMCP(name="mmseqs_foldseek")

API_BASE = os.environ.get("FOLDSEEK_API_BASE", "https://search.foldseek.com/api").rstrip("/")
MMSEQS_BIN = "/usr/bin/mmseqs"
FOLDSEEK_BIN = "/opt/foldseek/bin/foldseek"
FOLDMASON_BIN = "/opt/foldmason/bin/foldmason"
FOLDDISCO_BIN = "/opt/folddisco/bin/folddisco"
RIBOSEEK_BIN = "/opt/riboseek/bin/riboseek"
MMSEQS2_DB_PATH = os.path.expanduser(
    os.environ.get("MMSEQS2_DB_PATH", "~/.db/protein/uniref100/uniref100.fasta.db_padded")
)

_ALLOWED_ROOTS = tuple(
    Path(p)
    for p in (
        "/work",
        "/work",
    )
)
_ALIGNMENT_MODES = {"3diaa", "tmalign", "lolalign"}
_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "isambard-mmseqs-foldseek-mcp/1.0"})


def _is_under_allowed_root(path: Path) -> bool:
    resolved = path.resolve(strict=False)
    for root in _ALLOWED_ROOTS:
        try:
            resolved.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def _input_file(path: str, suffixes: Optional[set[str]] = None) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        raise ValueError("input path must be absolute")
    candidate = candidate.resolve(strict=True)
    if not _is_under_allowed_root(candidate):
        raise ValueError("input must be under /work")
    if not candidate.is_file():
        raise ValueError(f"input is not a file: {candidate}")
    if candidate.stat().st_size > 128 * 1024 * 1024:
        raise ValueError("input file exceeds the 128 MiB server limit")
    if suffixes and not any(str(candidate).lower().endswith(s) for s in suffixes):
        raise ValueError(f"unsupported file type: {candidate.name}")
    return candidate


def _output_dir(path: str) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        raise ValueError("output_dir must be absolute")
    if not _is_under_allowed_root(candidate):
        raise ValueError("output_dir must be under /work")
    candidate.mkdir(parents=True, exist_ok=True)
    return candidate.resolve(strict=True)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _http_json(method: str, url: str, **kwargs: Any) -> Any:
    timeout = kwargs.pop("timeout", (20, 120))
    response = _SESSION.request(method, url, timeout=timeout, **kwargs)
    if response.status_code >= 400:
        detail = response.text[:1000].strip()
        raise RuntimeError(f"Foldseek server HTTP {response.status_code}: {detail}")
    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError(f"Foldseek server returned non-JSON data from {url}") from exc


def _database_catalog() -> list[dict[str, Any]]:
    payload = _http_json("GET", f"{API_BASE}/databases")
    databases = payload.get("databases") if isinstance(payload, dict) else None
    if not isinstance(databases, list):
        raise RuntimeError("Foldseek database catalog has an unexpected shape")
    return [d for d in databases if isinstance(d, dict) and d.get("status") == "COMPLETE"]


def _scope_matches(entry: dict[str, Any], scope: str) -> bool:
    if scope == "structure":
        return not bool(entry.get("motif")) and not bool(entry.get("rna"))
    if scope == "complex":
        return bool(entry.get("complex")) and not bool(entry.get("interface"))
    if scope == "interface":
        return bool(entry.get("interface"))
    if scope == "motif":
        return bool(entry.get("motif"))
    if scope == "rna":
        return bool(entry.get("rna"))
    raise ValueError(f"unknown database scope: {scope}")


def _validated_databases(scope: str, requested: list[str]) -> list[str]:
    if not requested:
        raise ValueError("at least one database must be selected")
    catalog = _database_catalog()
    valid = {str(d["path"]): d for d in catalog if _scope_matches(d, scope)}
    invalid = [name for name in requested if name not in valid]
    if invalid:
        raise ValueError(
            f"invalid {scope} database(s): {invalid}; valid choices: {sorted(valid)}"
        )
    return list(dict.fromkeys(requested))


def _poll_ticket(ticket_id: str, max_wait_seconds: int, poll_seconds: float = 3.0) -> dict[str, Any]:
    if max_wait_seconds < 1 or max_wait_seconds > 7200:
        raise ValueError("max_wait_seconds must be in 1..7200")
    deadline = time.monotonic() + max_wait_seconds
    latest: dict[str, Any] = {"id": ticket_id, "status": "UNKNOWN"}
    while time.monotonic() < deadline:
        payload = _http_json("GET", f"{API_BASE}/ticket/{ticket_id}")
        if not isinstance(payload, dict):
            raise RuntimeError("ticket response has an unexpected shape")
        latest = payload
        status = str(payload.get("status", "UNKNOWN")).upper()
        if status == "COMPLETE":
            return payload
        if status in {"ERROR", "UNKNOWN", "RATELIMIT", "MAINTENANCE"}:
            raise RuntimeError(f"Foldseek job {ticket_id} ended with status {status}: {payload}")
        time.sleep(poll_seconds)
    raise TimeoutError(f"Foldseek job {ticket_id} did not finish within {max_wait_seconds}s; last={latest}")


def _submit_structure_job(
    *,
    endpoint: str,
    query_path: Path,
    databases: list[str],
    mode: Optional[str],
    output_dir: Path,
    max_wait_seconds: int,
    extra_fields: Optional[list[tuple[str, str]]] = None,
) -> tuple[str, dict[str, Any]]:
    data: list[tuple[str, str]] = [("database[]", db) for db in databases]
    data.append(("email", ""))
    if mode:
        data.append(("mode", mode))
    if extra_fields:
        data.extend(extra_fields)
    request_record = {
        "endpoint": endpoint,
        "query_path": str(query_path),
        "databases": databases,
        "mode": mode,
        "extra_fields": dict(extra_fields or []),
    }
    _write_json(output_dir / "request.json", request_record)
    with query_path.open("rb") as handle:
        response = _http_json(
            "POST",
            f"{API_BASE}/{endpoint.lstrip('/')}",
            files={"q": (query_path.name, handle, "application/octet-stream")},
            data=data,
            timeout=(20, 180),
        )
    if not isinstance(response, dict):
        raise RuntimeError("Foldseek submission response has an unexpected shape")
    status = str(response.get("status", "UNKNOWN")).upper()
    if status in {"RATELIMIT", "MAINTENANCE", "ERROR", "UNKNOWN"}:
        raise RuntimeError(f"Foldseek submission failed: {response}")
    ticket_id = str(response.get("id", ""))
    if not ticket_id:
        raise RuntimeError(f"Foldseek submission did not return a ticket: {response}")
    final = response if status == "COMPLETE" else _poll_ticket(ticket_id, max_wait_seconds)
    _write_json(output_dir / "ticket.json", final)
    return ticket_id, final


def _download_file(url: str, path: Path) -> Optional[str]:
    response = _SESSION.get(url, timeout=(20, 240), stream=True)
    if response.status_code == 404:
        return None
    if response.status_code >= 400:
        raise RuntimeError(f"download failed HTTP {response.status_code}: {response.text[:500]}")
    with path.open("wb") as handle:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                handle.write(chunk)
    return str(path)


def _alignment_rows(value: Any) -> list[dict[str, Any]]:
    """Flatten standard, complex and motif API alignment containers."""
    rows: list[dict[str, Any]] = []
    stack = [value]
    hit_keys = {
        "target", "eval", "score", "bits", "rmsd", "idfscore", "complexid"
    }
    while stack:
        item = stack.pop()
        if isinstance(item, list):
            stack.extend(reversed(item))
        elif isinstance(item, dict):
            if hit_keys.intersection(item):
                rows.append(item)
            else:
                stack.extend(reversed(list(item.values())))
    return rows


def _target_id(target: Any) -> Optional[str]:
    if not isinstance(target, str) or not target.strip():
        return None
    token = Path(target.split()[0]).name
    match = re.search(r"(?i)(?:^|[^a-z0-9])([0-9][a-z0-9]{3})(?:[^a-z0-9]|$)", token)
    return match.group(1).lower() if match else token


def _result_summary(payload: Any, limit: int = 10) -> dict[str, Any]:
    result_groups = payload.get("results", []) if isinstance(payload, dict) else []
    rows: list[dict[str, Any]] = []
    if isinstance(result_groups, list):
        for group in result_groups:
            if isinstance(group, dict):
                rows.extend(_alignment_rows(group.get("alignments", [])))

    top_hits: list[dict[str, Any]] = []
    unique_targets: list[str] = []
    seen_targets: set[str] = set()
    complex_ids: set[Any] = set()
    output_fields = (
        "target", "dbkey", "eval", "score", "bits", "prob", "seqId",
        "alntmscore", "qtmscore", "ttmscore", "complexid", "complexqtm",
        "complexttm", "rmsd", "nodecount", "idfscore", "queryresidues",
        "targetresidues",
    )
    for row in rows:
        target_id = _target_id(row.get("target"))
        if target_id and target_id not in seen_targets:
            seen_targets.add(target_id)
            unique_targets.append(target_id)
        if "complexid" in row:
            complex_ids.add(row["complexid"])
        if len(top_hits) < limit:
            keep = {key: row[key] for key in output_fields if key in row}
            if isinstance(keep.get("target"), str) and len(keep["target"]) > 240:
                keep["target"] = keep["target"][:237] + "..."
            if target_id:
                keep["target_id"] = target_id
            top_hits.append(keep)

    summary: dict[str, Any] = {
        "hit_count": len(rows),
        "unique_target_count": len(unique_targets),
        "top_hits": top_hits,
    }
    if complex_ids:
        summary["complex_count"] = len(complex_ids)
    return summary


def _fetch_standard_result(ticket_id: str, output_dir: Path) -> tuple[Any, str, Optional[str]]:
    payload = _http_json("GET", f"{API_BASE}/result/{ticket_id}/0")
    result_path = output_dir / "result.json"
    _write_json(result_path, payload)
    archive = _download_file(
        f"{API_BASE}/result/download/{ticket_id}", output_dir / "result.tar.gz"
    )
    return payload, str(result_path), archive


def _remote_foldseek_search(
    *,
    scope: Literal["structure", "complex", "interface"],
    query_path: str,
    output_dir: str,
    databases: list[str],
    alignment_mode: Literal["3diaa", "tmalign", "lolalign"],
    max_wait_seconds: int,
) -> dict[str, Any]:
    if alignment_mode not in _ALIGNMENT_MODES:
        raise ValueError(f"alignment_mode must be one of {sorted(_ALIGNMENT_MODES)}")
    query = _input_file(query_path, {".pdb", ".pdb.gz", ".cif", ".cif.gz", ".mmcif", ".mmcif.gz"})
    out = _output_dir(output_dir)
    dbs = _validated_databases(scope, databases)
    mode = alignment_mode
    if scope == "complex":
        mode = f"complex-{alignment_mode}"
    elif scope == "interface":
        mode = f"interface-{alignment_mode}"
    ticket, final = _submit_structure_job(
        endpoint="ticket",
        query_path=query,
        databases=dbs,
        mode=mode,
        output_dir=out,
        max_wait_seconds=max_wait_seconds,
    )
    payload, result_path, archive = _fetch_standard_result(ticket, out)
    return {
        "scope": scope,
        "ticket": ticket,
        "status": final.get("status"),
        "alignment_mode": alignment_mode,
        "databases": dbs,
        "result_json": result_path,
        "result_archive": archive,
        "summary": _result_summary(payload),
        "output_directory": str(out),
    }


def _generate_msa_impl(
    *,
    sequence: Optional[str] = None,
    fasta_file: Optional[str] = None,
    sequence_name: str = "query",
    output_dir: Optional[str] = None,
    database_path: Optional[str] = None,
    gpu: bool = False,
    cuda_device: Optional[int] = None,
    threads: int = 16,
    sensitivity: float = 7.5,
    num_iterations: int = 3,
    e_value: float = 0.001,
    max_seqs: int = 100000,
    return_format: Literal["a3m", "path"] = "a3m",
) -> str:
    if (sequence is None) == (fasta_file is None):
        raise ValueError("provide exactly one of sequence or fasta_file")
    database = Path(database_path or MMSEQS2_DB_PATH).expanduser()
    if not database.exists():
        raise FileNotFoundError(f"MMseqs2 database not found: {database}")
    if not 1 <= threads <= 128:
        raise ValueError("threads must be in 1..128")
    if output_dir is None:
        work_dir = Path(tempfile.mkdtemp(prefix="mmseqs2_"))
        remove_work_dir = True
    else:
        work_dir = _output_dir(output_dir)
        remove_work_dir = False
    sequence_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", sequence_name)[:120] or "query"
    try:
        if sequence is not None:
            clean_sequence = re.sub(r"\s+", "", sequence).upper()
            if not clean_sequence or not re.fullmatch(r"[A-Z*.-]+", clean_sequence):
                raise ValueError("sequence is empty or contains unsupported characters")
            query_fasta = work_dir / f"{sequence_name}.fasta"
            query_fasta.write_text(f">{sequence_name}\n{clean_sequence}\n", encoding="utf-8")
        else:
            query_fasta = _input_file(str(fasta_file), {".fa", ".faa", ".fasta", ".fas"})
            first = query_fasta.read_text(encoding="utf-8", errors="replace").splitlines()[0]
            if first.startswith(">"):
                sequence_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", first[1:].split()[0])[:120] or "query"

        query_db = work_dir / f"{sequence_name}_db"
        result_db = work_dir / f"{sequence_name}_result_db"
        msa_db = work_dir / f"{sequence_name}_msa_db"
        temp_dir = work_dir / "tmp"
        unpacked = work_dir / f"{sequence_name}_msa"
        output_a3m = work_dir / f"{sequence_name}.a3m"
        env = os.environ.copy()
        if cuda_device is not None:
            env["CUDA_VISIBLE_DEVICES"] = str(cuda_device)

        def run(args: list[str]) -> None:
            completed = subprocess.run(args, check=False, text=True, capture_output=True, env=env)
            if completed.stdout:
                print(completed.stdout, file=sys.stderr, end="")
            if completed.stderr:
                print(completed.stderr, file=sys.stderr, end="")
            if completed.returncode != 0:
                raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(args)}")

        run([MMSEQS_BIN, "createdb", str(query_fasta), str(query_db)])
        search = [
            MMSEQS_BIN, "search", str(query_db), str(database), str(result_db), str(temp_dir),
            "--threads", str(threads), "-s", str(sensitivity),
            "--num-iterations", str(num_iterations), "-e", str(e_value),
            "--max-seqs", str(max_seqs),
        ]
        if gpu:
            search.extend(["--gpu", "1"])
        run(search)
        run([
            MMSEQS_BIN, "result2msa", str(query_db), str(database), str(result_db), str(msa_db),
            "--msa-format-mode", "6",
        ])
        unpacked.mkdir(parents=True, exist_ok=True)
        run([MMSEQS_BIN, "unpackdb", str(msa_db), str(unpacked), "--unpack-suffix", ".a3m"])
        with output_a3m.open("w", encoding="utf-8") as target:
            for a3m in sorted(unpacked.glob("*.a3m")):
                target.write(a3m.read_text(encoding="utf-8", errors="replace"))
        result = output_a3m.read_text(encoding="utf-8") if return_format == "a3m" else str(output_a3m)

        for base in (query_db, result_db, msa_db):
            for candidate in work_dir.glob(base.name + "*"):
                if candidate.is_dir():
                    shutil.rmtree(candidate, ignore_errors=True)
                elif candidate != output_a3m and candidate != query_fasta:
                    candidate.unlink(missing_ok=True)
        shutil.rmtree(temp_dir, ignore_errors=True)
        shutil.rmtree(unpacked, ignore_errors=True)
        return result
    finally:
        if remove_work_dir:
            shutil.rmtree(work_dir, ignore_errors=True)


@mcp.tool()
def list_search_databases() -> dict[str, Any]:
    """List the live public Foldseek/Folddisco/Riboseek databases by usable scope."""
    catalog = _database_catalog()
    grouped: dict[str, list[dict[str, str]]] = {}
    for scope in ("structure", "complex", "interface", "motif", "rna"):
        grouped[scope] = [
            {"name": str(d.get("name")), "path": str(d.get("path")), "version": str(d.get("version"))}
            for d in catalog
            if _scope_matches(d, scope)
        ]
    return {"api_base": API_BASE, "database_count": len(catalog), "scopes": grouped}


@mcp.tool()
def generate_msa(
    sequence: Optional[str] = None,
    fasta_file: Optional[str] = None,
    sequence_name: str = "query",
    output_dir: Optional[str] = None,
    database_path: Optional[str] = None,
    gpu: bool = False,
    cuda_device: Optional[int] = None,
    threads: int = 16,
    sensitivity: float = 7.5,
    num_iterations: int = 3,
    e_value: float = 0.001,
    max_seqs: int = 100000,
    return_format: Literal["a3m", "path"] = "a3m",
) -> str:
    """Generate an A3M with native MMseqs2 and a caller-supplied local database."""
    with contextlib.redirect_stdout(sys.stderr):
        return _generate_msa_impl(
            sequence=sequence, fasta_file=fasta_file, sequence_name=sequence_name,
            output_dir=output_dir, database_path=database_path, gpu=gpu,
            cuda_device=cuda_device, threads=threads, sensitivity=sensitivity,
            num_iterations=num_iterations, e_value=e_value, max_seqs=max_seqs,
            return_format=return_format,
        )


@mcp.tool()
def generate_msa_from_file(
    fasta_file: str,
    output_dir: str,
    database_path: Optional[str] = None,
    gpu: bool = False,
    cuda_device: Optional[int] = None,
    threads: int = 16,
    sensitivity: float = 7.5,
    num_iterations: int = 3,
    e_value: float = 0.001,
    max_seqs: int = 100000,
) -> str:
    """Generate and retain an A3M from an input FASTA with native MMseqs2."""
    with contextlib.redirect_stdout(sys.stderr):
        return _generate_msa_impl(
            fasta_file=fasta_file, output_dir=output_dir, database_path=database_path,
            gpu=gpu, cuda_device=cuda_device, threads=threads, sensitivity=sensitivity,
            num_iterations=num_iterations, e_value=e_value, max_seqs=max_seqs,
            return_format="path",
        )


@mcp.tool()
def foldseek_structure_search(
    query_path: str,
    output_dir: str,
    databases: list[str] = ["pdb100"],
    alignment_mode: Literal["3diaa", "tmalign", "lolalign"] = "3diaa",
    max_wait_seconds: int = 1200,
) -> dict[str, Any]:
    """Search one or more protein chains against public structure collections."""
    return _remote_foldseek_search(
        scope="structure", query_path=query_path, output_dir=output_dir,
        databases=databases, alignment_mode=alignment_mode, max_wait_seconds=max_wait_seconds,
    )


@mcp.tool()
def foldseek_complex_search(
    query_path: str,
    output_dir: str,
    databases: list[str] = ["pdb100"],
    alignment_mode: Literal["3diaa", "tmalign", "lolalign"] = "3diaa",
    max_wait_seconds: int = 1200,
) -> dict[str, Any]:
    """Search a complete multi-chain protein complex with Foldseek-Multimer."""
    return _remote_foldseek_search(
        scope="complex", query_path=query_path, output_dir=output_dir,
        databases=databases, alignment_mode=alignment_mode, max_wait_seconds=max_wait_seconds,
    )


@mcp.tool()
def foldseek_interface_search(
    query_path: str,
    output_dir: str,
    databases: list[str] = ["pdb_interface"],
    alignment_mode: Literal["3diaa", "tmalign", "lolalign"] = "3diaa",
    max_wait_seconds: int = 1200,
) -> dict[str, Any]:
    """Search protein-protein interfaces rather than whole chains or complexes."""
    return _remote_foldseek_search(
        scope="interface", query_path=query_path, output_dir=output_dir,
        databases=databases, alignment_mode=alignment_mode, max_wait_seconds=max_wait_seconds,
    )


@mcp.tool()
def folddisco_motif_search(
    query_path: str,
    motif_residues: str,
    output_dir: str,
    databases: list[str] = ["pdb_folddisco"],
    max_wait_seconds: int = 1200,
) -> dict[str, Any]:
    """Search discontinuous protein residue motifs with Folddisco.

    motif_residues uses FoldDisco syntax such as ``A64,A86,A90`` or
    ``B57:H,B102:ST,C195``.  A maximum of 32 motif residues is accepted.
    Ligand atoms are not part of the FoldDisco residue motif and must be
    evaluated separately for ligand-conditioned design benchmarks.
    """
    query = _input_file(query_path, {".pdb", ".pdb.gz", ".cif", ".cif.gz", ".mmcif", ".mmcif.gz"})
    residues = [item.strip() for item in motif_residues.split(",") if item.strip()]
    if not 1 <= len(set(residues)) <= 32:
        raise ValueError("motif_residues must contain 1..32 unique residues")
    if any(not re.fullmatch(r"(?:[A-Za-z0-9]+)?-?\d+(?::[A-Za-z]+)?", item) for item in residues):
        raise ValueError("invalid FoldDisco motif syntax")
    out = _output_dir(output_dir)
    dbs = _validated_databases("motif", databases)
    ticket, final = _submit_structure_job(
        endpoint="ticket/folddisco", query_path=query, databases=dbs, mode=None,
        output_dir=out, max_wait_seconds=max_wait_seconds,
        extra_fields=[("motif", ",".join(residues))],
    )
    payload = _http_json("GET", f"{API_BASE}/result/folddisco/{ticket}")
    result_path = out / "result.json"
    _write_json(result_path, payload)
    archive = _download_file(
        f"{API_BASE}/result/folddisco/download/{ticket}", out / "result.tar.gz"
    )
    return {
        "scope": "motif", "ticket": ticket, "status": final.get("status"),
        "motif_residues": ",".join(residues), "databases": dbs,
        "result_json": str(result_path), "result_archive": archive,
        "summary": _result_summary(payload), "output_directory": str(out),
        "benchmark_note": "FoldDisco matches protein residue geometry; ligand identity/atoms need a separate evaluator.",
    }


@mcp.tool()
def foldmason_structure_msa(
    query_paths: list[str],
    output_dir: str,
    max_wait_seconds: int = 1200,
) -> dict[str, Any]:
    """Align 2..4999 uploaded protein structures with FoldMason."""
    if not 2 <= len(query_paths) <= 4999:
        raise ValueError("FoldMason needs 2..4999 structures")
    queries = [
        _input_file(path, {".pdb", ".pdb.gz", ".cif", ".cif.gz", ".mmcif", ".mmcif.gz"})
        for path in query_paths
    ]
    out = _output_dir(output_dir)
    _write_json(out / "request.json", {"query_paths": [str(p) for p in queries]})
    with ExitStack() as stack:
        files: list[tuple[str, tuple[str, Any, str]]] = []
        data: list[tuple[str, str]] = []
        for query in queries:
            handle = stack.enter_context(query.open("rb"))
            files.append(("queries[]", (query.name, handle, "application/octet-stream")))
            data.append(("fileNames[]", query.name))
        response = _http_json(
            "POST", f"{API_BASE}/ticket/foldmason", files=files, data=data, timeout=(20, 240)
        )
    ticket = str(response.get("id", "")) if isinstance(response, dict) else ""
    if not ticket:
        raise RuntimeError(f"FoldMason submission did not return a ticket: {response}")
    final = response if str(response.get("status", "")).upper() == "COMPLETE" else _poll_ticket(ticket, max_wait_seconds)
    _write_json(out / "ticket.json", final)
    payload = _http_json("GET", f"{API_BASE}/result/foldmason/{ticket}")
    result_path = out / "foldmason.json"
    _write_json(result_path, payload)
    return {
        "ticket": ticket, "status": final.get("status"), "query_count": len(queries),
        "result_json": str(result_path), "output_directory": str(out),
    }


@mcp.tool()
def riboseek_rna_search(
    sequence: Optional[str] = None,
    fasta_file: Optional[str] = None,
    output_dir: str = "",
    databases: list[str] = ["rnadb"],
    max_wait_seconds: int = 1200,
) -> dict[str, Any]:
    """Search an RNA sequence against the public AF3 RNA collection with Riboseek."""
    if (sequence is None) == (fasta_file is None):
        raise ValueError("provide exactly one of sequence or fasta_file")
    out = _output_dir(output_dir)
    dbs = _validated_databases("rna", databases)
    if fasta_file is not None:
        query = _input_file(fasta_file, {".fa", ".fasta", ".fna", ".fas"})
    else:
        clean = re.sub(r"\s+", "", str(sequence)).upper().replace("T", "U")
        if not clean or not re.fullmatch(r"[ACGUN.-]+", clean):
            raise ValueError("RNA sequence contains unsupported characters")
        query = out / "query.fasta"
        query.write_text(f">query\n{clean}\n", encoding="utf-8")
    ticket, final = _submit_structure_job(
        endpoint="ticket/riboseek", query_path=query, databases=dbs, mode=None,
        output_dir=out, max_wait_seconds=max_wait_seconds,
    )
    payload, result_path, archive = _fetch_standard_result(ticket, out)
    return {
        "scope": "rna", "ticket": ticket, "status": final.get("status"),
        "databases": dbs, "result_json": result_path, "result_archive": archive,
        "summary": _result_summary(payload), "output_directory": str(out),
    }


if __name__ == "__main__":
    mcp.run()
