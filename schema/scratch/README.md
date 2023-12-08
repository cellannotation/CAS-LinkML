## To run

generate json schema: `gen-json-schema scratch.yaml`
validate: `linkml-validate -s scratch.yaml data.yaml`
convert to rdf (ttl): `linkml-convert -s scratch.yaml data.yaml -o data.ttl`

Expand dynamic enums (via oaklib): 
    `vskit expand -s schema/scratch/scratch.yaml -o scratch_expanded.yaml` # currently failing

# Notes:

The schema in sratch.yaml replicates the basic functionality needed to reproduce cas json schema.

It also goes some way to producing RDF following the standard annotation schema developed elsewhere
(pandasaurus_cxg, VFB, BDSO/PCL):
  - annotations are represented as individuals typed as clusters and are related in a hierarchy vis subClusterOf
  - the correct predicate is specified for linking to Cell Type (CL term)
  - linking to CL term (although see below)
  - dynamic enum spec example (although see below)

Progress but still needs work:
  - CL term is not treated as an OWL entity (value type of axiom is string)
  - dynamic enums specifying a CL term in the CL slot.  RDF conversion fails when this is in place, although oddly not  validation. This needs reporting
  - not creating individuals for labelset (no idea why when the same pattern is being used as for annotations)
  - OWL typing of object properties (should be able to generate these from imports, so outside of LinkML)
  - Strictly Cluster --> CL term should be an existential restriction.  
    - Is there some way to fix this with LinkML OWL?
    - Could be hacked pos-generation with SPARQL update.

## To explore

Project generation: https://linkml.io/linkml/generators/project-generator.html
Note - the last we tried this, the doc was disappointing.  Some scope for contributing to improve.

Mixins & inheritance - can we use these to compose CAP and BICAN releases.

## To complete

The whole schema could potentially be pulled across by using 
[schema-automator](https://linkml.io/schema-automator/packages/importers.html#importing-from-json-schema) but so far, 
failing to install.  In absence of this, could be done manually.

Some simple OWL infrastructure & ROBOT pipelines could pull minimal imports (APs, declarations)
