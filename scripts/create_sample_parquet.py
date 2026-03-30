import os
import pandas as pd


def main():
    out_dir = os.path.join('lake', 'parquet')
    os.makedirs(out_dir, exist_ok=True)
    df = pd.DataFrame({
        'date': ['2017-07-01', '2017-07-01', '2017-07-02', '2017-07-03'],
        'time': ['12:00:00','12:05:00','12:10:00','12:15:00'],
        'username': ['viktor', 'viktor', 'viktor', 'viktor'],
        'acceleration_x': [0.1, 0.2, 0.15, 0.12],
        'acceleration_y': [0.0, 0.1, -0.05, 0.02],
        'acceleration_z': [0.0, 0.0, 0.0, 0.01],
        'gyro_x': [0.01, 0.02, -0.01, 0.0],
        'gyro_y': [0.0, 0.005, -0.002, 0.001],
        'gyro_z': [0.0, 0.0, 0.0, 0.0],
        'activity': [0, 1, 0, 1],
        'wrist': [0, 1, 0, 1],
    })
    df['date'] = pd.to_datetime(df['date'])
    path = os.path.join(out_dir, 'runs.parquet')
    df.to_parquet(path, index=False)
    print('Wrote sample parquet to', path)


if __name__ == '__main__':
    main()
