from django.test import TestCase
from rest_framework.test import APIClient
import joblib
# Create your tests here.
from ml.classifier.binary_model import BinaryClassifier
from ml.classifier.random_forest import RandomForestClassifier
class MLTests(TestCase):
    def test_rf_algorithm(self):
        input_data = joblib.load("D:\\Binh\\my_project\\backend\\backend\\model\\result_dict4.joblib")
        my_alg = BinaryClassifier()
        response = my_alg.compute_prediction(input_data)
        self.assertEqual('OK', response['status'])
        self.assertTrue('label' in response)
        self.assertEqual('Co nguy co bi hong', response['label'])
    def test_et_algorithm(self):
        input_data = joblib.load("D:\\Binh\\my_project\\backend\\backend\\model\\result_dict4.joblib")
        my_alg = RandomForestClassifier()
        response = my_alg.compute_prediction(input_data)
        self.assertEqual('OK', response['status'])
        self.assertTrue('label' in response)
        self.assertEqual('Co nguy co bi hong', response['label'])
class APITests(TestCase):
    def test_predict_view(self):
        client = APIClient()
        input_data = joblib.load("D:\\Binh\\my_project\\backend\\backend\\model\\result_dict3.joblib")
        classifier_url = "api/v1/classifier/predict"
        response = client.post(classifier_url, input_data, format='json')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.data['label'], "Co nguy co bi hong")
        self.assertTrue("request_id" in response.data)
        self.assertTrue("status" in response.data)

