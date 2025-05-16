import re
import pandas as pd

https://github.com/PacktPublishing/Apache-Airflow-Best-Practices/tree/main/chapter-06

def camel_to_snake(name: str) -> str:
    # 1) Split before a capital followed by lowercase
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    # 2) Split between lowercase/digit and capital
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1)
    return s2.lower()


test_strings = [
    "camelCase",
    "CamelCase",
    "simpleTest",
    "HTTPResponseCode",
    "getURL",
    "get2HTTPResponses",
    "already_snake_case",
    "",
    "XMLHttpRequest",
    "JSONData",
    "ThisIsATest",
    "userIDNumber",
    "var123Name",
    "nameWithHTTPDataURL",
]
expected = [
    "output",
    "camel_case",
    "camel_case",
    "simple_test",
    "http_response_code",
    "get_url",
    "get2_http_responses",
    "already_snake_case",
    "xml_http_request",
    "json_data",
    "this_is_a_test",
    "user_id_number",
    "var123_name",
    "name_with_http_data_url",
]
