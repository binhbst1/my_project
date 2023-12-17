import pandas as pd
import requests
import joblib
file_path ="D:\\Binh\\my_project\\backend\\backend\\model\\PM_test.txt"
test = pd.read_csv(file_path,delimiter=' ', header = None)
col_names = ['id','cycle','setting1','setting2','setting3','s1','s2','s3','s4','s5','s6','s7','s8','s9','s10','s11','s12','s13','s14','s15','s16','s17','s18','s19','s20','s21']
test.drop([26,27],axis=1,inplace=True)
test.columns = col_names
test = test[test['id']==34].reset_index()
for i in range (150):
      subset_data = test.iloc[i:i+50]
      input_data = subset_data.to_dict(orient='list')
      if (i<130):
      	target = 0
      else:
        target = 1    
      r = requests.post("http://127.0.0.1:8000/api/v1/classifier/predict?status=ab_testing", input_data,format='json')
      response = r.json()
      requests.put("http://127.0.0.1:8000/api/v1/mlrequests/{}".format(response["request_id"]), {"feedback": target})
