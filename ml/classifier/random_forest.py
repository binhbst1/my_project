import joblib
import pandas as pd
import numpy as np
import keras
class RandomForestClassifier:
    def __init__(self):
        self.model = joblib.load("D:\\Binh\\my_project\\backend\\backend\\model\\random_forest.joblib")
        self.std = joblib.load("D:\\Binh\\my_project\\backend\\backend\\model\\min_max_scaler.joblib")
    def preprocessing(self, input_data):
        # JSON to pandas DataFrame
        input_data = pd.DataFrame(input_data)[-1:]
        input_data.drop(['setting3','s1','s5','s10','s16','s18','s19'],axis=1, inplace=True)
        input_data['cycle_norm'] = input_data['cycle']
        cols_normalize = input_data.columns.difference(['id','cycle'])
        norm_input_data = pd.DataFrame(self.std.transform(input_data[cols_normalize]), columns=cols_normalize, index=input_data.index)
        join_df = input_data[input_data.columns.difference(cols_normalize)].join(norm_input_data)
        input_data = join_df.reindex(columns = input_data.columns)
        input_data.drop(['cycle','id','s6','s14','setting1','setting2'],axis=1, inplace=True)
        return input_data
    def predict(self, input_data):
        return self.model.predict_proba(input_data)
    def postprocessing(self, input_data):
        label = "Khong co nguy co bi hong"
        if input_data[1] > 0.5:
           label = "Co nguy co bi hong"
        return {'label': label, 'status': "OK"}
    def compute_prediction(self, input_data):
        # Bước 1: Chuyển input_data thành DataFrame
        input_data_df = self.preprocessing(input_data)
        # Bước 2: Thực hiện dự đoán 
        prediction = self.predict(input_data_df)[0]
        print('prediction:')
        print(prediction[1]) 
        prediction = self.postprocessing(prediction)
        return prediction
