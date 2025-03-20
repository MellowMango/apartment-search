import os
import json
import uuid
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional, Union

# Supabase client
from supabase import create_client, Client

# Neo4j driver
from neo4j import GraphDatabase, AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable

# Import configuration
from backend.data_enrichment.config import DB_CONFIG

logger = logging.getLogger(__name__)

class EnrichmentDatabaseOps:
    """
    Database operations for storing and retrieving deep property research data.
    
    This class provides methods to:
    1. Store research results in Supabase
    2. Create graph relationships in Neo4j
    3. Query both databases for research data
    4. Handle batch operations efficiently
    """
    
    def __init__(self):
        """Initialize database connections and configurations."""
        # Initialize Supabase client
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        
        # Initialize Neo4j driver
        self.neo4j_uri = os.environ.get("NEO4J_URI")
        self.neo4j_username = os.environ.get("NEO4J_USERNAME")
        self.neo4j_password = os.environ.get("NEO4J_PASSWORD")
        self.neo4j_database = os.environ.get("NEO4J_DATABASE", "neo4j")
        
        # Get configuration settings
        self.supabase_research_table = DB_CONFIG["supabase"]["research_table"]
        self.supabase_property_table = DB_CONFIG["supabase"]["property_table"]
        self.supabase_batch_size = DB_CONFIG["supabase"]["batch_size"]
        
        # Initialize connections only if credentials are available
        self.supabase = None
        self.neo4j_driver = None
        
        # Try to connect to Supabase
        if self.supabase_url and self.supabase_key:
            try:
                self.supabase = create_client(self.supabase_url, self.supabase_key)
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {str(e)}")
        else:
            logger.warning("Supabase credentials not found in environment variables")
        
        # Try to connect to Neo4j
        if self.neo4j_uri and self.neo4j_username and self.neo4j_password:
            try:
                self.neo4j_driver = GraphDatabase.driver(
                    self.neo4j_uri,
                    auth=(self.neo4j_username, self.neo4j_password)
                )
                # Test connection
                with self.neo4j_driver.session(database=self.neo4j_database) as session:
                    result = session.run("RETURN 1 as test")
                    result.single()
                logger.info("Neo4j driver initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Neo4j driver: {str(e)}")
                self.neo4j_driver = None
        else:
            logger.warning("Neo4j credentials not found in environment variables")
    
    async def save_research_results(self, property_id: str, research_results: Dict[str, Any]) -> bool:
        """
        Save property research results to databases and update the properties table with enriched data.
        
        Args:
            property_id: The unique identifier for the property
            research_results: The deep research results to save
            
        Returns:
            True if successful, False otherwise
        """
        success = True
        
        # Save to Supabase
        if self.supabase:
            try:
                # Prepare data for Supabase
                supabase_data = self._prepare_research_for_supabase(property_id, research_results)
                
                # Just use upsert to handle both insert and update cases
                logger.info(f"Upserting research results for property {property_id}")
                try:
                    # Add id field if missing to avoid duplicate ID errors
                    if "id" not in supabase_data:
                        supabase_data["id"] = str(uuid.uuid4())
                    
                    result = self.supabase.table(self.supabase_research_table) \
                        .upsert(supabase_data) \
                        .execute()
                    logger.info(f"Successfully upserted research results for property {property_id} in Supabase")
                    
                    # Update the properties table with enriched data
                    await self._update_property_with_enriched_data(property_id, research_results)
                except Exception as upsert_error:
                    logger.error(f"Upsert error: {str(upsert_error)}")
                    # Try insert as fallback
                    try:
                        result = self.supabase.table(self.supabase_research_table) \
                            .insert(supabase_data) \
                            .execute()
                        logger.info(f"Inserted research results for property {property_id} as fallback")
                        
                        # Still try to update properties with enriched data
                        await self._update_property_with_enriched_data(property_id, research_results)
                    except Exception as insert_error:
                        logger.error(f"Insert error: {str(insert_error)}")
                        raise
            except Exception as e:
                logger.error(f"Failed to save research results to Supabase: {str(e)}")
                success = False
        
        # Save to Neo4j
        if self.neo4j_driver:
            try:
                # Save research node and relationships in Neo4j
                self._save_research_to_neo4j(property_id, research_results)
                logger.info(f"Saved research results for property {property_id} in Neo4j")
            except Exception as e:
                logger.error(f"Failed to save research results to Neo4j: {str(e)}")
                success = False
        
        return success
    
    async def batch_save_research_results(self, property_results: List[Tuple[str, Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Save multiple property research results in batch.
        
        Args:
            property_results: List of (property_id, research_results) pairs
            
        Returns:
            Dictionary with success count and failed property IDs
        """
        success_count = 0
        failed_ids = []
        
        # For Supabase, we can batch insert/update
        if self.supabase and property_results:
            # Split into batches to avoid request size limits
            batch_size = self.supabase_batch_size
            for i in range(0, len(property_results), batch_size):
                batch = property_results[i:i+batch_size]
                
                try:
                    # Prepare batch data for Supabase
                    supabase_batch = [
                        self._prepare_research_for_supabase(prop_id, results)
                        for prop_id, results in batch
                    ]
                    
                    # Upsert data (insert or update)
                    result = self.supabase.table(self.supabase_research_table) \
                        .upsert(supabase_batch) \
                        .execute()
                    
                    # Count successful operations
                    success_count += len(result.data)
                    logger.info(f"Batch saved {len(result.data)} research results to Supabase")
                except Exception as e:
                    logger.error(f"Failed to batch save to Supabase: {str(e)}")
                    # Mark all properties in this batch as failed
                    failed_ids.extend([prop_id for prop_id, _ in batch])
        
        # For Neo4j, we need to process one by one due to complex relationships
        if self.neo4j_driver and property_results:
            for prop_id, results in property_results:
                try:
                    # Save to Neo4j
                    self._save_research_to_neo4j(prop_id, results)
                    if prop_id not in failed_ids:  # Only count if not already failed in Supabase
                        success_count += 1
                except Exception as e:
                    logger.error(f"Failed to save research for property {prop_id} to Neo4j: {str(e)}")
                    if prop_id not in failed_ids:
                        failed_ids.append(prop_id)
                        
        return {
            "success_count": success_count,
            "failed_property_ids": failed_ids
        }
    
    async def get_research_results(self, property_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve research results for a property.
        
        Args:
            property_id: The unique identifier for the property
            
        Returns:
            Research results dictionary or None if not found
        """
        # Try Supabase first as it's faster for simple retrieval
        if self.supabase:
            try:
                result = self.supabase.table(self.supabase_research_table) \
                    .select("*") \
                    .eq("property_id", property_id) \
                    .execute()
                
                if result.data:
                    # Convert from Supabase format back to original structure
                    return self._convert_from_supabase_format(result.data[0])
            except Exception as e:
                logger.error(f"Failed to get research results from Supabase: {str(e)}")
        
        # Fallback to Neo4j if available
        if self.neo4j_driver:
            try:
                with self.neo4j_driver.session(database=self.neo4j_database) as session:
                    result = session.run(
                        """
                        MATCH (r:PropertyResearch {property_id: $property_id})
                        RETURN r
                        """,
                        property_id=property_id
                    )
                    
                    record = result.single()
                    if record:
                        return self._convert_from_neo4j_format(record["r"])
            except Exception as e:
                logger.error(f"Failed to get research results from Neo4j: {str(e)}")
        
        return None
    
    async def get_properties_needing_research(self, limit: int = 10, 
                                             research_depth: str = "standard",
                                             days_threshold: int = 30) -> List[Dict[str, Any]]:
        """
        Find properties that need research or research refresh.
        
        Args:
            limit: Maximum number of properties to return
            research_depth: Depth of research to check for
            days_threshold: Number of days after which research is considered outdated
            
        Returns:
            List of property data dictionaries
        """
        if not self.supabase:
            logger.error("Cannot get properties needing research: Supabase client not initialized")
            return []
        
        try:
            # Get current timestamp
            current_time = datetime.now().isoformat()
            
            # Calculate threshold timestamp
            from datetime import timedelta
            threshold_time = (datetime.now() - timedelta(days=days_threshold)).isoformat()
            
            # Just get all properties until we have the research table setup
            result = self.supabase.table(self.supabase_property_table) \
                .select("*") \
                .order("updated_at", desc=True) \
                .limit(limit) \
                .execute()
            
            return result.data
        except Exception as e:
            logger.error(f"Failed to get properties needing research: {str(e)}")
            return []
    
    async def get_research_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics about stored research.
        
        Returns:
            Dictionary of research statistics
        """
        stats = {
            "total_researched_properties": 0,
            "research_by_depth": {
                "basic": 0,
                "standard": 0,
                "comprehensive": 0,
                "exhaustive": 0
            },
            "recently_updated": 0,
            "outdated_research": 0
        }
        
        if not self.supabase:
            logger.error("Cannot get research stats: Supabase client not initialized")
            return stats
        
        try:
            # Try to access the table and catch exception if it doesn't exist
            try:
                test_result = self.supabase.table(self.supabase_research_table) \
                    .select("count", count="exact") \
                    .limit(1) \
                    .execute()
            except Exception as e:
                logger.warning(f"Property research table access failed: {str(e)}")
                return stats
                
            if test_result.status_code != 200:
                logger.warning("Property research table does not exist yet")
                return stats
                
            # Get total count
            result = self.supabase.table(self.supabase_research_table) \
                .select("count", count="exact") \
                .execute()
            
            stats["total_researched_properties"] = result.count or 0
            
            # Get counts by research depth
            depths = ["basic", "standard", "comprehensive", "exhaustive"]
            for depth in depths:
                result = self.supabase.table(self.supabase_research_table) \
                    .select("count", count="exact") \
                    .eq("research_depth", depth) \
                    .execute()
                stats["research_by_depth"][depth] = result.count or 0
            
            # Get recently updated (within last 7 days)
            from datetime import timedelta
            threshold_time = (datetime.now() - timedelta(days=7)).isoformat()
            result = self.supabase.table(self.supabase_research_table) \
                .select("count", count="exact") \
                .gte("updated_at", threshold_time) \
                .execute()
            stats["recently_updated"] = result.count or 0
            
            # Get outdated research (over 30 days)
            threshold_time = (datetime.now() - timedelta(days=30)).isoformat()
            result = self.supabase.table(self.supabase_research_table) \
                .select("count", count="exact") \
                .lt("updated_at", threshold_time) \
                .execute()
            stats["outdated_research"] = result.count or 0
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get research stats: {str(e)}")
            return stats
    
    def _prepare_research_for_supabase(self, property_id: str, research_results: Dict[str, Any]) -> Dict[str, Any]:
        """Convert research results to a format suitable for Supabase storage."""
        # Create a copy to avoid modifying the original
        processed_results = research_results.copy()
        
        # Make sure we have a property ID
        processed_results["property_id"] = property_id
        
        # If modules exists, convert to JSON string
        if "modules" in processed_results and isinstance(processed_results["modules"], dict):
            # Store modules as JSONB
            modules_json = processed_results["modules"]
        else:
            modules_json = {}
        
        # Create simplified Supabase record
        supabase_record = {
            "property_id": property_id,
            "research_depth": processed_results.get("research_depth", "standard"),
            "research_date": processed_results.get("research_date", datetime.now().isoformat()),
            "executive_summary": processed_results.get("executive_summary", ""),
            "modules": modules_json,
            "updated_at": datetime.now().isoformat()
        }
        
        return supabase_record
    
    def _convert_from_supabase_format(self, supabase_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert from Supabase storage format back to original structure."""
        research_results = {
            "property_id": supabase_data.get("property_id"),
            "research_depth": supabase_data.get("research_depth", "standard"),
            "research_date": supabase_data.get("research_date"),
            "executive_summary": supabase_data.get("executive_summary", ""),
            "modules": supabase_data.get("modules", {})
        }
        
        return research_results
    
    def _save_research_to_neo4j(self, property_id: str, research_results: Dict[str, Any]) -> None:
        """Save research results to Neo4j database with proper relationships."""
        if not self.neo4j_driver:
            raise ValueError("Neo4j driver not initialized")
        
        with self.neo4j_driver.session(database=self.neo4j_database) as session:
            # Create or update PropertyResearch node
            session.run(
                """
                MERGE (r:PropertyResearch {property_id: $property_id})
                SET r.research_depth = $research_depth,
                    r.research_date = $research_date,
                    r.executive_summary = $executive_summary,
                    r.updated_at = datetime()
                RETURN r
                """,
                property_id=property_id,
                research_depth=research_results.get("research_depth", "standard"),
                research_date=research_results.get("research_date", datetime.now().isoformat()),
                executive_summary=research_results.get("executive_summary", "")
            )
            
            # Link PropertyResearch to Property
            session.run(
                """
                MATCH (r:PropertyResearch {property_id: $property_id})
                MATCH (p:Property {id: $property_id})
                MERGE (p)-[rel:HAS_RESEARCH]->(r)
                RETURN r, p
                """,
                property_id=property_id
            )
            
            # Create relationships based on research content
            modules = research_results.get("modules", {})
            
            # Market relationships
            if "market_conditions" in modules:
                market_data = modules["market_conditions"]
                if "overview" in market_data:
                    city = market_data["overview"].get("city")
                    state = market_data["overview"].get("state")
                    
                    if city and state:
                        # Create or get Market node
                        session.run(
                            """
                            MERGE (m:Market {city: $city, state: $state})
                            ON CREATE SET m.created_at = datetime()
                            SET m.updated_at = datetime()
                            WITH m
                            
                            MATCH (p:Property {id: $property_id})
                            MERGE (p)-[rel:IN_MARKET]->(m)
                            
                            MATCH (r:PropertyResearch {property_id: $property_id})
                            MERGE (r)-[rel2:ANALYZES_MARKET]->(m)
                            
                            RETURN m, p, r
                            """,
                            city=city,
                            state=state,
                            property_id=property_id
                        )
            
            # Risk relationships
            if "risk_assessment" in modules:
                risk_data = modules["risk_assessment"]
                risk_level = risk_data.get("overall_risk_score", {}).get("risk_level", "moderate")
                
                # Add risk level to research node
                session.run(
                    """
                    MATCH (r:PropertyResearch {property_id: $property_id})
                    SET r.risk_level = $risk_level
                    RETURN r
                    """,
                    property_id=property_id,
                    risk_level=risk_level
                )
                
                # Create RiskFactor nodes for each major risk
                risk_categories = ["physical_risks", "environmental_risks", "financial_risks", 
                                 "market_risks", "legal_regulatory_risks", "tenant_risks"]
                
                for category in risk_categories:
                    if category in risk_data:
                        category_data = risk_data[category]
                        if isinstance(category_data, dict) and "risk_level" in category_data:
                            # Create risk factor node and relationship
                            session.run(
                                """
                                MATCH (r:PropertyResearch {property_id: $property_id})
                                
                                MERGE (rf:RiskFactor {
                                    property_id: $property_id,
                                    category: $category
                                })
                                
                                SET rf.risk_level = $risk_level,
                                    rf.risk_score = $risk_score,
                                    rf.updated_at = datetime()
                                
                                MERGE (r)-[rel:HAS_RISK_FACTOR]->(rf)
                                
                                RETURN rf
                                """,
                                property_id=property_id,
                                category=category.replace("_risks", ""),
                                risk_level=category_data.get("risk_level", "moderate"),
                                risk_score=category_data.get("risk_score", 5)
                            )
            
            # Investment relationships
            if "investment_potential" in modules:
                investment_data = modules["investment_potential"]
                
                # Add cap rate and other key metrics as properties on the research node
                cap_rate = investment_data.get("cap_rate")
                irr = investment_data.get("projected_irr")
                
                if cap_rate or irr:
                    properties_to_set = {}
                    if cap_rate:
                        properties_to_set["cap_rate"] = cap_rate
                    if irr:
                        properties_to_set["projected_irr"] = irr
                    
                    # Dynamically build SET clause
                    set_clause = ", ".join([f"r.{k} = ${k}" for k in properties_to_set.keys()])
                    
                    session.run(
                        f"""
                        MATCH (r:PropertyResearch {{property_id: $property_id}})
                        SET {set_clause}
                        RETURN r
                        """,
                        property_id=property_id,
                        **properties_to_set
                    )
    
    async def _update_property_with_enriched_data(self, property_id: str, research_results: Dict[str, Any]) -> None:
        """
        Update the properties table with enriched data from research results.
        
        Args:
            property_id: The unique identifier for the property
            research_results: The deep research results containing enriched data
        """
        try:
            # Extract modules with the enriched data
            modules = research_results.get("modules", {})
            property_details = modules.get("property_details", {})
            
            # Skip if no property details available or it has an error
            if not property_details or "error" in property_details:
                logger.warning(f"No valid property details to update for property {property_id}")
                return
            
            # Extract fields that should be updated in the properties table
            update_fields = {}
            
            # Map of property_details fields to properties table fields
            # Only include fields that exist in the properties table
            field_mapping = {
                "address": "address",
                "city": "city",
                "state": "state",
                "zip_code": "zip_code",
                "latitude": "latitude",
                "longitude": "longitude",
                "units": "units",
                "year_built": "year_built",
                "property_type": "property_type",
                "property_status": "property_status"
                # "property_website" field doesn't exist in properties table
            }
            
            # Add fields to update if they exist in property_details and aren't empty
            for detail_field, table_field in field_mapping.items():
                if detail_field in property_details and property_details[detail_field]:
                    update_fields[table_field] = property_details[detail_field]
            
            # Skip update if no fields to update
            if not update_fields:
                logger.info(f"No fields to update for property {property_id}")
                return
                
            # Add updated_at timestamp
            update_fields["updated_at"] = datetime.now().isoformat()
            
            # Update the properties table
            logger.info(f"Updating property {property_id} with enriched data: {list(update_fields.keys())}")
            result = self.supabase.table(self.supabase_property_table) \
                .update(update_fields) \
                .eq("id", property_id) \
                .execute()
                
            logger.info(f"Successfully updated property {property_id} with enriched data")
        except Exception as e:
            logger.error(f"Error updating property with enriched data: {str(e)}")

    def _convert_from_neo4j_format(self, neo4j_node: Any) -> Dict[str, Any]:
        """Convert from Neo4j node format back to original structure."""
        # Extract base properties
        node_props = dict(neo4j_node)
        
        # Basic structure
        research_results = {
            "property_id": node_props.get("property_id"),
            "research_depth": node_props.get("research_depth", "standard"),
            "research_date": node_props.get("research_date"),
            "executive_summary": node_props.get("executive_summary", ""),
            "modules": {}
        }
        
        # We need to fetch modules separately since they are in related nodes
        # For a real implementation, this would require additional Neo4j queries
        
        return research_results
    
    def close(self):
        """Close database connections."""
        if self.neo4j_driver:
            self.neo4j_driver.close()
            logger.info("Neo4j driver closed")

# Create SQL to set up the research table in Supabase
def get_supabase_research_table_sql():
    """Get SQL to create the property_research table in Supabase."""
    return """
    CREATE TABLE property_research (
      id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
      research_depth TEXT NOT NULL DEFAULT 'standard',
      research_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
      executive_summary TEXT,
      modules JSONB,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    -- Create index on property_id for faster lookups
    CREATE INDEX idx_property_research_property_id ON property_research(property_id);

    -- Create index on research_depth for filtering
    CREATE INDEX idx_property_research_depth ON property_research(research_depth);

    -- Enable Row Level Security
    ALTER TABLE property_research ENABLE ROW LEVEL SECURITY;

    -- Create policies
    CREATE POLICY "Property research is viewable by everyone" 
      ON property_research FOR SELECT USING (true);

    CREATE POLICY "Property research is editable by authenticated users" 
      ON property_research FOR UPDATE USING (auth.role() = 'authenticated');

    CREATE POLICY "Property research is insertable by authenticated users" 
      ON property_research FOR INSERT WITH CHECK (auth.role() = 'authenticated');
    """

# Create Cypher to set up Neo4j constraints and indexes
def get_neo4j_setup_cypher():
    """Get Cypher queries to set up Neo4j constraints and indexes."""
    return [
        # Create constraints
        """
        CREATE CONSTRAINT property_id_constraint IF NOT EXISTS
        FOR (p:Property) REQUIRE p.id IS UNIQUE
        """,
        
        """
        CREATE CONSTRAINT property_research_id_constraint IF NOT EXISTS
        FOR (r:PropertyResearch) REQUIRE r.property_id IS UNIQUE
        """,
        
        """
        CREATE CONSTRAINT market_constraint IF NOT EXISTS
        FOR (m:Market) REQUIRE (m.city, m.state) IS UNIQUE
        """,
        
        # Create indexes
        """
        CREATE INDEX property_type_index IF NOT EXISTS
        FOR (p:Property) ON (p.property_type)
        """,
        
        """
        CREATE INDEX research_depth_index IF NOT EXISTS
        FOR (r:PropertyResearch) ON (r.research_depth)
        """,
        
        """
        CREATE INDEX risk_level_index IF NOT EXISTS
        FOR (r:PropertyResearch) ON (r.risk_level)
        """
    ]
