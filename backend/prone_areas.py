# prone_areas.py
# Purpose: Find top accident prone areas from dataset

import pandas as pd
import numpy as np
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_prone_areas():
    """Return top 20 accident prone areas with risk analysis"""
    try:
        df = pd.read_csv(os.path.join(BASE_DIR, "accident_data.csv"))

        # Severity score mapping
        severity_score = {'fatal': 3, 'major': 2, 'minor': 1}
        df['sev_score'] = df['accident_severity'].map(severity_score).fillna(1)

        # Round coordinates to cluster nearby accidents
        df['lat_r'] = df['latitude'].round(2)
        df['lng_r'] = df['longitude'].round(2)

        # Group by location
        grouped = df.groupby(['lat_r', 'lng_r', 'city']).agg(
            total_accidents = ('accident_id',  'count'),
            avg_risk_score  = ('risk_score',   'mean'),
            fatal_count     = ('sev_score',    lambda x: (x == 3).sum()),
            major_count     = ('sev_score',    lambda x: (x == 2).sum()),
            common_weather  = ('weather',      lambda x: x.mode()[0] if len(x) > 0 else 'clear'),
            common_road     = ('road_type',    lambda x: x.mode()[0] if len(x) > 0 else 'urban'),
            common_hour     = ('hour',         'median')
        ).reset_index()

        # Danger score = accidents × avg_risk + fatal bonus
        grouped['danger_score'] = (
            grouped['total_accidents'] * grouped['avg_risk_score'] +
            grouped['fatal_count'] * 2
        ).round(2)

        # Sort by danger score
        top = grouped.nlargest(20, 'danger_score').reset_index(drop=True)
        top['rank'] = top.index + 1

        result = []
        for _, row in top.iterrows():
            danger = row['danger_score']
            if danger >= top['danger_score'].quantile(0.75):
                level = 'EXTREME'
                color = '#e74c3c'
            elif danger >= top['danger_score'].quantile(0.5):
                level = 'HIGH'
                color = '#f39c12'
            else:
                level = 'MODERATE'
                color = '#f1c40f'

            result.append({
                "rank"            : int(row['rank']),
                "city"            : str(row['city']),
                "lat"             : round(float(row['lat_r']), 4),
                "lng"             : round(float(row['lng_r']), 4),
                "total_accidents" : int(row['total_accidents']),
                "fatal_count"     : int(row['fatal_count']),
                "major_count"     : int(row['major_count']),
                "avg_risk_score"  : round(float(row['avg_risk_score']), 2),
                "danger_score"    : round(float(row['danger_score']), 2),
                "danger_level"    : level,
                "danger_color"    : color,
                "common_weather"  : str(row['common_weather']),
                "common_road"     : str(row['common_road']),
                "peak_hour"       : int(row['common_hour'])
            })

        return result

    except Exception as e:
        print(f"Prone areas error: {e}")
        return []
