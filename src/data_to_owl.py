import os
from linkml.generators.pythongen import PythonGenerator
from linkml_runtime import SchemaView

from linkml_owl.util.loader_wrapper import load_structured_file
from linkml_owl.dumpers.owl_dumper import OWLDumper

MODEL_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../schema/schemauto')
INPUT_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../schema/schemauto/sample_data')


SCHEMA_IN = os.path.join(MODEL_DIR, 'BICAN-schema.yaml')
DATA_IN = os.path.join(INPUT_DIR, 'AIT_MTG.json')
OWL_OUT = os.path.join(MODEL_DIR, 'AIT_MTG.ofn')


def run_data2owl():
    sv = SchemaView(SCHEMA_IN)
    python_module = PythonGenerator(SCHEMA_IN).compile_module()
    data = load_structured_file(DATA_IN, schemaview=sv, python_module=python_module)
    dumper = OWLDumper()
    dumper.schemaview = sv

    doc = dumper.to_ontology_document(data, schema=sv.schema)
    for a in doc.ontology.axioms:
        print(f'AXIOM={a}')
    with open(OWL_OUT, 'w') as stream:
        stream.write(str(doc))


if __name__ == '__main__':
    run_data2owl()
    print("Done")
