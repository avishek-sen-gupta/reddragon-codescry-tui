# Rev-Eng TUI

A top-down, read-only, multi-repo reverse engineering terminal UI that integrates [Codescry](https://github.com/avishek-sen-gupta/codescry) (repo surveying, integration detection, symbol resolution) and [Red Dragon](https://github.com/avishek-sen-gupta/red-dragon) (symbolic execution, IR, dataflow analysis).

[MIT License](LICENSE.md) | [Philosophy](PHILOSOPHY.md)

## What it does

Engineers exploring unfamiliar codebases can drill down from a high-level overview to function-level symbolic execution, with an LLM chat pane for contextual questions.

```
DashboardScreen ──Enter──▸ RepoScreen ──Enter──▸ FileScreen ──Enter──▸ FunctionScreen
(list all repos)          (file tree +          (source code +       (IR, CFG, VM state,
                           symbols +             symbols +            dataflow tabs +
                           integrations)         integrations)        LLM chat pane)

                           Escape goes back one screen at each level
```

### DashboardScreen
- Multi-repo overview from a JSON config
- Summary panel showing languages, frameworks, integration count

### RepoScreen
- File tree built from CTags symbols
- Symbol table (name, kind, line, scope, language)
- Integration signals table with confidence/direction coloring
- BGE embedding concretisation for signal classification

### FileScreen
- Syntax-highlighted source viewer
- File-scoped symbols and integration signals

### FunctionScreen
- **IR tab**: Color-coded three-address code instructions (19 opcodes)
- **CFG tab**: Text-based control flow graph with block labels, predecessors/successors (`o` opens SVG externally)
- **VM State tab**: Heap objects, call stack, path conditions from symbolic execution
- **Dataflow tab**: Def-use chains and variable dependencies (press `d` to toggle table/graph view)
- **Chat pane**: LLM-powered contextual Q&A about the code being viewed

## Setup

```bash
# Clone alongside codescry and red-dragon
cd ~/code
git clone <this-repo> rev-eng-tui
git clone <codescry-repo> codescry
git clone <red-dragon-repo> red-dragon

# Install
cd rev-eng-tui
poetry install

# Configure
cp config/repos.example.json config/repos.json
# Edit repos.json with your repo paths

# Run
poetry run retui --config config/repos.json
```

## Configuration

```json
{
  "version": 1,
  "repos": [
    {"name": "my-service", "path": "/code/svc", "languages": ["Java"], "auto_survey": true}
  ],
  "session_dir": "~/.rev-eng-tui/sessions",
  "llm": {"provider": "claude", "model": "claude-sonnet-4-20250514", "api_key_env": "ANTHROPIC_API_KEY"},
  "embedding": {"enabled": true, "model": "BAAI/bge-base-en-v1.5", "threshold": 0.62},
  "neo4j": {"enabled": false}
}
```

## Keybindings

| Key | Action |
|-----|--------|
| `Enter` | Drill into selected item |
| `Escape` | Go back one screen |
| `q` | Quit |
| `o` | Open CFG as SVG in system viewer (FunctionScreen) |
| `d` | Toggle dataflow table/graph view (FunctionScreen) |
| Arrow keys | Navigate tables and trees |

## Dependencies

- **[Codescry](https://github.com/avishek-sen-gupta/codescry)**: Repo surveying, CTags, integration detection, BGE embedding concretisation
- **[Red Dragon](https://github.com/avishek-sen-gupta/red-dragon)**: Tree-sitter parsing, IR lowering, CFG, dataflow analysis, symbolic execution
- **[Textual](https://textual.textualize.io/)**: TUI framework
- **[Anthropic](https://docs.anthropic.com/)**: Claude API for LLM chat
- **[CairoSVG](https://cairosvg.org/)**: SVG→PNG for CFG rendering
- **[sentence-transformers](https://www.sbert.net/)**: BGE embedding model

## Tests

```bash
poetry run pytest tests/ -v
```
