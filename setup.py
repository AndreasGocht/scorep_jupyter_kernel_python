from setuptools import setup
import sys
import pathlib
import json


kernel_spec = {
    "argv": [sys.executable, "-m", "scorep_jupyter.kernel", "{connection_file}"],
    "display_name":"scorep-python",
    "name":"scorep-python",
    "language":"python"
}

with open("kernel.json","w") as f:
    json.dump(kernel_spec,f,indent=4)

setup(
    name='scorep-jupyter',
    version='0.1.0',
    packages=["scorep_jupyter"], 
    data_files=[
        ("share/jupyter/kernels/scorep",["kernel.json"])
    ]
)