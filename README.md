# Google Maps A2A Server

An open-source Agent2Agent (A2A) compliant server that provides Google Maps capabilities to other agents via a standardized protocol.

## Features

- **A2A Protocol Compliance**: Implements the Agent2Agent protocol for seamless agent-to-agent communication
- **Google Maps API Integration**: Provides access to various Google Maps services:
  - Geocoding (address to coordinates)
  - Reverse geocoding (coordinates to address)
  - Directions between locations
  - Places search
  - Place details
  - Distance matrix calculations
- **Task Lifecycle Management**: Handles the entire task lifecycle (created, in-progress, completed, failed)
- **Capability Discovery**: Provides an agent card that describes available capabilities
- **Security**: Basic API key authentication

## Prerequisites

- Python 3.8+
- Google Maps API key
- Docker (optional, for containerized deployment)

## Installation

### Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/google-maps-a2a.git
   cd google-maps-a2a
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   # Create a .env file
   echo "API_KEY=your_api_key_here" > .env
   echo "GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here" >> .env
   ```

4. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

### Docker Setup

1. Build the Docker image:
   ```bash
   docker build -t google-maps-a2a .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 \
     -e API_KEY=your_api_key_here \
     -e GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here \
     google-maps-a2a
   ```

## Usage

### Agent Card

To discover the server's capabilities, send a GET request to the `/agent-card` endpoint:

```bash
curl http://localhost:8000/agent-card
```

### Creating a Task

To create a new task, send a POST request to the `/tasks` endpoint:

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

### Checking Task Status

To check the status of a task, send a GET request to the `/tasks/{task_id}` endpoint:

```bash
curl http://localhost:8000/tasks/your-task-id-here \
  -H "X-API-Key: your_api_key_here"
```

### Executing a Task

To execute a task, send a PUT request to the `/tasks/{task_id}/execute` endpoint:

```bash
curl -X PUT http://localhost:8000/tasks/your-task-id-here/execute \
  -H "X-API-Key: your_api_key_here"
```

## API Documentation

Once the server is running, you can access the Swagger UI documentation at:

```
http://localhost:8000/docs
```

## Example Workflows

### Geocoding

1. Create a geocoding task:
   ```json
   {
     "type": "geocode",
     "input": {
       "format": "text",
       "content": "1600 Amphitheatre Parkway, Mountain View, CA"
     }
   }
   ```

2. Execute the task and receive coordinates:
   ```json
   {
     "status": "completed",
     "output": {
       "format": "application/json",
       "content": {
         "results": [
           {
             "geometry": {
               "location": {
                 "lat": 37.4224764,
                 "lng": -122.0842499
               }
             },
             "formatted_address": "1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA",
             "place_id": "ChIJ2eUgeAK6j4ARbn5u_wAGqWA"
           }
         ],
         "status": "OK"
       }
     }
   }
   ```

### Directions

1. Create a directions task:
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

2. Execute the task to get route information.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Google Maps Platform for their mapping services
- FastAPI for the web framework
- The A2A protocol community