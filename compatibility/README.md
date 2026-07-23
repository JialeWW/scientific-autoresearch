# Legacy machine-audit compatibility

The schema-1.5.4 machine-audit workflow is not part of the default Skill from
v0.3.1 onward. Its validator, formal report contract, status schema, and round
gate remain preserved in the immutable
[`v0.3.0`](https://github.com/JialeWW/scientific-autoresearch/tree/v0.3.0)
tag and release asset.

Use that frozen release only to inspect or continue an existing schema-1.5.4
run. Do not install its formal audit components for ordinary scientific work,
and do not mix their runtime-package provenance with v0.3.1.
