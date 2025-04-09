# A2A Protocol Implementation Details

This document provides information about how the Google Maps A2A server implements the [Agent2Agent (A2A) protocol](https://github.com/google/A2A).

## Protocol Overview

The Agent2Agent (A2A) protocol is a specification created by Google for enabling communication between AI agents. It defines a standardized way for agents to:

1. Discover each other's capabilities
2. Submit tasks for execution
3. Monitor task progress
4. Receive task results

## Key Components

### Agent Card

The agent card is a JSON document that describes the agent's capabilities, input/output formats, and authentication requirements. It's available at the `/agent-card` endpoint:

```json
{
  "schema_version": "v1",
  "name": "Google Maps A2A",
  "description": "An A2A-compliant agent that provides Google Maps capabilities",
  "version": "1.0.0",
  "contact": "https://github.com/pab1it0/google-maps-a2a",
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
    // Other tasks...
  ]
}
```

### Tasks

Tasks are the primary unit of work in the A2A protocol. Each task has:

- A unique ID
- A type (e.g., "geocode", "directions")
- Status (created, in_progress, completed, or failed)
- Input data with format
- Output data with format
- Timestamps for creation and updates

The task lifecycle is:

1. **Creation**: Client submits a task to the `/tasks` endpoint
2. **Execution**: Client requests execution via `/tasks/{task_id}/execute`
3. **Status Checking**: Client checks status via `/tasks/{task_id}`
4. **Result Retrieval**: Client uses the same endpoint to retrieve results

### Input/Output Formats

Our implementation supports multiple input and output formats:

| Format | Description |
|--------|-------------|
| `text` | Plain text for simple inputs and outputs |
| `application/json` | Structured JSON data |
| `application/geo+json` | GeoJSON format for geographic data |
| `text/markdown` | Markdown-formatted text |

## A2A Protocol Implementation

### Endpoint Structure

Our implementation follows the HTTP/JSON-RPC approach with these endpoints:

- `GET /agent-card`: Provides the agent descriptor
- `POST /tasks`: Creates a new task
- `GET /tasks/{task_id}`: Retrieves task status and results
- `PUT /tasks/{task_id}/execute`: Executes a task

### Authentication

We use API key authentication as specified in the A2A protocol. Clients must include the API key in the `X-API-Key` header for all endpoints except `/agent-card`.

### Task Execution Model

Tasks in our implementation follow this flow:

1. Task creation establishes the task type and input
2. Task execution processes the input and performs the specified operation
3. Task status updates as progress occurs
4. Task output is populated with results in the requested format

## Extending the Implementation

To add new task types to the server:

1. Add the task to the `AGENT_CARD` in `main.py`
2. Create a handler function following the pattern of existing handlers
3. Update the execution dispatch logic in `execute_task`

## Differences from A2A Specification

Our implementation closely follows the A2A protocol with a few enhancements:

1. **Additional Output Formats**: We support GeoJSON for geographic data
2. **Task Input**: We directly include task input in the creation request
3. **Execution Endpoint**: We use a dedicated endpoint for task execution

## Future Improvements

To further enhance A2A compliance:

1. Add WebSocket support for real-time status updates
2. Implement persistent storage for tasks
3. Add fine-grained authentication and authorization
4. Support agent-to-agent discovery mechanisms