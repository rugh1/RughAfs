import pickle
import socket
from kerberos.base.msg import command
from kerberos.base.protocol import send, recv

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 9999
CLIENT_ID = 'client'

command.user = CLIENT_ID
# -- Client Implementation --
print("Client started. Will connect, send one command, and disconnect for each input.")
print("Enter commands like '<command> <data>' or just '<command>' (Ctrl+C to quit):")

while True: # Main loop for user input
    client_socket = None # Ensure socket is reset each iteration
    try:
        # 1. Get input from the user FIRST
        user_input = input("> ").strip()

        if not user_input: # Skip if input is empty
            continue

        # 2. Parse the input
        parts = user_input.split(maxsplit=1)
        cmd_type = parts[0].lower()
        cmd_data = parts[1] if len(parts) > 1 else ""
        cmd_data = cmd_data.split(' ')
    
        if len(cmd_data) == 1:
            cmd_data = cmd_data[0]
        print(cmd_data)
        # 3. Create the command object
        cmd_to_send = command(cmd=cmd_type, data=cmd_data)

        # 4. Create socket and connect (inside the loop)
        # Using 'with' ensures the socket is closed automatically
        print(f"Connecting to {SERVER_HOST}:{SERVER_PORT}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            # Set a timeout for connection attempt (optional, but good practice)
            # client_socket.settimeout(5) # 5 seconds

            client_socket.connect((SERVER_HOST, SERVER_PORT))
            print("Connected. Sending command...")

            # 5. Serialize and send the command
            send(client_socket, cmd_to_send)
            print(f"Sent: {cmd_to_send}")

            # Optional: Receive a response from the server if expected
            # try:
            #    response = client_socket.recv(4096) # Adjust buffer size as needed
            #    print(f"Server response: {response.decode()}") # Assuming text response
            # except socket.timeout:
            #    print("No response received within timeout.")
            # except Exception as e:
            #    print(f"Error receiving response: {e}")


        # 6. Disconnect (handled automatically by 'with' statement exiting)
        print("Disconnected.")
        # time.sleep(0.1) # Optional: small delay if needed


    except (EOFError, KeyboardInterrupt):
        print("\nExiting client...")
        break # Exit the main while loop
    except socket.error as e:
        # Handle errors during connect/send for THIS iteration
        print(f"Socket Error for this command: {e}. Try again.")
        # No need to close socket here if 'with' statement was used or if connect failed
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # Depending on the error, you might want to break or continue
        print("Exiting due to unexpected error.")
        break # Exit loop on other errors

print("Client shut down.")


