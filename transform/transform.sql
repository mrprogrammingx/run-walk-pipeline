-- transform.sql
-- Aggregate sensor samples into a compact daily/user summary table named `run_summary`.
-- Source schema (sampled from lake/parquet/runs.parquet):
--   date (VARCHAR like '2017-6-30'), time (VARCHAR), username, wrist, activity,
--   acceleration_x/y/z (DOUBLE), gyro_x/y/z (DOUBLE), ...
--
-- This SQL expects a relation named `runs` (for example a view over the parquet file).

DROP TABLE IF EXISTS daily_user_summary;
CREATE TABLE daily_user_summary AS
SELECT
  CAST(date AS DATE) AS date,
  username,
  -- most common activity code for the day/user
  MODE() WITHIN GROUP (ORDER BY activity) AS top_activity,
  -- most common wrist used for the day/user
  MODE() WITHIN GROUP (ORDER BY wrist) AS top_wrist,
  COUNT(*) AS samples,
  -- per-sample acceleration magnitude, then aggregated
  AVG(
    sqrt(
      acceleration_x * acceleration_x
      + acceleration_y * acceleration_y
      + acceleration_z * acceleration_z
    )
  ) AS avg_accel_magnitude,
  MAX(
    sqrt(
      acceleration_x * acceleration_x
      + acceleration_y * acceleration_y
      + acceleration_z * acceleration_z
    )
  ) AS max_accel_magnitude,
  AVG(gyro_x) AS avg_gyro_x,
  AVG(gyro_y) AS avg_gyro_y,
  AVG(gyro_z) AS avg_gyro_z
FROM runs
GROUP BY CAST(date AS DATE), username
ORDER BY date, username;

-- Activity counts per date/user
DROP TABLE IF EXISTS daily_activity_counts;
CREATE TABLE daily_activity_counts AS
SELECT
  CAST(date AS DATE) AS date,
  username,
  activity,
  COUNT(*) AS cnt
FROM runs
GROUP BY CAST(date AS DATE), username, activity
ORDER BY date, username, cnt DESC;


-- Wrist counts per date/user
DROP TABLE IF EXISTS daily_wrist_counts;
CREATE TABLE daily_wrist_counts AS
SELECT
  CAST(date AS DATE) AS date,
  username,
  wrist,
  COUNT(*) AS cnt
FROM runs
GROUP BY CAST(date AS DATE), username, wrist
ORDER BY date, username, cnt DESC;
