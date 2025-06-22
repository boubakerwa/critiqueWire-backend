from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import uuid
from app.core.config import supabase_client, settings
from app.api.v1 import schemas
from supabase import create_client

class DatabaseService:
    """Service for handling database operations with Supabase."""
    
    def __init__(self):
        self.supabase = supabase_client
    
    async def store_analysis(self, analysis_data: Dict[str, Any], user_id: str, jwt_token: str = None) -> str:
        """
        Store analysis results in the database.
        
        Args:
            analysis_data: The analysis data to store
            user_id: The ID of the user who created the analysis
            
        Returns:
            The analysis ID that was stored
        """
        try:
            # Generate a proper UUID for the analysis
            analysis_id = str(uuid.uuid4())
            
            # Determine the analysis type based on content
            db_analysis_type = "url" if analysis_data.get("url") else "text"
            
            # Prepare the data for storage
            analysis_record = {
                "id": analysis_id,
                "user_id": user_id,
                "title": analysis_data.get("title", ""),
                "preset": analysis_data.get("preset", "general"),
                "analysis_type": db_analysis_type,  # Use 'url' or 'text' as per schema
                "status": analysis_data.get("status", "pending"),
                "article_id": analysis_data.get("articleId"),
                "url": analysis_data.get("url"),
                "content_preview": analysis_data.get("content", "")[:500] if analysis_data.get("content") else "",
                "results": analysis_data.get("results"),  # Store as dict, Supabase will convert to JSONB
                "metadata": {
                    "original_analysis_types": analysis_data.get("analysisTypes", []),  # Store the original analysis types
                    "processingTime": analysis_data.get("processingTime", 0.0),  # Use camelCase to match schema
                    "preset": analysis_data.get("preset", "general"),
                    "createdAt": datetime.utcnow().isoformat(),
                    "wordsAnalyzed": len(analysis_data.get("content", "").split()) if analysis_data.get("content") else 0,
                    **analysis_data.get("metadata", {})
                }
            }
            
            print("[DEBUG] analysis_record to insert:", json.dumps(analysis_record, indent=2, default=str))
            
            # Use JWT token for authentication if provided
            if jwt_token:
                # Create a new client instance 
                client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
                # Set the session with the JWT token - we'll use the access token as both access and refresh for this operation
                try:
                    client.auth.set_session(jwt_token, jwt_token)
                except Exception as e:
                    print(f"[DEBUG] Failed to set session: {e}")
                    # Fallback: try to set headers directly on the client
                    if hasattr(client, 'postgrest'):
                        client.postgrest.session.headers.update({"Authorization": f"Bearer {jwt_token}"})
            else:
                client = self.supabase
            
            # Insert into the analyses table
            result = client.table("analyses").insert(analysis_record).execute()
            
            if result.data:
                # Update the original analysis data with the new UUID
                analysis_data["analysisId"] = analysis_id
                return analysis_id
            else:
                raise Exception("Failed to store analysis - no data returned")
                
        except Exception as e:
            print(f"Error storing analysis: {e}")
            raise
    
    async def get_analysis(self, analysis_id: str, user_id: str, jwt_token: str = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve an analysis by ID for a specific user.
        
        Args:
            analysis_id: The analysis ID to retrieve
            user_id: The ID of the user requesting the analysis
            
        Returns:
            The analysis data or None if not found
        """
        try:
            # Use JWT token for authentication if provided
            if jwt_token:
                client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
                try:
                    client.auth.set_session(jwt_token, jwt_token)
                except Exception as e:
                    print(f"[DEBUG] Failed to set session: {e}")
                    if hasattr(client, 'postgrest'):
                        client.postgrest.session.headers.update({"Authorization": f"Bearer {jwt_token}"})
            else:
                client = self.supabase
            
            result = client.table("analyses").select("*").eq("id", analysis_id).eq("user_id", user_id).execute()
            
            if result.data:
                analysis_record = result.data[0]
                formatted_response = self._format_analysis_response(analysis_record)
                return formatted_response
            else:
                return None
                
        except Exception as e:
            print(f"Error retrieving analysis: {e}")
            return None
    
    async def get_user_analyses(
        self, 
        user_id: str, 
        limit: int = 20, 
        offset: int = 0,
        search: Optional[str] = None,
        preset: Optional[str] = None,
        analysis_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        jwt_token: str = None
    ) -> Dict[str, Any]:
        """
        Retrieve paginated analysis history for a user with filtering.
        
        Args:
            user_id: The user ID
            limit: Number of analyses to return
            offset: Number of analyses to skip
            search: Search term for title or content
            preset: Filter by analysis preset
            analysis_type: Filter by analysis type
            date_from: Filter analyses from this date
            date_to: Filter analyses up to this date
            
        Returns:
            Dictionary with analyses and pagination info
        """
        try:
            # Use JWT token for authentication if provided
            if jwt_token:
                client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
                try:
                    client.auth.set_session(jwt_token, jwt_token)
                except Exception as e:
                    print(f"[DEBUG] Failed to set session: {e}")
                    if hasattr(client, 'postgrest'):
                        client.postgrest.session.headers.update({"Authorization": f"Bearer {jwt_token}"})
            else:
                client = self.supabase
                
            # Start with base query
            query = client.table("analyses").select("*").eq("user_id", user_id)
            
            # Apply filters
            if search:
                query = query.or_(f"title.ilike.%{search}%,content_preview.ilike.%{search}%")
            
            if preset:
                query = query.eq("preset", preset)
                
            if analysis_type:
                query = query.eq("analysis_type", analysis_type)
                
            if date_from:
                query = query.gte("created_at", date_from)
                
            if date_to:
                query = query.lte("created_at", date_to)
            
            # Apply ordering and pagination
            query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
            
            result = query.execute()
            
            # Get total count for pagination
            count_query = client.table("analyses").select("id", count="exact").eq("user_id", user_id)
            count_result = count_query.execute()
            total_count = count_result.count if count_result.count is not None else 0
            
            # Format the response
            analyses = []
            for record in result.data:
                analysis_item = {
                    "analysisId": record["id"],
                    "title": record["title"],
                    "preset": record["preset"],
                    "analysisType": record["analysis_type"],
                    "createdAt": record["created_at"],
                    "summary": self._generate_summary(record),
                    "analysisScore": self._extract_analysis_score(record),
                    "article": self._format_article_summary(record) if record.get("url") else None
                }
                analyses.append(analysis_item)
            
            return {
                "items": analyses,
                "nextCursor": str(offset + limit) if offset + limit < total_count else None,
                "totalCount": total_count
            }
            
        except Exception as e:
            print(f"Error retrieving user analyses: {e}")
            return {"items": [], "nextCursor": None, "totalCount": 0}
    
    async def update_analysis_status(self, analysis_id: str, user_id: str, status: str, results: Optional[Dict] = None, jwt_token: str = None) -> bool:
        """
        Update the status and optionally results of an analysis.
        
        Args:
            analysis_id: The analysis ID to update
            user_id: The user ID (for security)
            status: The new status
            results: Optional results to store
            jwt_token: Optional JWT token for authentication
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {
                "status": status
            }
            
            if results:
                update_data["results"] = results  # Store as dict, Supabase will convert to JSONB
            
            # Use JWT token for authentication if provided
            if jwt_token:
                client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
                try:
                    client.auth.set_session(jwt_token, jwt_token)
                except Exception as e:
                    print(f"[DEBUG] Failed to set session: {e}")
                    if hasattr(client, 'postgrest'):
                        client.postgrest.session.headers.update({"Authorization": f"Bearer {jwt_token}"})
            else:
                client = self.supabase
            
            print(f"[DEBUG] Updating analysis {analysis_id} status to {status} for user {user_id}")
            
            # First, let's check if the record exists
            check_result = client.table("analyses").select("id, user_id, status").eq("id", analysis_id).execute()
            print(f"[DEBUG] Analysis record check: {check_result}")
            
            if not check_result.data:
                print(f"[ERROR] No analysis found with id {analysis_id}")
                return False
                
            stored_user_id = check_result.data[0].get("user_id")
            print(f"[DEBUG] Stored user_id: {stored_user_id}, Provided user_id: {user_id}")
            print(f"[DEBUG] User IDs match: {stored_user_id == user_id}")
            
            # If user IDs don't match, try updating without user_id filter (for background tasks)
            if stored_user_id != user_id:
                print(f"[WARNING] User ID mismatch, updating analysis {analysis_id} without user_id filter")
                result = client.table("analyses").update(update_data).eq("id", analysis_id).execute()
            else:
                result = client.table("analyses").update(update_data).eq("id", analysis_id).eq("user_id", user_id).execute()
            print(f"[DEBUG] Update result: {result}")
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"Error updating analysis status: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def create_analysis(
        self,
        analysis_id: str,
        user_id: str,
        content: str,
        analysis_types: List[str],
        content_type: str,
        preset: str,
        jwt_token: str = None,
        title: str = "",
        url: str = None,
        article_id: str = None
    ) -> bool:
        """
        Create a new analysis record in the database.
        
        Args:
            analysis_id: The analysis ID
            user_id: The user ID
            content: The content being analyzed
            analysis_types: List of analysis types (e.g., ['bias', 'sentiment'])
            content_type: The content type ('url' or 'text')
            preset: The analysis preset
            jwt_token: Optional JWT token for authentication
            title: Optional title
            url: Optional URL if content_type is 'url'
            article_id: Optional article ID if content_type is 'url'
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare the data for storage
            analysis_record = {
                "id": analysis_id,
                "user_id": user_id,
                "title": title or "Analysis",
                "preset": preset,
                "analysis_type": content_type,  # This should be 'url' or 'text', NOT comma-separated analysis types
                "status": "pending",
                "article_id": article_id,
                "url": url,
                "content_preview": content[:500] if content else "",
                "results": None,
                "metadata": {
                    "original_analysis_types": analysis_types,  # Store the actual analysis types here
                    "processingTime": 0.0,  # Use camelCase to match schema
                    "preset": preset,
                    "createdAt": datetime.utcnow().isoformat(),
                    "wordsAnalyzed": len(content.split()) if content else 0,
                }
            }
            
            print("[DEBUG] Creating analysis record:", json.dumps(analysis_record, indent=2, default=str))
            
            # Use JWT token for authentication if provided
            if jwt_token:
                client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
                try:
                    client.auth.set_session(jwt_token, jwt_token)
                except Exception as e:
                    print(f"[DEBUG] Failed to set session: {e}")
                    if hasattr(client, 'postgrest'):
                        client.postgrest.session.headers.update({"Authorization": f"Bearer {jwt_token}"})
            else:
                client = self.supabase
            
            # Insert into the analyses table
            result = client.table("analyses").insert(analysis_record).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"Error creating analysis: {e}")
            return False
    
    def _format_analysis_response(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Format a database record into the API response format."""
        try:
            # Safely extract fields with defaults
            results = record.get("results")
            metadata = record.get("metadata") or {}
            
            # Ensure metadata is a dict (sometimes it might be a string)
            if isinstance(metadata, str):
                try:
                    import json
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            
            # Format metadata to match the expected schema
            formatted_metadata = {
                "processingTime": metadata.get("processing_time") or metadata.get("processingTime", 0.0),
                "preset": metadata.get("preset", "general"),
                "wordsAnalyzed": metadata.get("wordsAnalyzed", 0),
                "createdAt": metadata.get("createdAt") or record.get("created_at") or datetime.utcnow().isoformat()
            }
            
            # Build the response with safe field access
            data = {
                "analysisId": str(record.get("id", "")),
                "title": str(record.get("title", "")),
                "articleId": record.get("article_id"),
                "analysisType": str(record.get("analysis_type", "text")),  # Should be 'url' or 'text', not the analysis types
                "status": str(record.get("status", "pending")),
                "results": results,
                "metadata": formatted_metadata
            }
            
            # Build the final response
            response = {
                "status": "success",
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return response
            
        except Exception as e:
            print(f"Error formatting analysis response: {e}")
            import traceback
            traceback.print_exc()
            
            # Return a minimal safe response
            return {
                "status": "error",
                "data": {
                    "analysisId": str(record.get("id", "unknown")),
                    "title": str(record.get("title", "")),
                    "articleId": None,
                    "analysisType": "text",
                    "status": "error",
                    "results": None,
                    "metadata": {
                        "processingTime": 0.0,
                        "preset": "general",
                        "wordsAnalyzed": 0,
                        "createdAt": datetime.utcnow().isoformat()
                    }
                },
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _generate_summary(self, record: Dict[str, Any]) -> str:
        """Generate a summary from the analysis record."""
        try:
            if record.get("results"):
                results = record["results"]  # Already a dict from JSONB
                if results.get("executiveSummary"):
                    return results["executiveSummary"][:200] + "..." if len(results["executiveSummary"]) > 200 else results["executiveSummary"]
            
            # Get original analysis types for better summary
            metadata = record.get("metadata", {})
            original_types = metadata.get("original_analysis_types", [])
            if original_types:
                type_str = ", ".join(original_types)
            else:
                type_str = record['analysis_type']
            
            return f"{type_str.title()} analysis using {record['preset']} preset"
            
        except Exception:
            return f"{record['analysis_type'].title()} analysis using {record['preset']} preset"
    
    def _extract_analysis_score(self, record: Dict[str, Any]) -> float:
        """Extract the analysis score from the results."""
        try:
            if record.get("results"):
                results = record["results"]  # Already a dict from JSONB
                return results.get("analysisScore", 0.0)
            return 0.0
        except Exception:
            return 0.0
    
    def _format_article_summary(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Format article summary for URL-based analyses."""
        from urllib.parse import urlparse
        
        domain = urlparse(record["url"]).netloc if record.get("url") else ""
        
        return {
            "id": record.get("article_id", ""),
            "title": record["title"],
            "url": record.get("url", ""),
            "domain": domain
        }

# Create a singleton instance
database_service = DatabaseService() 