from bson import ObjectId
from typing import List, Dict, Any

def convert_objectid_to_string(document: Dict[str, Any]) -> Dict[str, Any]:
    """Convert ObjectId fields to strings in a MongoDB document."""
    if "_id" in document:
        document["id"] = str(document["_id"])
        del document["_id"]
    
    # Handle nested ObjectId fields if any
    for key, value in document.items():
        if isinstance(value, ObjectId):
            document[key] = str(value)
        elif isinstance(value, list):
            document[key] = [
                convert_objectid_to_string(item) if isinstance(item, dict) else 
                str(item) if isinstance(item, ObjectId) else item
                for item in value
            ]
        elif isinstance(value, dict):
            document[key] = convert_objectid_to_string(value)
    
    return document

def convert_documents_list(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert a list of MongoDB documents, handling ObjectId conversion."""
    return [convert_objectid_to_string(doc.copy()) for doc in documents]
