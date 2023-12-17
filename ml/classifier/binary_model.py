import joblib
import pandas as pd
import numpy as np
import keras
class BinaryClassifier:
    def __init__(self):
        self.model = keras.models.load_model("D:\\Binh\\my_project\\backend\\backend\\model\\model_lstm_bin.h5")
        self.std = joblib.load("D:\\Binh\\my_project\\backend\\backend\\model\\min_max_scaler.joblib")
    def preprocessing(self, input_data):
        # JSON to pandas DataFrame
        input_data = pd.DataFrame(input_data)
        input_data.drop(['setting3','s1','s5','s10','s16','s18','s19'],axis=1, inplace=True)
        input_data['cycle_norm'] = input_data['cycle']
        cols_normalize = input_data.columns.difference(['id','cycle'])
        norm_input_data = pd.DataFrame(self.std.transform(input_data[cols_normalize]), columns=cols_normalize, index=input_data.index)
        join_df = input_data[input_data.columns.difference(cols_normalize)].join(norm_input_data)
        input_data = join_df.reindex(columns = input_data.columns)
        cols_normalize = input_data.columns.difference(['id','cycle','setting1','setting2','s6','s14'])
        input_data = input_data[cols_normalize]
        return input_data
    def pad_data(self, input_data):
        # Lấy số lượng dòng cần padding
        num_padding_rows = 50 - len(input_data)
        # Tạo DataFrame chứa dữ liệu padding với giá trị 0
        padding_data = pd.DataFrame(np.zeros((num_padding_rows, input_data.shape[1])), columns=input_data.columns)
        # Kết hợp DataFrame input_data và padding_data
        padded_data = pd.concat([padding_data, input_data], ignore_index=True)
        return padded_data
    def predict(self, input_data):
        return self.model.predict(input_data)
    def postprocessing(self, input_data):
        label = "Khong co nguy co bi hong"
        if input_data[0] > 0.015:
           label = "Co nguy co bi hong"
        return {'label': label, 'status': "OK"}
    def compute_prediction(self, input_data):
        # Bước 1: Chuyển input_data thành DataFrame
        input_data_df = self.preprocessing(input_data)
        # Bước 2: Kiểm tra nếu có đủ 50 mẫu dữ liệu, nếu không thì thêm dữ liệu padding
        if len(input_data_df) < 50:
            input_data_df = self.pad_data(input_data_df)
        # Bước 3: Nếu có nhiều hơn 50 dòng, chỉ lấy 50 dòng cuối cùng
        elif len(input_data_df) > 50:
            input_data_df = input_data_df[-50:]
        # Bước 4: Thực hiện dự đoán chỉ khi có đúng 50 mẫu dữ liệu
        prediction = self.predict(np.array([input_data_df.values]))[0]
        print(prediction[0]) 
        prediction = self.postprocessing(prediction)
        return prediction
