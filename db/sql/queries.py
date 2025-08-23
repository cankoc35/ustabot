hybrit_search_query = """
    WITH queries AS (
        SELECT 
            %s merged_queries
    )
    ,extracted_terms AS (
                SELECT array_agg(DISTINCT term) AS terms
                FROM (
                    SELECT unnest(regexp_matches(merged_queries, E'\\w+', 'g')) AS term FROM queries
        ) AS sub
    )
    ,term_combinations AS (
        (SELECT 
            r, 
            string_agg(t.term, ' | ') AS term_combination
        FROM extracted_terms,
            generate_series(1, array_length(terms, 1)) AS r, 
            LATERAL (
                SELECT unnest(terms) AS term
                ORDER BY random() 
                LIMIT r
            ) AS t
        GROUP BY r)
        UNION ALL 
        (
        SELECT 
            r, 
            string_agg(t.term, ' & ') AS term_combination
        FROM extracted_terms,
            generate_series(1, array_length(terms, 1)) AS r, 
            LATERAL (
                SELECT unnest(terms) AS term
                ORDER BY random() 
                LIMIT r
            ) AS t
        GROUP BY r
        )
    )
    ,search_query AS (
        SELECT 
            string_agg('(' || term_combination || ')', ' | ') tsquery_str
        FROM term_combinations
    )
    ,bm25_cte AS (
        SELECT 
            d."documents" document, 
            ts_rank(tsv, to_tsquery('english', tsquery_str)) AS bm25_score
        FROM embeddings d, search_query
        WHERE tsquery_str IS NOT NULL AND tsv @@ to_tsquery('english', tsquery_str)  
    )
    ,embed_cte AS (
        SELECT 
            d."documents" document, 
            1 - (d.embeddings <=> (SELECT ai.ollama_embed('mxbai-embed-large', (SELECT %s)))) AS embedding_score
        FROM embeddings d
    )
    , merge_documents AS (
        SELECT 
            COALESCE(bm25_cte.document, embed_cte.document) AS document
        FROM embed_cte
        LEFT JOIN bm25_cte ON embed_cte.document = bm25_cte.document 
        ORDER BY (COALESCE(0.6 * bm25_cte.bm25_score, 0) + 0.4 * embed_cte.embedding_score) DESC
        LIMIT 5
    )	
        SELECT string_agg("document",' ') AS documents
        FROM merge_documents;
"""

insert_embeddings_query = """
    INSERT INTO embeddings ("documents","embeddings")
    VALUES (%s, ai.ollama_embed('mxbai-embed-large', %s))
"""

get_documents_query = """
        WITH cte AS (
        SELECT 
            s.id "shipmentId",
            origin_name.name "originName",
            destination_name.name "destinationName",
            REPLACE( (array_agg( DISTINCT routes.distance)::text),'NULL','') "distance",
            REPLACE( (array_agg( DISTINCT products.name)::text),'NULL','') "productName",
            REPLACE( (array_agg( DISTINCT "carriers"."carriers")::text),'NULL','') "carriers",
            REPLACE( (array_agg( DISTINCT "parentCarriers"."parentCarriers")::text),'NULL','') "parentCarriers"
        FROM shipments s
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
        WHERE s."createdAt" BETWEEN now()-interval'60days' AND now()
        GROUP BY 1,2,3
        ORDER BY 1 DESC 
    )
        SELECT 
            format(
                '
                    Shipment Number: %s,
                    Starting Place of shipment (origin of shipment): %s,
                    Ending Place of shipment (destination of shipment): %s,
                    Total distance in kilometers will be travelled: %s,
                    Product of shipment: %s,
                    Main carriers of shipment: %s,
                    Parent carriers of shipment: %s,
                    The time that this information was generated: %s
                ',
                "shipmentId",
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

def get_response_from_llm_query(user_question, documents):
    query = f"""
        WITH merged_documents AS (
            SELECT '
            
                "role": "shipment assistant",  
                "user question": "{user_question}",  
                "related documents": "{documents}", 
                "instructions": "
                
                    Please respond to the users question shortly based on the provided documents. 
                    Do not repeat the task, role and instructions.
                    Respond to the user question with the help of the related documents.
                    Only use the information from the related documents, never add extra information.
                    Never repeat the user question.
                    Answer the user question in a complete sentence.
                    If there are multiple documents, you can use all of them to answer the question.
                    You have to Use example sentence starter to start the response.
                    You have to Use example sentence ender to end the response.
                    
                ",
                "example sentence starter": "I am your UstaBot helper",
                "example sentence ender": "I hope this information helps you. If you need more information, let me know."
                
            '::TEXT AS "document"
        )
        , llama_response AS (
            SELECT ai.ollama_generate('llama3.2:3b',"document") response 
            FROM merged_documents
        )
        SELECT (response ->> 'response')::text AS response FROM llama_response;
    """
    return query