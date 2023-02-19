from pydantic import BaseModel


def empresa_id_to_rut_empresa(empresa_id: str):
    """Converts empresa_id to rut_empresa format string"""

    rut_empresa = empresa_id[:-1] + "-" + empresa_id[-1]
    return rut_empresa


# These functions are used to convert the pydantic models into a dictionary
# and clean null terms
def document_to_dict(document):
    document = dict(document)
    for key, value in document.items():
        if isinstance(value, BaseModel):
            document[key] = document_to_dict(value)
    return document


def clean_null_terms(d):
    clean = {}
    for k, v in d.items():
        if isinstance(v, dict):
            nested = clean_null_terms(v)
            if len(nested.keys()) > 0:
                clean[k] = nested
        elif v is not None:
            clean[k] = v
    return clean
