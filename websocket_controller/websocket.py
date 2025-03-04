import asyncio
import websockets
import json
import ssl
import math

def map_range(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min
speed = 100
# Store connected clients
connected_clients = set()

async def handle_connection(websocket):
    # Register new client
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            print(f"Received message: {message}")
            try:
                data = json.loads(message)
                command = data.get('command', '')  # Fixed 'commands' to 'command' for consistency
                if '{"command":"joystick"' in message:
                    x = message[message.find("x")+3:]
                    x = x[:x.find(",")]
                    x = int(x)
                    y = message[message.find('"y"')+4:]
                    y = y[:y.find("}")]
                    y = int(y)
                    #print(x,y)
                    if y > 0:
                        motorSpeed = (math.log(abs(y),100)) * 100
                    elif y < 0:
                        motorSpeed = -(math.log(abs(y),100)) * 100
                    else:
                        motorSpeed = 0
                    if x > 0:
                        horicontalMotorDiff = (math.log(abs(x),100)) * speed
                    elif x < 0:
                        horicontalMotorDiff = -(math.log(abs(x),100)) * speed
                    else:
                        horicontalMotorDiff = 0
                    #print(motorSpeed,horicontalMotorDiff)

                    print("{:03d}, {:03d}".format(int(motorSpeed+horicontalMotorDiff),int(motorSpeed-horicontalMotorDiff)))
                # Process commands
                response = {'status': 'success', 'message': f'Received command: {command}'}
                
                if command == 'ping':
                    response['message'] = 'pong'
                elif command == 'status':
                    response['message'] = f'Active clients: {len(connected_clients)}'
                else:
                    response['message'] = f'Unknown command: {command}'
                
                # Send response back to client
                await websocket.send(json.dumps(response))
                
                # Optional: Uncomment to enable broadcasting
                # await broadcast(json.dumps({'broadcast': f'Command received: {command}'}))

            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    'status': 'error',
                    'message': 'Invalid JSON format'
                }))
    except websockets.ConnectionClosed:
        print("Client connection closed")
    finally:
        # Unregister client
        connected_clients.remove(websocket)
        print(f"Client disconnected. Active clients: {len(connected_clients)}")

async def broadcast(message):
    # Send message to all connected clients
    if connected_clients:
        await asyncio.gather(
            *[client.send(message) for client in connected_clients]
        )

async def main():
    # Configure SSL context for WSS
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    try:
        ssl_context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")
    except FileNotFoundError:
        print("Error: Certificate files (cert.pem and key.pem) not found!")
        return
    except Exception as e:
        print(f"Error loading SSL certificates: {e}")
        return

    # Start WebSocket server with SSL
    async with websockets.serve(
        handle_connection,
        "0.0.0.0",  # Bind to all interfaces
        8765,       # Port number
        ssl=ssl_context
    ):
        print("Secure WebSocket server started on wss://0.0.0.0:8765")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())