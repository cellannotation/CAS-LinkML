# CAS to OWL using LinkML 

Generate the LinkML schema from the CAS JSON schema.

```sh
schemauto import-json-schema schema/BICAN_schema.json > schema/schemauto/BICAN-schema.yaml
```

Convert [sample data](https://github.com/brain-bican/human-neocortex-middle-temporal-gyrus/blob/main/AIT_MTG.json) to OWL using [LinkML-OWL](https://github.com/linkml/linkml-owl)

```sh 
linkml-data2owl -s schema/schemauto/BICAN-schema.yaml schema/schemauto/sample_data/AIT_MTG.json -o schema/schemauto/AIT_MTG.owl
```