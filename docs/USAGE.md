# Google Maps A2A Server Usage Guide

This guide provides detailed instructions for using the Google Maps A2A server.

## Table of Contents

- [Authentication](#authentication)
- [Working with Tasks](#working-with-tasks)
- [Task Types](#task-types)
  - [Geocoding](#geocoding)
  - [Reverse Geocoding](#reverse-geocoding)
  - [Directions](#directions)
  - [Places Search](#places-search)
  - [Place Details](#place-details)
  - [Distance Matrix](#distance-matrix)
- [Error Handling](#error-handling)
- [Examples](#examples)

## Authentication

All API endpoints (except for the agent card endpoint) require authentication using an API key.

Add the API key to your requests using the `X-API-Key` header:

```
X-API-Key: your_api_key_here
```

## Working with Tasks

The A2A protocol is task-based. Tasks follow this lifecycle:

1. **Created** - Initial state when a task is first created
2. **In Progress** - When a task is being executed
3. **Completed** - When a task is successfully completed
4. **Failed** - When a task execution has failed

### Creating a Task

To create a task, send a POST request to `/tasks`:

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{
    "type": "geocode",
    "input": {
      "format": "text",
      "content": "1600 Amphitheatre Parkway, Mountain View, CA"
    }
  }'
```

The response includes a task ID that you'll use to check status and results.

### Checking Task Status

To check a task's status, send a GET request to `/tasks/{task_id}`:

```bash
curl http://localhost:8000/tasks/your-task-id-here \
  -H "X-API-Key: your_api_key_here"
```

### Executing a Task

To execute a task, send a PUT request to `/tasks/{task_id}/execute`:

```bash
curl -X PUT http://localhost:8000/tasks/your-task-id-here/execute \
  -H "X-API-Key: your_api_key_here"
```

## Task Types

### Geocoding

Convert addresses to geographic coordinates.

**Input Formats:**
- `text`: Direct address string
- `application/json`: JSON object with address field

**Output Formats:**
- `application/json`: Full Google Maps API response
- `application/geo+json`: GeoJSON formatted response

**Example:**

```json
{
  "type": "geocode",
  "input": {
    "format": "text",
    "content": "1600 Amphitheatre Parkway, Mountain View, CA"
  }
}
```

### Reverse Geocoding

Convert geographic coordinates to addresses.

**Input Formats:**
- `application/json`: JSON object with lat/lng fields

**Output Formats:**
- `application/json`: Full Google Maps API response
- `text`: Simplified address string

**Example:**

```json
{
  "type": "reverse_geocode",
  "input": {
    "format": "application/json",
    "content": {
      "lat": 37.4224764,
      "lng": -122.0842499
    }
  }
}
```

### Directions

Get directions between locations.

**Input Formats:**
- `application/json`: JSON object with origin, destination, and optional mode

**Output Formats:**
- `application/json`: Full Google Maps API response
- `text`: Text instructions for navigation

**Example:**

```json
{
  "type": "directions",
  "input": {
    "format": "application/json",
    "content": {
      "origin": "San Francisco, CA",
      "destination": "Mountain View, CA",
      "mode": "driving"
    }
  }
}
```

### Places Search

Search for places using Google Places API.

**Input Formats:**
- `text`: Direct search query
- `application/json`: JSON object with query and optional location/radius

**Output Formats:**
- `application/json`: Full Google Maps API response
- `application/geo+json`: GeoJSON formatted response

**Example:**

```json
{
  "type": "places_search",
  "input": {
    "format": "application/json",
    "content": {
      "query": "restaurants",
      "location": {
        "lat": 37.4224764,
        "lng": -122.0842499
      },
      "radius": 1000
    }
  }
}
```

### Place Details

Get detailed information about a specific place.

**Input Formats:**
- `application/json`: JSON object with place_id

**Output Formats:**
- `application/json`: Full Google Maps API response

**Example:**

```json
{
  "type": "place_details",
  "input": {
    "format": "application/json",
    "content": {
      "place_id": "ChIJ2eUgeAK6j4ARbn5u_wAGqWA"
    }
  }
}
```

### Distance Matrix

Calculate distances and travel times between multiple origins and destinations.

**Input Formats:**
- `application/json`: JSON object with origins, destinations, and optional mode

**Output Formats:**
- `application/json`: Full Google Maps API response

**Example:**

```json
{
  "type": "distance_matrix",
  "input": {
    "format": "application/json",
    "content": {
      "origins": ["San Francisco, CA", "Oakland, CA"],
      "destinations": ["Mountain View, CA", "San Jose, CA"],
      "mode": "driving"
    }
  }
}
```

## Error Handling

The server returns standard HTTP status codes:

- 200: Success
- 400: Bad Request (invalid input)
- 401: Unauthorized (invalid API key)
- 404: Not Found (task not found)
- 500: Internal Server Error

Errors include a detail message explaining what went wrong.

## Examples

Here are some complete examples:

### Geocode an Address

```bash
# Create a task
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{
    "type": "geocode",
    "input": {
      "format": "text",
      "content": "1600 Amphitheatre Parkway, Mountain View, CA"
    }
  }'

# Response
{
  "id": "12345abc-def6-7890-ghij-klmnopqrstuv",
  "type": "geocode",
  "status": "created",
  "created_at": "2025-04-10T14:30:00.000000",
  "updated_at": "2025-04-10T14:30:00.000000",
  "input": {
    "format": "text",
    "content": "1600 Amphitheatre Parkway, Mountain View, CA"
  },
  "output": null
}

# Execute the task
curl -X PUT http://localhost:8000/tasks/12345abc-def6-7890-ghij-klmnopqrstuv/execute \
  -H "X-API-Key: your_api_key_here"

# Response will include the geocoding results
```

### Get Directions

```bash
# Create a task
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{
    "type": "directions",
    "input": {
      "format": "application/json",
      "content": {
        "origin": "San Francisco, CA",
        "destination": "Mountain View, CA",
        "mode": "driving"
      }
    }
  }'

# Execute the task (using the task ID from the response above)
curl -X PUT http://localhost:8000/tasks/your-task-id-here/execute \
  -H "X-API-Key: your_api_key_here"

# Response will include the directions results
```