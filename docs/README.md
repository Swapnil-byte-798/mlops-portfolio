# MLOps Portfolio study material

Updated 29 October 2026. These documents describe the repaired implementation, measured fixture results, failure handling and the boundaries of each module.

| Read this for | Markdown | PDF |
|---|---|---|
| Architecture, data flow and evidence | [How it works](how-it-works.md) | [Architecture guide](MLOps-How-It-Works.pdf) |
| Conversational interview answers | [Interview Q&A](interview-questions.md) | [Interview guide](MLOps-Interview-Questions.pdf) |
| Fundamentals, analogies and advanced limits | [Tools primer](tools-primer.md) | [Tools guide](MLOps-Tools-Primer.pdf) |
| All three guides together | [Complete guide](MLOps_Portfolio_Study_Guide.md) | [Complete PDF](MLOps_Portfolio_Study_Guide.pdf) |

The complete guide replaces the earlier study snapshot. Start with the primer, follow the architecture, then practise the questions. [Verification](verification.md) distinguishes real service runs, local fault injection and unverified live AWS behavior.

## Rebuild

From the repository root:

```bash
python -m pip install -r requirements-docs.txt
python scripts/render_study_docs.py
```

The Python renderer builds all four PDFs from the maintained three Markdown sources and assembles the complete Markdown edition. It checks page text bounds and missing glyphs. DejaVu Sans fonts are required; set `STUDY_FONT_DIR` if they are outside the default Linux font location.
