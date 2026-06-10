-- whapi_matviews.sql
-- DROP + CREATE materialized views with id (derived via row_number on outer query)
-- DAILY COUNTS
DROP MATERIALIZED VIEW IF EXISTS whapi_daily_counts CASCADE;
CREATE MATERIALIZED VIEW whapi_daily_counts AS
SELECT
  row_number() OVER (ORDER BY t.day)::bigint AS id,
  t.day AT TIME ZONE 'UTC' AS day,
  t.cnt::bigint AS message_count
FROM (
  SELECT
    date_trunc('day', received_at AT TIME ZONE 'UTC') AS day,
    COUNT(*) AS cnt
  FROM whapi_message
  GROUP BY date_trunc('day', received_at AT TIME ZONE 'UTC')
) t
ORDER BY t.day;

CREATE INDEX IF NOT EXISTS whapi_daily_counts_day_idx ON whapi_daily_counts (day);


-- CHANNEL COUNTS
DROP MATERIALIZED VIEW IF EXISTS whapi_channel_counts CASCADE;
CREATE MATERIALIZED VIEW whapi_channel_counts AS
SELECT
  row_number() OVER (ORDER BY t.day, t.channel_name)::bigint AS id,
  t.channel_name,
  t.day AT TIME ZONE 'UTC' AS day,
  t.cnt::bigint AS message_count
FROM (
  SELECT
    COALESCE(NULLIF(chat_name, ''), NULLIF(channel_id, ''), 'UNKNOWN') AS channel_name,
    date_trunc('day', received_at AT TIME ZONE 'UTC') AS day,
    COUNT(*) AS cnt
  FROM whapi_message
  GROUP BY COALESCE(NULLIF(chat_name, ''), NULLIF(channel_id, ''), 'UNKNOWN'),
           date_trunc('day', received_at AT TIME ZONE 'UTC')
) t
ORDER BY t.day DESC, t.cnt DESC;

CREATE INDEX IF NOT EXISTS whapi_channel_counts_channel_idx ON whapi_channel_counts (channel_name);
CREATE INDEX IF NOT EXISTS whapi_channel_counts_day_idx ON whapi_channel_counts (day);


-- CATEGORY COUNTS
DROP MATERIALIZED VIEW IF EXISTS whapi_category_counts CASCADE;
CREATE MATERIALIZED VIEW whapi_category_counts AS
SELECT
  row_number() OVER (ORDER BY t.cnt DESC)::bigint AS id,
  COALESCE(NULLIF(t.wa_category, ''), 'UNKNOWN') AS wa_category,
  t.cnt::bigint AS message_count
FROM (
  SELECT
    COALESCE(NULLIF(wa_category, ''), 'UNKNOWN') AS wa_category,
    COUNT(*) AS cnt
  FROM whapi_message
  GROUP BY COALESCE(NULLIF(wa_category, ''), 'UNKNOWN')
) t
ORDER BY t.cnt DESC;

CREATE INDEX IF NOT EXISTS whapi_category_counts_cat_idx ON whapi_category_counts (wa_category);


-- TAG COUNTS
DROP MATERIALIZED VIEW IF EXISTS whapi_tag_counts CASCADE;
CREATE MATERIALIZED VIEW whapi_tag_counts AS
SELECT
  row_number() OVER (ORDER BY t.cnt DESC)::bigint AS id,
  t.tag_id,
  t.tag_name,
  t.cnt::bigint AS message_count
FROM (
  SELECT
    t.id AS tag_id,
    t.name AS tag_name,
    COUNT(rel.message_id) AS cnt
  FROM whapi_tag t
  LEFT JOIN whapi_message_tag_rel rel ON rel.tag_id = t.id
  LEFT JOIN whapi_message m ON m.id = rel.message_id
  GROUP BY t.id, t.name
) t
ORDER BY t.cnt DESC;

CREATE INDEX IF NOT EXISTS whapi_tag_counts_tagname_idx ON whapi_tag_counts (tag_name);
