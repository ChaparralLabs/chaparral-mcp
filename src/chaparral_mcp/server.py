"""Chaparral MCP Server.

Exposes Chaparral proteomics data as MCP tools so that AI agents
(Claude, Copilot, GPT-4, etc.) can query experiments, search results,
QC metrics, peptides, proteins, PTM sites, XIC traces, and PRM quant
data via natural language.

Configuration (environment variables):
    CHAPARRAL_API_KEY   — required; your long-lived API key (chpr_live_...)
    CHAPARRAL_BASE_URL  — optional; defaults to https://api.chaparral.ai
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from mcp.server.fastmcp import FastMCP

from chaparral import Client

# ---------------------------------------------------------------------------
# FastMCP server instance
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "chaparral",
    instructions=(
        "You have access to the Chaparral proteomics platform. "
        "Use these tools to explore projects, experiments, and mass-spec search results. "
        "Always start by listing projects or experiments so you know which IDs to use. "
        "search_result_id values look like UUIDs. "
        "For DDA experiments use get_qc_dashboard; for DIA use get_qc_dashboard_dia. "
        "For PRM experiments use get_prm_quant. "
        "get_peptides returns paginated results — increase per_page or page to get more."
    ),
)


# ---------------------------------------------------------------------------
# Shared client helper (cached per-process)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _client() -> Client:
    api_key = os.environ.get("CHAPARRAL_API_KEY")
    base_url = os.environ.get("CHAPARRAL_BASE_URL")
    kwargs: dict[str, Any] = {}
    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["base_url"] = base_url
    return Client(**kwargs)


def _dump(obj: Any) -> Any:
    """Convert a Pydantic model (or list thereof) to a JSON-safe dict."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, list):
        return [_dump(item) for item in obj]
    return obj


# ---------------------------------------------------------------------------
# Tool 1 — list_projects
# ---------------------------------------------------------------------------

@mcp.tool()
def list_projects() -> list[dict]:
    """List all projects in the organisation.

    Returns a list of projects with their IDs, names, and descriptions.
    Use a project_id from this list when calling list_experiments.
    """
    return _dump(_client().list_projects())


# ---------------------------------------------------------------------------
# Tool 2 — list_experiments
# ---------------------------------------------------------------------------

@mcp.tool()
def list_experiments(project_id: str) -> list[dict]:
    """List all experiments that belong to a project.

    Args:
        project_id: UUID of the project (from list_projects).

    Returns a list of experiments with IDs, names, tags, and status.
    Use an experiment_id from this list when calling list_search_results.
    """
    return _dump(_client().list_experiments_by_project(project_id))


# ---------------------------------------------------------------------------
# Tool 3 — list_search_results
# ---------------------------------------------------------------------------

@mcp.tool()
def list_search_results(experiment_id: str) -> list[dict]:
    """List all search results (DDA / DIA / PRM) for an experiment.

    Args:
        experiment_id: UUID of the experiment (from list_experiments).

    Returns a list of search results with their IDs, status, search type,
    and timestamps. Use a search_result_id from this list for all downstream tools.
    """
    return _dump(_client().list_search_results_by_experiment(experiment_id))


# ---------------------------------------------------------------------------
# Tool 4 — get_qc_dashboard
# ---------------------------------------------------------------------------

@mcp.tool()
def get_qc_dashboard(search_result_id: str, mode: str = "dda") -> dict:
    """Return the QC dashboard for a completed search.

    Args:
        search_result_id: UUID of the search result.
        mode: "dda" (default) or "dia". Use "dia" for data-independent acquisition
              searches. PRM searches do not have a QC dashboard — use get_prm_quant.

    Returns protein/peptide ID counts, FDR values, and per-file statistics.
    This is the first thing to check after a search completes.
    """
    c = _client()
    if mode == "dia":
        return _dump(c.qc_dashboard_dia(search_result_id))
    return _dump(c.qc_dashboard(search_result_id))


# ---------------------------------------------------------------------------
# Tool 5 — get_peptides
# ---------------------------------------------------------------------------

@mcp.tool()
def get_peptides(
    search_result_id: str,
    page: int = 1,
    per_page: int = 100,
) -> list[dict]:
    """Return a paginated list of identified peptides from a search result.

    Peptides are pre-filtered at q-value < 0.01 by the server.

    Args:
        search_result_id: UUID of the search result.
        page: Page number (1-based). Default 1.
        per_page: Number of peptides per page. Default 100, max 1000.

    Returns peptide sequences, associated proteins, charge states, scores,
    retention times, and source files.
    """
    return _dump(_client().get_peptides(search_result_id, page=page, per_page=per_page))


# ---------------------------------------------------------------------------
# Tool 6 — get_protein_psms
# ---------------------------------------------------------------------------

@mcp.tool()
def get_protein_psms(
    search_result_id: str,
    protein: str,
    mode: str = "dda",
) -> list[dict]:
    """Return all PSMs (peptide-spectrum matches) for a specific protein.

    Args:
        search_result_id: UUID of the search result.
        protein: Protein accession or name (e.g. "P04406" or "GAPDH_HUMAN").
        mode: "dda" (default) or "dia".

    Returns individual PSMs with peptide sequence, charge, score, q-value,
    retention time, source file, and scan number.
    """
    c = _client()
    if mode == "dia":
        return _dump(c.get_protein_psms_dia(search_result_id, protein))
    return _dump(c.get_protein_psms(search_result_id, protein))


# ---------------------------------------------------------------------------
# Tool 7 — get_ptm_sites
# ---------------------------------------------------------------------------

@mcp.tool()
def get_ptm_sites(
    search_result_id: str,
    protein: str | None = None,
) -> list[dict]:
    """Return post-translational modification (PTM) site localisation data.

    Args:
        search_result_id: UUID of the search result.
        protein: Optional protein accession to filter results to one protein.
                 If omitted, returns PTM sites across all proteins in the search.

    Returns residue positions, modification masses, localisation scores,
    and site-level q-values.
    """
    c = _client()
    if protein:
        return _dump(c.get_ptm_sites(search_result_id, protein))
    return _dump(c.get_all_ptm_sites(search_result_id))


# ---------------------------------------------------------------------------
# Tool 8 — get_prm_quant
# ---------------------------------------------------------------------------

@mcp.tool()
def get_prm_quant(search_result_id: str) -> list[dict]:
    """Return peptide-level quantification data from a PRM search.

    Args:
        search_result_id: UUID of a PRM search result.

    Returns a table of peptides × samples with response values (peak areas)
    suitable for building a quantitative report or heatmap.
    Only valid for PRM (parallel reaction monitoring) search results.
    """
    return _dump(_client().get_prm_quant(search_result_id))


# ---------------------------------------------------------------------------
# Tool 9 — stream_results
# ---------------------------------------------------------------------------

@mcp.tool()
def stream_results(
    search_result_id: str,
    q_value_cutoff: float = 0.01,
) -> Any:
    """Stream the full quantitative result table for a search.

    Returns all quantified peptides/precursors as a structured payload.
    Useful for downstream analysis, filtering, or export.

    Args:
        search_result_id: UUID of the search result.
        q_value_cutoff: Maximum q-value to include (default 0.01 = 1% FDR).

    Returns a JSON-serialisable object (list of dicts or nested structure)
    with the complete result set. For very large datasets this may be slow —
    prefer get_peptides with pagination for interactive queries.
    """
    filters = {"q_value": q_value_cutoff}
    result = _client().stream_results(search_result_id, filters=filters)
    # stream_results may return bytes (Parquet) or parsed JSON
    if isinstance(result, (bytes, bytearray)):
        return {"format": "parquet", "size_bytes": len(result), "note": "Binary Parquet payload — save to file for analysis"}
    return result


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
