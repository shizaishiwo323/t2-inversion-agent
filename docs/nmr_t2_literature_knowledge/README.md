# NMR T2 Literature Knowledge Base

This directory converts selected NMR T2 theory/simulation PDFs into Agent-readable Markdown and JSON retrieval artifacts. It is designed so the T2 Agent can explain simulation and inversion results with source-backed citation keys without re-parsing PDFs every time.

## Files

- `papers/`: one Markdown knowledge card per PDF.
- `result_interpretation_scenarios.md`: human-readable scenario map from result patterns to mechanisms and citations.
- `result_interpretation_scenarios.json`: machine-readable version for Agent retrieval.
- `citation_registry.md`: citation key to PDF/card mapping.
- `literature_manifest.enriched.json`: extraction metadata, selected concepts, tags, and text-cache paths.
- `_extracted_text/`: extracted text cache for source checking.

## Scope

The knowledge base prioritizes theory, pore-scale simulation, inversion regularization, surface relaxation, diffusive coupling, restricted diffusion, FEM/FVM/LBM/matrix methods, internal gradients, CPMG sampling, Gaussian decomposition cautions, and T2-T2 interpretation.

## Use in reports

Use citation keys such as `[@BrownsteinTarr1979]` or combined citations such as `[@Whittall1991NNLS; @Coates1999NMRLogging]`. Keep interpretation probabilistic and data-aware.
