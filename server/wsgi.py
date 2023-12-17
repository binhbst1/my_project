"""
WSGI config for server project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')

application = get_wsgi_application()

# ML registry
from ml.registry import MLRegistry
from ml.classifier.binary_model import BinaryClassifier
from ml.classifier.random_forest import RandomForestClassifier

try:
    # create ML registry
    registry = MLRegistry()
    # BinaryClassifier
    bin = BinaryClassifier()
    rf = RandomForestClassifier()
    # add to ML registry
    registry.add_algorithm(endpoint_name="classifier",
                        algorithm_object=rf,
                        algorithm_name="random forest",
                        algorithm_status="production",
                        algorithm_version="0.0.1",
                        owner="Nhom7",
                        algorithm_description="Random Forest with simple pre- and post-processing")
    registry.add_algorithm(endpoint_name="classifier",
                            algorithm_object=bin,
                            algorithm_name="LSTM",
                            algorithm_status="production",
                            algorithm_version="0.0.1",
                            owner="Nhom7",
                            algorithm_description="LSTM with simple pre- and post-processing")
except Exception as e:
    print("Exception while loading the algorithms to the registry,", str(e))


