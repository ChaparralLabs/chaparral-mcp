# chaparral-mcp

MCP server that exposes [Chaparral](https://chaparral.ai) proteomics data to AI agents — Claude, GitHub Copilot, GPT-4, and any other MCP-compatible host.

## What it does

Gives your AI assistant read access to your Chaparral experiments and search results so you can ask questions like:

> *"Show me the QC summary for my last DDA experiment."*
> *"Which peptides from GAPDH were identified at 1% FDR?"*
> *"Give me the PRM quant table for the phospho panel."*

## Tools exposed

| Tool | Description |
|---|---|
| `list_projects` | List all projects in the organisation |
| `list_experiments` | List experiments in a project |
| `list_search_results` | List DDA/DIA/PRM search results for an experiment |
| `get_qc_dashboard` | QC metrics — protein IDs, FDR, precursor accuracy (DDA or DIA) |
| `get_peptides` | Paginated peptide identifications at 1% FDR |
| `get_protein_psms` | All PSMs for a specific protein (DDA or DIA) |
| `get_ptm_sites` | PTM site localisation data (all proteins or one) |
| `get_prm_quant` | Peptide-level quant table from a PRM search |
| `stream_results` | Full quantitative result set for downstream analysis |

## Quick start (Claude Desktop)

### 1. Get an API key

Log in to [app.chaparral.ai](https://app.chaparral.ai) → **Settings → API Keys → Create**.  
Copy the key (starts with `chpr_live_`).

### 2. Install

```bash
pip install chaparral-mcp
```

Or from source:

```bash
git clone https://github.com/ChaparralLabs/chaparral-mcp
cd chaparral-mcp
pip install -e .
```

### 3. Configure Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "chaparral": {
      "command": "chaparral-mcp",
      "env": {
        "CHAPARRAL_API_KEY": "chpr_live_YOUR_KEY_HERE"
      }
    }
  }
}
```

### 4. Restart Claude Desktop

The **chaparral** server will appear in the tools panel (hammer icon).

### 5. Ask a question

> *"List my Chaparral projects, then show me the QC dashboard for the most recent DDA search."*

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `CHAPARRAL_API_KEY` | Yes | — | Long-lived API key (`chpr_live_...`) |
| `CHAPARRAL_BASE_URL` | No | `https://api.chaparral.ai` | Override for testing (`https://api.testing.chaparral.ai`) |

## Use with GitHub Copilot (VS Code)

Add to `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "chaparral": {
      "type": "stdio",
      "command": "chaparral-mcp",
      "env": {
        "CHAPARRAL_API_KEY": "${env:CHAPARRAL_API_KEY}"
      }
    }
  }
}
```

Then enable MCP in Copilot Chat (Agent mode).

## Use with testing environment

```json
{
  "mcpServers": {
    "chaparral-testing": {
      "command": "chaparral-mcp",
      "env": {
        "CHAPARRAL_API_KEY": "chpr_live_YOUR_TESTING_KEY",
        "CHAPARRAL_BASE_URL": "https://api.testing.chaparral.ai"
      }
    }
  }
}
```

## Requirements

- Python 3.10+
- `chaparral >= 0.3.0`
- `mcp >= 1.0.0`

## License

MIT
