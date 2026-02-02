"""
Simple WebSocket test script.

Usage:
1. Start your server: uvicorn app.main:app --reload
2. Get a token by logging in via /docs
3. Create a room and note the room_code
4. Run this script with your token and room_code
"""

import asyncio
import json

import websockets


async def test_websocket():
    # REPLACE THESE VALUES
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzcwMDUwODM2fQ.2SC4twqHAwWFz-0vJPYvx4Fpj88z8ae5E4bpVql7TIg"
    room_code = "bLzjs2"

    uri = f"ws://localhost:8000/ws/{room_code}?token={token}"

    print(f"Connecting to {uri[:50]}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")

            # Listen for the join notification (broadcast to self)
            response = await websocket.recv()
            print(f"Received: {response}")

            # Send a chat message
            message = {
                "event": "chat_message",
                "content": "Hello from Python test script!",
            }
            await websocket.send(json.dumps(message))
            print(f"Sent: {message}")

            # Receive the broadcast of our message
            response = await websocket.recv()
            print(f"Received: {response}")

            # Keep connection open and listen for more messages
            print("\nListening for messages (Ctrl+C to exit)...")
            while True:
                response = await websocket.recv()
                print(f"Received: {response}")

    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed: {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_websocket())
