-- Inventory tổng hợp source licenses; source_items/feature_ids giữa các nhóm có thể chồng lấp.
SELECT
    src.provider,
    src.dataset,
    src.license,
    src.property,
    COUNT(*) AS source_item_count,
    COUNT(DISTINCT places.id) AS feature_count
FROM read_parquet(
    'data/raw/overture/release=2026-10-21.0/region=us-census-state-equivalents/run=20261115T114934.225255Z/theme=places/type=place/place.geoparquet'
) AS places
CROSS JOIN UNNEST(places.sources) AS source_rows(src)
GROUP BY src.provider, src.dataset, src.license, src.property
ORDER BY feature_count DESC, source_item_count DESC, src.provider, src.dataset, src.property;
