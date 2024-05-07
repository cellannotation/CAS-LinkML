import json
import os
import logging
import tempfile
from typing import List, Optional, Union
from pathlib import Path

from ruamel.yaml import YAML

from linkml.generators.pythongen import PythonGenerator
from linkml_runtime import SchemaView
from linkml_runtime.utils.schemaview import load_schema_wrap

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

from linkml_runtime.utils.schema_as_dict import schema_as_dict
from linkml_runtime.loaders import yaml_loader
from linkml_runtime.dumpers import json_dumper
from oaklib.utilities.subsets.value_set_expander import ValueSetExpander, ValueSetConfiguration

SCHEMA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../schema')
MODEL_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../schema/schemauto')
INPUT_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../schema/schemauto/sample_data')

CAS_SCHEMA_IN = os.path.join(SCHEMA_DIR, 'BICAN_schema.json')

BASE_LINKML_SCHEMA = os.path.join(MODEL_DIR, 'BICAN-schema.yaml')
SCHEMA_IN = os.path.join(MODEL_DIR, 'BICAN-schema2.yaml')
SCHEMA_IN3 = os.path.join(MODEL_DIR, 'BICAN-schema3.yaml')
SCHEMA_EXPANDED = os.path.join(MODEL_DIR, 'BICAN-schema3-expanded.yaml')

DATA_IN = os.path.join(INPUT_DIR, 'AIT_MTG2.json')
DATA_IN3 = os.path.join(INPUT_DIR, 'AIT_MTG3.json')

OWL_OUT = os.path.join(MODEL_DIR, 'AIT_MTG.ofn')
OWL_OUT2 = os.path.join(MODEL_DIR, 'AIT_MTG_rdf.owl')

CAS_NAMESPACE = "https://cellular-semantics.sanger.ac.uk/ontology/CAS"

logger = logging.getLogger()
logger.setLevel(level=logging.DEBUG)


def run_rdf_dumper(schema: Union[str, Path, dict], data_path, output_path, validate=True):
    # gen, output, _ = _generate_framework_output(schema, PYTHON_DATACLASSES)
    schema_def: SchemaDefinition = yaml_loader.load(schema, target_class=SchemaDefinition)
    # if isinstance(schema, dict):
    #     schema_def: SchemaDefinition = yaml_loader.load(schema, target_class=SchemaDefinition)
    # else:
    #     schema_def: SchemaDefinition = yaml_loader.load(schema, SchemaDefinition)

    target_class = "GeneralCellAnnotationOpenStandard"

    with open(data_path) as f:
        instance = json.load(f)

    if validate:
        validator = Validator(schema_def)
        report = validator.validate(instance)
        print(report)
        print("DONE VALIDATING")

    # gen = generators.PythonGenerator(schema_path)
    # gen = generators.PythonGenerator(schema=schema_def)
    gen = generators.PythonGenerator(schema_def)
    output = gen.serialize()

    python_module = compile_python(output)
    py_target_class = getattr(python_module, target_class)

    try:
        py_inst = py_target_class(**instance)
    except Exception as e:
        print(f"Could not instantiate {py_target_class} from the data; exception: {e}")
        return None

    # schemaview = SchemaView(SchemaDefinition(**schema))
    schemaview = SchemaView(schema_def)

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


def run_data2owl(schema: Union[str, Path, dict], data_path, output_path):
    temp_file = None
    try:
        if isinstance(schema, dict):
            temp_file = tempfile.SpooledTemporaryFile(suffix='.yaml')
            schema_path = temp_file.name
            yaml = YAML()
            yaml.dump(schema, stream=temp_file)
            # loader = yaml_loader.YAMLLoader()
            # schema = loader.load(schema, target_class=SchemaDefinition)
            # schema = load_schema_wrap(schema, target_class=SchemaDefinition)
        else:
            schema_path = schema
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
    finally:
        if temp_file:
            temp_file.close()


def convert_cas_schema_to_linkml(cas_schema, output_path=None):
    """
    Converts the CAS schema to LinkML schema.
    Parameters:
        cas_schema: str
            Path to the CAS schema file
        output_path: str
            (Optional) Path to the output schema file
    Returns:
        LinkML SchemaDefinition object
    """
    ie = JsonSchemaImportEngine()
    schema = ie.load(cas_schema, name="cell-annotation-schema", format='json', root_class_name=None)
    if output_path:
        write_schema(schema, output_path)

    return schema


def expand_schema(config: Optional[str], yaml_obj: dict, value_set_names: List[str], output_path: Optional[str] = None):
    """
    Dynamic Value set expander. Expands the yaml_obj schema inplace with the given value set names.
    Source code from https://github.com/INCATools/ontology-access-kit/blob/main/src/oaklib/utilities/subsets/value_set_expander.py

    Parameters:
        config: str
            Configuration file path
        yaml_obj: dict
            Yaml schema object
        value_set_names: List[str]
            Value set names to expand
        output_path: str
            (Optional) Output expanded schema file path
    """
    expander = ValueSetExpander()
    if config:
        expander.configuration = yaml_loader.load(config, target_class=ValueSetConfiguration)
    # expander.expand_in_place(
    #     schema_path=schema, value_set_names=value_set_names, output_path=output
    # )
    yaml = YAML()
    schema = yaml_loader.load(yaml_obj, target_class=SchemaDefinition)
    if value_set_names is None:
        value_set_names = list(schema.enums.keys())
    for value_set_name in value_set_names:
        if value_set_name not in schema.enums:
            raise ValueError(f"Unknown value set: {value_set_name}")
        value_set = schema.enums[value_set_name]
        pvs = list(expander.expand_value_set(value_set, schema=schema))
        yaml_obj["enums"][value_set_name]["permissible_values"] = {
            str(pv.text): json_dumper.to_dict(pv) for pv in pvs
        }
    if output_path:
        with open(output_path, "w", encoding="UTF-8") as file:
            yaml.dump(yaml_obj, stream=file)
    return yaml_obj


def decorate_linkml_schema(schema_obj: Union[dict, SchemaDefinition], ontology_namespace, ontology_iri, labelsets=None, output_path=None):
    """
    Adds additional properties to the LinkML schema that are required for OWL conversion.
    Parameters:
        schema_obj: dict or SchemaDefinition
            Link ML schema object
        ontology_namespace: str
            Ontology namespace (e.g. MTG)
        ontology_iri: str
            Ontology IRI (e.g. https://purl.brain-bican.org/ontology/AIT_MTG/)
        labelsets: List[str]
            Labelsets used in the taxonomy.
        output_path: str
            (Optional) Path to the output schema file
    Returns:
        Decorated schema
    """
    if isinstance(schema_obj, SchemaDefinition):
        schema_obj = schema_as_dict(schema_obj)

    schema_obj["id"] = CAS_NAMESPACE

    ontology_namespace = ontology_namespace.upper()
    prefixes = {
        "linkml": "https://w3id.org/linkml/",
        "CAS": CAS_NAMESPACE + "/",
        "General_Cell_Annotation_Open_Standard": CAS_NAMESPACE + "/",
        "_base": ontology_iri,
        ontology_namespace: ontology_iri,
        "obo": "http://purl.obolibrary.org/obo/",
        "CL": "http://purl.obolibrary.org/obo/CL_",
        "PCL": "http://purl.obolibrary.org/obo/PCL_",
        "RO": "http://purl.obolibrary.org/obo/RO_",
        "skos": "http://www.w3.org/2004/02/skos/core#"
    }
    for labelset in labelsets:
        prefixes[labelset] = ontology_iri + f"{labelset}#"

    schema_obj["prefixes"] = prefixes
    schema_obj["default_range"] = "string"
    schema_obj["default_curi_maps"] = ["semweb_context", "obo_context"]
    schema_obj["enums"]["CellTypeEnum"] = {
        "reachable_from": {
            "source_ontology": "obo:cl",
            "source_nodes": ["CL:0000000"],
            "include_self": True,
            "relationship_types": ["rdfs:subClassOf"]
        }
    }
    schema_obj["slots"]["id"] = {
        "identifier": True,
        "range": "uriorcurie"
    }
    schema_obj["slots"]["name"]["slot_uri"] = "rdfs:label"
    schema_obj["slots"]["description"]["slot_uri"] = "IAO:0000115"
    schema_obj["slots"]["cell_label"]["slot_uri"] = "rdfs:label"
    schema_obj["slots"]["cell_fullname"]["slot_uri"] = "skos:preflabel"
    schema_obj["slots"]["cell_ontology_term_id"]["slot_uri"] = "RO:0002473"
    schema_obj["slots"]["cell_ontology_term_id"]["range"] = "CellTypeEnum"
    schema_obj["slots"]["cell_set_accession"]["identifier"] = True
    schema_obj["slots"]["parent_cell_set_accession"]["slot_uri"] = "RO:0015003"
    schema_obj["slots"]["parent_cell_set_accession"]["range"] = "Annotation"
    schema_obj["slots"]["source_taxonomy"]["range"] = "uriorcurie"
    schema_obj["slots"]["comment"]["slot_uri"] = "IAO:0000115"
    schema_obj["slots"]["labelset"]["slot_uri"] = "CAS:has_labelset"
    schema_obj["slots"]["labelsets"]["inlined"] = True
    schema_obj["slots"]["annotations"]["inlined"] = True

    schema_obj["classes"]["Labelset"]["slots"] = list(schema_obj["classes"]["Labelset"]["slots"]) + ["id"]
    schema_obj["classes"]["GeneralCellAnnotationOpenStandard"]["slots"] = list(schema_obj["classes"]["GeneralCellAnnotationOpenStandard"]["slots"]) + ["id"]
    schema_obj["classes"]["Annotation"]["class_uri"] = "PCL:0010001"

    if output_path:
        write_schema(schema_obj, output_path)

    return schema_obj


def convert_linkml_to_linkml_owl():
    pass


def read_yaml(file_path: str) -> dict:
    """
    Reads the schema file from the given path.
    :param file_path: path to the yaml file
    :return: yaml object
    """
    with open(file_path, "r") as fs:
        try:
            ryaml = YAML(typ="safe")
            return ryaml.load(fs)
        except Exception as e:
            raise Exception("Yaml read failed:" + file_path + " " + str(e))


if __name__ == '__main__':
    linkml_schema = convert_cas_schema_to_linkml(CAS_SCHEMA_IN)
    decorated_schema = decorate_linkml_schema(linkml_schema,
                                              ontology_namespace="MTG",
                                              ontology_iri="https://purl.brain-bican.org/ontology/AIT_MTG/",
                                              labelsets=["CrossArea_cluster", "CrossArea_subclass", "Class"])
    expanded_schema = expand_schema(config=None,
                                    yaml_obj=decorated_schema,
                                    value_set_names=["CellTypeEnum"])
    # run_data2owl(expanded_schema, DATA_IN, OWL_OUT)
    if os.path.exists(OWL_OUT2):
        os.remove(OWL_OUT2)
    run_rdf_dumper(expanded_schema, DATA_IN3, OWL_OUT2, validate=True)
    print("Done")
