# Method modules

Each analytical method is one YAML file that agents read to plan and run an analysis. A new method needs a new file
only; the core does not change. Status: drafts, to be refined when the analysis engine is built.

| Field | Meaning |
| :--- | :--- |
| `id`, `name`, `references`, `summary` | what the method is and where it comes from |
| `research_design` | how the method links purpose, research questions and theory: `purpose`, `questions`, `prior_theory`, `reasoning`, `theory_output` (`docs/research-design.md`) |
| `code_types` | kinds of codes the method uses |
| `relation_types` | relations the method allows between concepts (`id`, `description`) |
| `phases` | ordered phases: `goal`, `input`, `output`, optional `allowed_relations`, what the model does (`model_role`) and where the human decides (`human_gate`) |
| `practices` | method-wide practices (constant comparison, memoing, reflexivity) |
| `conclusions` | how the method reaches its conclusions |

Next: SKAD (sociology of knowledge approach to discourse, Keller), the method of the first study. Planned: Mayring's qualitative content analysis, ethnography, narrative and discourse analysis, mixed-methods
designs, and non-LLM methods (embedding clusters, topic models).
