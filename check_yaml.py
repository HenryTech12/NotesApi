import yaml
import sys

try:
    with open('openapi.yaml', 'r') as f:
        yaml.safe_load(f)
    print("YAML is valid")
except yaml.YAMLError as exc:
    print(f"Error in YAML: {exc}")
    sys.exit(1)
