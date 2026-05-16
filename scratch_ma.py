from google.cloud import modelarmor_v1
import inspect

methods = [m for m in dir(modelarmor_v1) if not m.startswith('_')]
print("Methods:", methods)
