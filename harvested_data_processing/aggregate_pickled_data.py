import pandas as pd 
import sys
import numpy as np
import boto3
import json
import itertools
from time import gmtime, strftime

def geojson2s3(geojson_dict, out_bucket, out_key):
    s3client = boto3.client('s3')
    s3client.put_object(
        Body=json.dumps(geojson_dict, indent=2), 
        Bucket=out_bucket, 
        Key=out_key, 
        ContentType='application/json',
        ACL='private')#'public-read'

### Read data
QUERY_RESULTS_DF_NAME = 'query_results_df_datetime.pkl' # CHANGE
IMPUTE_DF_NAME = 'impute_df_datetime.pkl' # CHANGE

input_df = pd.read_pickle(QUERY_RESULTS_DF_NAME)
print('shape of the query_reults dataframe: ', input_df.shape)
#print(input_df.dtypes)

### Convert to weekdays and weekends
input_df['query_weekend'] = np.where(input_df['query_weekday'].isin([0,6]), 1, 0)
# print(input_df.dtypes)
avg_speed_df = input_df.groupby(['link_id', 'link_type', 'start_node', 'end_node', 'query_hour', 'query_weekend']).agg({'sec_speed': 'mean', 'coordinates': 'first'}).reset_index()
print('avg_speed_df.shape: ', avg_speed_df.shape)

### Three-step imputing for missing traffic data
impute_df = pd.read_pickle(IMPUTE_DF_NAME)
print('shape of impute_df', impute_df.shape)
imputed_df = pd.merge(impute_df, avg_speed_df.drop('coordinates', axis=1), 
    how='left', 
    on=['link_id', 'link_type', 'start_node', 'end_node', 'query_hour', 'query_weekend'],
    validate='1:1')
print('shape of imputed_df', imputed_df.shape)
print('number of NaN in sec_speed before imputation', imputed_df['sec_speed'].isnull().sum())
### 1st
imputed_df['sec_speed1'] = imputed_df['sec_speed'].fillna(imputed_df.groupby(
    ['query_weekend', 'query_hour', 'approx_coordinates', 'link_type'])['sec_speed'].transform('mean'))
print('number of NaN in sec_speed after weekend-hour-location-type imputation', imputed_df['sec_speed1'].isnull().sum())
### 2nd
imputed_df['sec_speed2'] = imputed_df['sec_speed1'].fillna(imputed_df.groupby(
    ['query_weekend', 'query_hour', 'link_type'])['sec_speed'].transform('mean'))
print('number of NaN in sec_speed after weekend-hour-type imputation', imputed_df['sec_speed2'].isnull().sum())
### 3rd
imputed_df['sec_speed3'] = imputed_df['sec_speed2'].fillna(imputed_df.groupby(
    ['link_type'])['sec_speed'].transform('mean'))
print('number of NaN in sec_speed after type imputation', imputed_df['sec_speed3'].isnull().sum())

### Convert data to geojson and push to S3 to visualize
query_weekend_list = [True, False]
query_hour_list = [hr for hr in range(8,18)]
visualize_df = imputed_df # avg_speed_df or imputed_df
S3_BUCKET = 'CHANGE'
S3_FOLDER = 'CHANGE' # 'Collected_data/' or 'Imputed_data/'
speed_column = 'sec_speed3'    # 'sec_speed' or 'sec_speed3'

for day, hour in itertools.product(query_weekend_list, query_hour_list):
    filtered_df = visualize_df.loc[(visualize_df['query_weekend'] == day) & (visualize_df['query_hour'] == hour)]
    print('at weekend {}, hour {}, there are {} filtered results'.format(day, hour, filtered_df.shape[0]))

    if filtered_df.shape[0] == 0:
        feature_list = []
    else:
        feature_list = []
        for index, row in filtered_df.iterrows():
            feature = {'type': 'Feature', 
                    'geometry': {'type': 'LineString', 'coordinates': row['coordinates']},
                    'properties': {'link_id': row['link_id'], 
                                'start_node': row['start_node'], 
                                'end_node': row['end_node'], 
                                'query_weekend': row['query_weekend'], 
                                'query_hour': row['query_hour'], 
                                'sec_speed': row[speed_column]}}
            feature_list.append(feature)
    geojson_dict = {'type': 'FeatureCollection', 'features': feature_list}

    KEY = S3_FOLDER+str(day)+str(hour)
    geojson2s3(geojson_dict, S3_BUCKET, KEY)

print('end of aggregate_pickled_data.py')


#print(test_df.loc[(test_df['link_id']=='8916547r') & (test_df['start_node']=='1714191994')])
#print(list(test_df.loc[(test_df['link_id']=='8916547r') & (test_df['start_node']=='1714191994'), 'coordinates']))