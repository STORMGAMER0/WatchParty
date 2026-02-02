

import asyncio
import json

import websockets


async def test_websocket():
    # REPLACE THESE VALUES
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzcwMDU5Mjk4fQ.Ae7nGiR-4-lHKGNahQ_xK4oEFoOuhugUU2HmWFZMPFw"
    room_code = "bLzjs2"

    uri = f"ws://localhost:8000/ws/{room_code}?token={token}"

    print(f"Connecting to {uri[:50]}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")


            response = await websocket.recv()
            print(f"Received: {response}")


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
