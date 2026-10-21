-- Add session-level conversion metrics and GA4 property timezone without rewriting historical rows.
ALTER TABLE visitor_daily_totals ADD COLUMN conversion_sessions INTEGER;
ALTER TABLE visitor_daily_sources ADD COLUMN conversion_sessions INTEGER;
ALTER TABLE visitor_daily_landing_pages ADD COLUMN conversion_sessions INTEGER;
ALTER TABLE visitor_range_snapshots ADD COLUMN conversion_sessions INTEGER;
ALTER TABLE visitor_range_ai_metrics ADD COLUMN conversion_sessions INTEGER;
ALTER TABLE visitor_range_sources ADD COLUMN conversion_sessions INTEGER;
ALTER TABLE visitor_range_landing_pages ADD COLUMN conversion_sessions INTEGER;
ALTER TABLE visitor_sync_runs ADD COLUMN property_timezone TEXT;
