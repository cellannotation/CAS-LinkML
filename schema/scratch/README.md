STATUS: EXPERIMENTAL

## Aims

Generate a LinkML version of the [Cell Annotation Schema](https://github.com/cellannotation/cell-annotation-schema) that can be used to:

* _enhance validation with dynamic enumns_ (e.g. for CL) and internal reference checks (e.g. for CL).
  - longer term aim - build a better infrastructure for Link-ML dynamic enums using UberGraph (complete graph of OBO ontologies) & OBASK autosuggest endpoints. see https://github.com/linkml/linkml/issues/1775#issuecomment-1851002025

* _generate OWL/RDF from data to drive knowldge graphs_ (the RDF is also potentially useful in [cas-tools](https://github.com/cellannotation/cas-tools) - e.g. for calculating cell_id closure.)

*  _generate python data classes_ e.g. for use in [cas-tools](https://github.com/cellannotation/cas-tools)

The current approach is to incrementally build and test desired functionaly with a scratch version of the schema.
Once major issues are solved we can move to a more complete representation and start using generators for doc, JSON-schema, python Dataclasses etc. 
At this point we should also automate tests against CAS compliant.

Because the need for an OWL/RDF representation is most critical for BICAN, initial work is concentrating on modelling the BICAN extended version of cas ([snapshot release](https://github.com/cellannotation/cell-annotation-schema/releases/tag/untagged-1fcd76c4bd60071caa66)).

## RDF schema sketch (based on prior work in pandasaurus_cxg, VFB, BDSO/PCL)

- Annotation objects are instances of 'cluster' (PCL:0010001)  # could be improved.
- Clusters that form a simple nested hierarchy are related by subcluster_of ([RO:0015003](https://www.ebi.ac.uk/ols4/ontologies/ro/properties/http%253A%252F%252Fpurl.obolibrary.org%252Fobo%252FRO_0015003))
- Clusters are typed with a Cell Type term using an existential resriction on `composed primarily of` ([RO:0002473](https://www.ebi.ac.uk/ols4/ontologies/ro/properties/http%253A%252F%252Fpurl.obolibrary.org%252Fobo%252FRO_0002473))
- cell_label --> rdfs:label
proposal: annotation.cell_fullname --> skos:preflabel?

TBD: cluster --> labelset - should this use internal CAS IRIs?

## Files

*Inputs:*

- `schema/scratch/scratch.yaml` # Exptl schema
- `schema/scratch/data.yaml` # test data file
    
*Outputs:*

- `schema/scratch/data.ttl` # ttl file generated from data 
- `schema/scratch/scratch.json` # JSON schema output


## To run

generate json schema: `gen-json-schema scratch.yaml > scratch.json`

validate: `linkml-validate -s scratch.yaml data.yaml`

convert to rdf (ttl): `linkml-convert -s scratch.yaml data.yaml -o data.ttl`

Expand dynamic enums (via oaklib): 
    `vskit expand -s schema/scratch/scratch.yaml -o scratch_expanded.yaml CellTypeEnum`

## Notes:

The schema in scratch.yaml replicates the basic functionality needed to reproduce cas json schema.

It also goes some way to producing RDF following the standard annotation schema developed elsewhere
(pandasaurus_cxg, VFB, BDSO/PCL):
  - annotations are represented as individuals typed as clusters and are related in a hierarchy via subClusterOf
  - the correct predicate is specified for linking to Cell Type (CL term)
  - Dynamic enum & CL term linking works as a simple triple (requires expansion first or rdf gen fails)

### Still needs work:
  - CL term is not treated as an OWL entity (value type of axiom is string) - Relevant ticket: https://github.com/linkml/linkml/issues/1775
  - Dynamic enums specifying a CL term in the CL slot.  RDF conversion fails when this is in place, although oddly not validation. Relavant ticket https://github.com/linkml/linkml/issues/1775 ? 
  - Individuals are not being created for labelsets (no idea why when the same pattern is being used as for annotations)
  - There is no OWL typing of object properties (should be able to generate these from imports, so outside of LinkML)
  - Strictly Cluster --> CL term should be an existential restriction.  
    - Is there some way to fix this with LinkML OWL?
    - Could be hacked post-generation with SPARQL update.

## To explore

- Project generation: https://linkml.io/linkml/generators/project-generator.html
   - Note - the last we tried this, the doc was disappointing.  Some scope for contributing to improve.

- Mixins & inheritance - can we use these to compose CAP and BICAN releases.

## To complete

- The whole schema could potentially be pulled across by using 
[schema-automator](https://linkml.io/schema-automator/packages/importers.html#importing-from-json-schema) but so far, 
failing to install.  In the absence of this solution, it could be added manually.

- Some simple OWL infrastructure & ROBOT pipelines could pull minimal imports (APs, declarations)
