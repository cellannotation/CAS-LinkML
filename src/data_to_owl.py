import json
import os
import logging
from typing import List

from linkml.generators.pythongen import PythonGenerator
from linkml_runtime import SchemaView

from linkml_owl.util.loader_wrapper import load_structured_file
from linkml_owl.dumpers.owl_dumper import OWLDumper
from linkml_runtime.index.object_index import ObjectIndex

from schema_automator.importers.jsonschema_import_engine import JsonSchemaImportEngine
from schema_automator.utils.schemautils import write_schema

import rdflib
from linkml_runtime.dumpers import rdflib_dumper
from linkml_runtime.linkml_model import SchemaDefinition
from linkml import generators as generators
from linkml_runtime.utils.compile_python import compile_python
from linkml.validator import Validator
from linkml.utils import validation
from linkml.utils.datautils import (
    get_loader,
    _get_format
    )

from linkml_runtime.loaders import yaml_loader
from oaklib.utilities.subsets.value_set_expander import ValueSetExpander, ValueSetConfiguration

SCHEMA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../schema')
MODEL_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../schema/schemauto')
INPUT_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../schema/schemauto/sample_data')


CAS_SCHEMA_IN = os.path.join(SCHEMA_DIR, 'BICAN_schema.json')
SCHEMA_IN = os.path.join(MODEL_DIR, 'BICAN-schema2.yaml')
SCHEMA_IN3 = os.path.join(MODEL_DIR, 'BICAN-schema3.yaml')
SCHEMA_EXPANDED = os.path.join(MODEL_DIR, 'BICAN-schema3-expanded.yaml')

DATA_IN = os.path.join(INPUT_DIR, 'AIT_MTG2.json')
DATA_IN3 = os.path.join(INPUT_DIR, 'AIT_MTG3.json')

OWL_OUT = os.path.join(MODEL_DIR, 'AIT_MTG.ofn')
OWL_OUT2 = os.path.join(MODEL_DIR, 'AIT_MTG_rdf.owl')


logger = logging.getLogger()
logger.setLevel(level=logging.DEBUG)


def run_rdf_dumper(schema_path, data_path, output_path, validate=True):
    # gen, output, _ = _generate_framework_output(schema, PYTHON_DATACLASSES)
    target_class = "GeneralCellAnnotationOpenStandard"

    with open(data_path) as f:
        instance = json.load(f)

    if validate:
        validator = Validator(schema_path)
        report = validator.validate(instance)
        print(report)
        print("DONE VALIDATING")

    gen = generators.PythonGenerator(schema_path)
    # gen = generators.PythonGenerator(schema=SchemaDefinition(schema))
    output = gen.serialize()

    python_module = compile_python(output)
    py_target_class = getattr(python_module, target_class)

    try:
        py_inst = py_target_class(**instance)
    except Exception as e:
        print(f"Could not instantiate {py_target_class} from the data; exception: {e}")
        return None

    # schemaview = SchemaView(SchemaDefinition(**schema))
    schemaview = SchemaView(schema_path)

    # if validate:
    #     input_format = _get_format(data_path)
    #     loader = get_loader(input_format)
    #     # py_target_class = python_module.__dict__[target_class]
    #     inargs = {"schemaview": schemaview,
    #               "fmt": input_format,
    #               "schema": schema_path}
    #     obj = loader.load(source=data_path, target_class=py_target_class, **inargs)
    #     validation.validate_object(obj, schema_path)

    g = rdflib_dumper.as_rdf_graph(
        py_inst,
        schemaview=schemaview,
        prefix_map={
            "CAS": "https://cellular-semantics.sanger.ac.uk/ontology/CAS/",
            "General_Cell_Annotation_Open_Standard": "https://cellular-semantics.sanger.ac.uk/ontology/CAS/",
            "_base": "https://purl.brain-bican.org/ontology/AIT_MTG/",
            "MTG": "https://purl.brain-bican.org/ontology/AIT_MTG/",
            "CrossArea_cluster": "https://purl.brain-bican.org/ontology/AIT_MTG/CrossArea_cluster#",
            "CrossArea_subclass": "https://purl.brain-bican.org/ontology/AIT_MTG/CrossArea_subclass#",
            "Class": "https://purl.brain-bican.org/ontology/AIT_MTG/Class#",
            "obo": "http://purl.obolibrary.org/obo/",
            "CL": "http://purl.obolibrary.org/obo/CL_",
            "PCL": "http://purl.obolibrary.org/obo/PCL_",
            "RO": "http://purl.obolibrary.org/obo/RO_",
            "skos": "http://www.w3.org/2004/02/skos/core#"
        },
    )
    g.serialize(format="xml", destination=output_path)


def run_data2owl(schema_path, data_path, output_path):
    sv = SchemaView(schema_path)
    python_module = PythonGenerator(schema_path).compile_module()
    data = load_structured_file(data_path, schemaview=sv, python_module=python_module)
    dumper = OWLDumper()
    dumper.schemaview = sv

    # container = py_mod.Container(entities=check.records)
    # dumper.object_index = ObjectIndex(container, schemaview=sv)
    # dumper.autofill = True

    doc = dumper.to_ontology_document(data, schema=sv.schema)
    for a in doc.ontology.axioms:
        print(f'AXIOM={a}')
    with open(output_path, 'w') as stream:
        stream.write(str(doc))


def convert_cas_schema_to_linkml(output_path=None):
    ie = JsonSchemaImportEngine()
    schema = ie.load(CAS_SCHEMA_IN, name="cell-annotation-schema", format='json', root_class_name=None)
    model_path = os.path.join(MODEL_DIR, 'BICAN-schema.yaml')

    write_schema(schema, model_path)
    return schema


def expand_schema(config: str, schema: str, value_set_names: List[str], output: str):
    """
    Dynamic Value set expander.
    Source code from https://github.com/INCATools/ontology-access-kit/blob/main/src/oaklib/utilities/subsets/value_set_expander.py

    Parameters:
        config: str
            Configuration file path
        schema: str
            Schema file path
        value_set_names: List[str]
            Value set names to expand
        output: str
            Output expanded schema file path
    """
    expander = ValueSetExpander()
    if config:
        expander.configuration = yaml_loader.load(config, target_class=ValueSetConfiguration)
    expander.expand_in_place(
        schema_path=schema, value_set_names=value_set_names, output_path=output
    )


def convert_linkml_to_linkml_owl():
    pass


if __name__ == '__main__':
    # schema = convert_cas_schema_to_linkml()
    expand_schema(None, SCHEMA_IN3, ["CellTypeEnum"], SCHEMA_EXPANDED)
    # run_data2owl(SCHEMA_IN, DATA_IN, OWL_OUT)
    # if os.path.exists(OWL_OUT2):
    #     os.remove(OWL_OUT2)
    # run_rdf_dumper(SCHEMA_IN3, DATA_IN3, OWL_OUT2, validate=True)
    print("Done")
