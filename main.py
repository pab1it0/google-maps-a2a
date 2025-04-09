import os
import uuid
import json
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union

import httpx
from fastapi import FastAPI, HTTPException, Depends, Header, Request, Body
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Initialize FastAPI app
app = FastAPI(title="Google Maps A2A Server")

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables (in a production environment, use proper env variable management)
API_KEY = os.getenv("API_KEY", "default_api_key")  # Default for development
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "your_google_maps_api_key_here")

# Simple API key security
api_key_header = APIKeyHeader(name="X-API-Key")

# Models for A2A Protocol
class TaskStatus(str, Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class InputFormat(str, Enum):
    TEXT = "text"
    JSON = "application/json"
    MARKDOWN = "text/markdown"

class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "application/json"
    MARKDOWN = "text/markdown"
    GEOJSON = "application/geo+json"

class TaskInput(BaseModel):
    format: InputFormat
    content: Union[str, Dict[str, Any]]

class TaskOutput(BaseModel):
    format: OutputFormat
    content: Union[str, Dict[str, Any]]

class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    status: TaskStatus = TaskStatus.CREATED
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    input: TaskInput
    output: Optional[TaskOutput] = None

# In-memory database for tasks
tasks_db: Dict[str, Task] = {}

# Agent Card for capability discovery
AGENT_CARD = {
    "schema_version": "v1",
    "name": "Google Maps A2A",
    "description": "An A2A-compliant agent that provides Google Maps capabilities",
    "version": "1.0.0",
    "contact": "https://github.com/yourusername/google-maps-a2a",
    "auth": {
        "type": "api_key",
        "header_name": "X-API-Key"
    },
    "input_formats": [
        {"format": "text", "description": "Natural language query for maps operations"},
        {"format": "application/json", "description": "Structured data for maps operations"}
    ],
    "output_formats": [
        {"format": "text", "description": "Text response with maps information"},
        {"format": "application/json", "description": "JSON response with structured maps data"},
        {"format": "application/geo+json", "description": "GeoJSON formatted location data"}
    ],
    "tasks": [
        {
            "type": "geocode",
            "description": "Convert addresses to latitude and longitude coordinates",
            "input_formats": ["text", "application/json"],
            "output_formats": ["application/json", "application/geo+json"]
        },
        {
            "type": "reverse_geocode",
            "description": "Convert coordinates to addresses",
            "input_formats": ["application/json"],
            "output_formats": ["application/json", "text"]
        },
        {
            "type": "directions",
            "description": "Get directions between locations",
            "input_formats": ["application/json"],
            "output_formats": ["application/json", "text"]
        },
        {
            "type": "places_search",
            "description": "Search for places using Google Places API",
            "input_formats": ["text", "application/json"],
            "output_formats": ["application/json", "application/geo+json"]
        },
        {
            "type": "place_details",
            "description": "Get detailed information about a specific place",
            "input_formats": ["application/json"],
            "output_formats": ["application/json"]
        },
        {
            "type": "distance_matrix",
            "description": "Calculate travel distance and time between points",
            "input_formats": ["application/json"],
            "output_formats": ["application/json"]
        }
    ]
}

# Authentication dependency
async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key

# Google Maps API Client
async def google_maps_client():
    """Create an HTTP client for Google Maps API requests"""
    async with httpx.AsyncClient(
        base_url="https://maps.googleapis.com/maps/api",
        params={"key": GOOGLE_MAPS_API_KEY}
    ) as client:
        yield client

# Route Handlers
@app.get("/")
async def root():
    """Root endpoint with basic server information"""
    return {"message": "Google Maps A2A Server", "version": "1.0.0"}

@app.get("/agent-card")
async def get_agent_card():
    """Return the agent card for capability discovery"""
    return AGENT_CARD

@app.post("/tasks", dependencies=[Depends(verify_api_key)])
async def create_task(task: Task):
    """Create a new task"""
    # Validate task type against supported types
    supported_tasks = [t["type"] for t in AGENT_CARD["tasks"]]
    if task.type not in supported_tasks:
        raise HTTPException(status_code=400, detail=f"Unsupported task type. Must be one of: {supported_tasks}")
    
    # Save task to database
    tasks_db[task.id] = task
    return task

@app.get("/tasks/{task_id}", dependencies=[Depends(verify_api_key)])
async def get_task(task_id: str):
    """Get a task by ID"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks_db[task_id]

@app.put("/tasks/{task_id}/execute", dependencies=[Depends(verify_api_key)])
async def execute_task(
    task_id: str, 
    client: httpx.AsyncClient = Depends(google_maps_client)
):
    """Execute a task by ID"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks_db[task_id]
    task.status = TaskStatus.IN_PROGRESS
    task.updated_at = datetime.now().isoformat()
    
    try:
        # Handle different task types
        if task.type == "geocode":
            result = await handle_geocode(task, client)
        elif task.type == "reverse_geocode":
            result = await handle_reverse_geocode(task, client)
        elif task.type == "directions":
            result = await handle_directions(task, client)
        elif task.type == "places_search":
            result = await handle_places_search(task, client)
        elif task.type == "place_details":
            result = await handle_place_details(task, client)
        elif task.type == "distance_matrix":
            result = await handle_distance_matrix(task, client)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported task type: {task.type}")
        
        # Update task with result
        task.output = result
        task.status = TaskStatus.COMPLETED
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.output = TaskOutput(
            format=OutputFormat.TEXT,
            content=f"Error executing task: {str(e)}"
        )
    
    task.updated_at = datetime.now().isoformat()
    return task

# Task handlers for different Google Maps operations
async def handle_geocode(task: Task, client: httpx.AsyncClient):
    """Handle geocode task - convert address to coordinates"""
    if task.input.format == InputFormat.TEXT:
        address = task.input.content
    else:  # JSON
        address = task.input.content.get("address", "")
    
    response = await client.get("/geocode/json", params={"address": address})
    data = response.json()
    
    if response.status_code != 200 or data.get("status") != "OK":
        raise HTTPException(status_code=400, detail=f"Geocoding failed: {data.get('status')}")
    
    # Format the response based on requested output format
    if task.output and task.output.format == OutputFormat.GEOJSON:
        # Convert to GeoJSON format
        result = data.get("results", [])[0]
        location = result.get("geometry", {}).get("location", {})
        geojson = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [location.get("lng"), location.get("lat")]
            },
            "properties": {
                "formatted_address": result.get("formatted_address"),
                "place_id": result.get("place_id")
            }
        }
        return TaskOutput(format=OutputFormat.GEOJSON, content=geojson)
    else:
        # Default JSON response
        return TaskOutput(format=OutputFormat.JSON, content=data)

async def handle_reverse_geocode(task: Task, client: httpx.AsyncClient):
    """Handle reverse geocode task - convert coordinates to address"""
    if task.input.format != InputFormat.JSON:
        raise HTTPException(status_code=400, detail="Reverse geocoding requires JSON input")
    
    lat = task.input.content.get("lat")
    lng = task.input.content.get("lng")
    
    if lat is None or lng is None:
        raise HTTPException(status_code=400, detail="Latitude and longitude required")
    
    response = await client.get("/geocode/json", params={"latlng": f"{lat},{lng}"})
    data = response.json()
    
    if response.status_code != 200 or data.get("status") != "OK":
        raise HTTPException(status_code=400, detail=f"Reverse geocoding failed: {data.get('status')}")
    
    # Format output based on requested format
    if task.output and task.output.format == OutputFormat.TEXT:
        result = data.get("results", [])[0]
        address = result.get("formatted_address", "Address not found")
        return TaskOutput(format=OutputFormat.TEXT, content=address)
    else:
        # Default JSON response
        return TaskOutput(format=OutputFormat.JSON, content=data)

async def handle_directions(task: Task, client: httpx.AsyncClient):
    """Handle directions task - get directions between locations"""
    if task.input.format != InputFormat.JSON:
        raise HTTPException(status_code=400, detail="Directions requires JSON input")
    
    origin = task.input.content.get("origin")
    destination = task.input.content.get("destination")
    mode = task.input.content.get("mode", "driving")
    
    if not origin or not destination:
        raise HTTPException(status_code=400, detail="Origin and destination required")
    
    response = await client.get("/directions/json", params={
        "origin": origin,
        "destination": destination,
        "mode": mode
    })
    data = response.json()
    
    if response.status_code != 200 or data.get("status") != "OK":
        raise HTTPException(status_code=400, detail=f"Directions failed: {data.get('status')}")
    
    # Format output based on requested format
    if task.output and task.output.format == OutputFormat.TEXT:
        # Simplify to text directions
        steps = []
        for route in data.get("routes", []):
            for leg in route.get("legs", []):
                for i, step in enumerate(leg.get("steps", [])):
                    steps.append(f"{i+1}. {step.get('html_instructions', '').replace('<b>', '').replace('</b>', '').replace('<div>', '. ').replace('</div>', '')}")
        
        text_directions = "\n".join(steps)
        return TaskOutput(format=OutputFormat.TEXT, content=text_directions)
    else:
        # Default JSON response
        return TaskOutput(format=OutputFormat.JSON, content=data)

async def handle_places_search(task: Task, client: httpx.AsyncClient):
    """Handle places search task"""
    if task.input.format == InputFormat.TEXT:
        query = task.input.content
        params = {"query": query, "type": "restaurant"}  # default type
    else:  # JSON
        query = task.input.content.get("query")
        location = task.input.content.get("location")
        radius = task.input.content.get("radius", 5000)
        
        params = {"query": query}
        if location:
            params["location"] = f"{location.get('lat')},{location.get('lng')}"
            params["radius"] = radius
    
    response = await client.get("/place/textsearch/json", params=params)
    data = response.json()
    
    if response.status_code != 200 or data.get("status") != "OK":
        raise HTTPException(status_code=400, detail=f"Places search failed: {data.get('status')}")
    
    # Format output based on requested format
    if task.output and task.output.format == OutputFormat.GEOJSON:
        # Convert to GeoJSON
        features = []
        for place in data.get("results", []):
            location = place.get("geometry", {}).get("location", {})
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [location.get("lng"), location.get("lat")]
                },
                "properties": {
                    "name": place.get("name"),
                    "address": place.get("formatted_address"),
                    "rating": place.get("rating"),
                    "place_id": place.get("place_id")
                }
            }
            features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        return TaskOutput(format=OutputFormat.GEOJSON, content=geojson)
    else:
        # Default JSON response
        return TaskOutput(format=OutputFormat.JSON, content=data)

async def handle_place_details(task: Task, client: httpx.AsyncClient):
    """Handle place details task"""
    if task.input.format != InputFormat.JSON:
        raise HTTPException(status_code=400, detail="Place details requires JSON input")
    
    place_id = task.input.content.get("place_id")
    
    if not place_id:
        raise HTTPException(status_code=400, detail="Place ID required")
    
    response = await client.get("/place/details/json", params={"place_id": place_id})
    data = response.json()
    
    if response.status_code != 200 or data.get("status") != "OK":
        raise HTTPException(status_code=400, detail=f"Place details failed: {data.get('status')}")
    
    # Only JSON output format supported for this task
    return TaskOutput(format=OutputFormat.JSON, content=data)

async def handle_distance_matrix(task: Task, client: httpx.AsyncClient):
    """Handle distance matrix task"""
    if task.input.format != InputFormat.JSON:
        raise HTTPException(status_code=400, detail="Distance matrix requires JSON input")
    
    origins = task.input.content.get("origins", [])
    destinations = task.input.content.get("destinations", [])
    mode = task.input.content.get("mode", "driving")
    
    if not origins or not destinations:
        raise HTTPException(status_code=400, detail="Origins and destinations required")
    
    # Format origins and destinations for the API
    origins_str = "|".join(origins)
    destinations_str = "|".join(destinations)
    
    response = await client.get("/distancematrix/json", params={
        "origins": origins_str,
        "destinations": destinations_str,
        "mode": mode
    })
    data = response.json()
    
    if response.status_code != 200 or data.get("status") != "OK":
        raise HTTPException(status_code=400, detail=f"Distance matrix failed: {data.get('status')}")
    
    # Only JSON output format supported for this task
    return TaskOutput(format=OutputFormat.JSON, content=data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)