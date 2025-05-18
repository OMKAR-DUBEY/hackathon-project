import pandas as pd
import sqlite3
from datetime import datetime

conn=sqlite3.connect(r"D:\user_info\user_info.db")
cursor=conn.cursor()


user_data=pd.read_sql_query("SELECT * FROM user",conn)
events_data=pd.read_sql_query("SELECT * FROM Events",conn)
interactions_data=pd.read_sql_query("SELECT * FROM interactions",conn)

weights={
    'view':1,
    'search':2,
    'add_event':4,
}

interactions_data['timestamp'] = interactions_data['timestamp'].str.replace('c', ' ')
interactions_data['timestamp'] = pd.to_datetime(interactions_data['timestamp'])

interactions_data['interactions_score']=interactions_data['interaction_type'].map(weights)

interactions_data['days_ago']=(datetime.now()-interactions_data['timestamp']).dt.days
interactions_data['recency_weights']=1/(1+interactions_data['days_ago'])

interactions_data['final_score']=interactions_data['interactions_score']*interactions_data['recency_weights']

merged_events=interactions_data.merge(events_data[['events_id','categories']],on='events_id',how='left')
user_category_score=merged_events.groupby(['user_id', 'categories'])['final_score'].sum().reset_index()


recommendations = []
top_categories = user_category_score.sort_values(['user_id', 'final_score'], ascending=[True, False])

for _, row in top_categories.iterrows():
    user_id = row['user_id']
    category = row['categories']
    
    seen_events_id = interactions_data[interactions_data['user_id'] == user_id]['events_id'].unique()
    
    recommended_events = events_data[
        (events_data['categories'] == category) &
        (~events_data['events_id'].isin(seen_events_id))
    ]

    for _, event in recommended_events.iterrows():
        recommendations.append({
            'user_id': user_id,
            'recommended_event_id': event['events_id'],
            'events_list': event['events_list'],
            'categories': category
        })

recommendations_data = pd.DataFrame(recommendations)
print(recommendations_data)
print("Script ran successfully!")
