hybrit_search_query = """

"""

insert_embeddings_query = """
    INSERT INTO embeddings ("documents","embeddings")
    VALUES (%s, ai.ollama_embed('mxbai-embed-large', %s))
    ON CONFLICT ("documents")
    DO UPDATE SET "embeddings" = EXCLUDED."embeddings";
"""

get_documents_query = """
    WITH cte AS (
        SELECT 
            s.id "shipmentId",
            t.status,
            origin_name.name "originName",
            destination_name.name "destinationName",
            REPLACE( (array_agg( DISTINCT routes.distance)::text),'NULL','') "distance",
            REPLACE( (array_agg( DISTINCT products.name)::text),'NULL','') "productName",
            REPLACE( (array_agg( DISTINCT "carriers"."carriers")::text),'NULL','') "carriers",
            REPLACE( (array_agg( DISTINCT "parentCarriers"."parentCarriers")::text),'NULL','') "parentCarriers"
        FROM shipments s
        INNER JOIN transportations t ON t.id = s.id 
            AND t."deletedAt" IS NULL 
            AND s."deletedAt" IS NULL 
        LEFT JOIN LATERAL (
            SELECT 
                c."plateNumber" carriers
            FROM shipment_carriers sc 
            JOIN carriers c ON c.id = sc."carrierId" 
            WHERE sc."shipmentId" = s.id 
            AND sc."deletedAt" IS NULL 
        ) carriers ON TRUE 
        LEFT JOIN LATERAL (
            SELECT 
                c."plateNumber" "parentCarriers"
            FROM shipment_designs sd 
            JOIN carriers c ON c.id = sd."parentCarrierId" 
            WHERE sd."shipmentId" = s.id 
            AND sd."deletedAt" IS NULL 
        ) "parentCarriers" ON TRUE 
        LEFT JOIN LATERAL (
            SELECT p.name
            FROM places p
            WHERE st_intersects(p.geom::geometry,s.origin::geometry)
            AND p."countryCodes" IS NOT NULL 
            ORDER BY p."countryCodes" DESC  
            LIMIT 1
        ) origin_name ON TRUE 
        LEFT JOIN LATERAL (
            SELECT p.name
            FROM places p
            WHERE st_intersects(p.geom::geometry,s.destination::geometry)
            AND p."countryCodes" IS NOT NULL 
            ORDER BY p."countryCodes" DESC 
            LIMIT 1
        ) destination_name ON TRUE 
        LEFT JOIN LATERAL (
            SELECT p.name
            FROM shipment_products sp 
            INNER JOIN products p ON p.id = sp."productId" 
                AND sp."deletedAt" IS NULL 
                AND p."deletedAt" IS NULL 
            WHERE sp."shipmentId" = s.id 
        ) products ON TRUE 
        LEFT JOIN LATERAL (
            SELECT 
                sum( DISTINCT distance)/1000 distance
            FROM shipment_routes sr
            WHERE sr."shipmentId" = s.id 
            AND sr."deletedAt" IS NULL 
        ) routes ON TRUE 
        WHERE s."createdAt" BETWEEN %s AND %s
        GROUP BY 1,2,3,4
        ORDER BY 1 DESC 
    )
        SELECT 
            format(
                '
                    Shipment Number: %s,
                    Status of shipment: %s,
                    Starting Place of shipment (origin of shipment): %s,
                    Ending Place of shipment (destination of shipment): %s,
                    Total distance in kilometers will be travelled: %s,
                    Product of shipment: %s,
                    Main carriers of shipment: %s,
                    Parent carriers of shipment: %s,
                    The time that this information was generated: %s
                ',
                "shipmentId",
                "status",
                "originName",
                "destinationName",
                "distance",
                "productName",
                "carriers",
                "parentCarriers",
                LEFT(now()::text,16)
            ) "document"
        FROM cte 
"""