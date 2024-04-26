import os
import logging
from linkml.generators.pythongen import PythonGenerator
from linkml_runtime import SchemaView

from linkml_owl.util.loader_wrapper import load_structured_file
from linkml_owl.dumpers.owl_dumper import OWLDumper
from linkml_runtime.index.object_index import ObjectIndex

from schema_automator.importers.jsonschema_import_engine import JsonSchemaImportEngine
from schema_automator.utils.schemautils import write_schema

SCHEMA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../schema')
MODEL_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../schema/schemauto')
INPUT_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../schema/schemauto/sample_data')


CAS_SCHEMA_IN = os.path.join(SCHEMA_DIR, 'BICAN_schema.json')
SCHEMA_IN = os.path.join(MODEL_DIR, 'BICAN-schema2.yaml')
DATA_IN = os.path.join(INPUT_DIR, 'AIT_MTG2.json')
OWL_OUT = os.path.join(MODEL_DIR, 'AIT_MTG.ofn')


logger = logging.getLogger()
logger.setLevel(level=logging.DEBUG)


def run_data2owl():
    sv = SchemaView(SCHEMA_IN)
    python_module = PythonGenerator(SCHEMA_IN).compile_module()
    data = load_structured_file(DATA_IN, schemaview=sv, python_module=python_module)
    dumper = OWLDumper()
    dumper.schemaview = sv

    # container = py_mod.Container(entities=check.records)
    # dumper.object_index = ObjectIndex(container, schemaview=sv)
    # dumper.autofill = True

    doc = dumper.to_ontology_document(data, schema=sv.schema)
    for a in doc.ontology.axioms:
        print(f'AXIOM={a}')
    with open(OWL_OUT, 'w') as stream:
        stream.write(str(doc))


def convert_cas_schema_to_linkml():
    ie = JsonSchemaImportEngine()
    schema = ie.load(CAS_SCHEMA_IN, name="cell-annotation-schema", format='json', root_class_name=None)
    model_path = os.path.join(MODEL_DIR, 'BICAN-schema.yaml')
    write_schema(schema, model_path)


if __name__ == '__main__':
    convert_cas_schema_to_linkml()
    run_data2owl()
    print("Done")
