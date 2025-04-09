import asyncio
import json
import uuid
from datetime import datetime

import httpx

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "your_api_key_here"  # Replace with your API key

async def main():
    """Example A2A client for Google Maps A2A server"""
    async with httpx.AsyncClient() as client:
        # 1. Discover agent capabilities (agent card)
        print("Fetching agent card...")
        response = await client.get(f"{BASE_URL}/agent-card")
        agent_card = response.json()
        print(f"Agent name: {agent_card['name']}")
        print(f"Available tasks: {[task['type'] for task in agent_card['tasks']]}")
        print("-" * 50)
        
        # 2. Create a geocoding task
        print("Creating geocoding task...")
        task_data = {
            "id": str(uuid.uuid4()),
            "type": "geocode",
            "status": "created",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "input": {
                "format": "text",
                "content": "1600 Amphitheatre Parkway, Mountain View, CA"
            }
        }
        
        response = await client.post(
            f"{BASE_URL}/tasks",
            headers={"X-API-Key": API_KEY},
            json=task_data
        )
        
        if response.status_code != 200:
            print(f"Error creating task: {response.text}")
            return
        
        task = response.json()
        task_id = task["id"]
        print(f"Task created with ID: {task_id}")
        print("-" * 50)
        
        # 3. Execute the task
        print("Executing task...")
        response = await client.put(
            f"{BASE_URL}/tasks/{task_id}/execute",
            headers={"X-API-Key": API_KEY}
        )
        
        if response.status_code != 200:
            print(f"Error executing task: {response.text}")
            return
        
        result = response.json()
        print(f"Task status: {result['status']}")
        
        # 4. Print the result in a readable format
        if result["output"] and result["output"]["format"] == "application/json":
            output_content = result["output"]["content"]
            if "results" in output_content and len(output_content["results"]) > 0:
                location = output_content["results"][0]["geometry"]["location"]
                address = output_content["results"][0]["formatted_address"]
                print(f"Address: {address}")
                print(f"Coordinates: Latitude {location['lat']}, Longitude {location['lng']}")
        
        print("-" * 50)
        
        # 5. Create a directions task
        print("Creating directions task...")
        directions_task = {
            "id": str(uuid.uuid4()),
            "type": "directions",
            "status": "created",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "input": {
                "format": "application/json",
                "content": {
                    "origin": "San Francisco, CA",
                    "destination": "Mountain View, CA",
                    "mode": "driving"
                }
            }
        }
        
        response = await client.post(
            f"{BASE_URL}/tasks",
            headers={"X-API-Key": API_KEY},
            json=directions_task
        )
        
        if response.status_code != 200:
            print(f"Error creating directions task: {response.text}")
            return
        
        directions_task_id = response.json()["id"]
        print(f"Directions task created with ID: {directions_task_id}")
        print("-" * 50)
        
        # 6. Execute the directions task
        print("Executing directions task...")
        response = await client.put(
            f"{BASE_URL}/tasks/{directions_task_id}/execute",
            headers={"X-API-Key": API_KEY}
        )
        
        if response.status_code != 200:
            print(f"Error executing directions task: {response.text}")
            return
        
        directions_result = response.json()
        print(f"Directions task status: {directions_result['status']}")
        
        # 7. Process and print directions in a readable format
        if directions_result["output"] and directions_result["output"]["format"] == "application/json":
            routes = directions_result["output"]["content"].get("routes", [])
            if routes:
                legs = routes[0].get("legs", [])
                if legs:
                    distance = legs[0].get("distance", {}).get("text", "Unknown")
                    duration = legs[0].get("duration", {}).get("text", "Unknown")
                    print(f"Distance: {distance}")
                    print(f"Duration: {duration}")
                    
                    # Print the first few steps of directions
                    print("\nDirections:")
                    steps = legs[0].get("steps", [])
                    for i, step in enumerate(steps[:3]):  # First 3 steps
                        instruction = step.get("html_instructions", "")
                        # Remove HTML tags for better readability
                        instruction = instruction.replace("<b>", "").replace("</b>", "")
                        instruction = instruction.replace("<div>", " ").replace("</div>", "")
                        print(f"  {i+1}. {instruction}")
                    
                    if len(steps) > 3:
                        print(f"  ... and {len(steps) - 3} more steps")

if __name__ == "__main__":
    asyncio.run(main())