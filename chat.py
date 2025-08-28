import socket
import json
import os
import threading
import rsa

public_key, private_key = rsa.newkeys(1024)
public_partner = None

CONTACTS_FILE = "contacts.json"
OWN_FILE = "own.json"
fallback_port = 9999
name = None
port = None
target_ddns = None
client = None
MAX_CHUNK = 115

# --- Carica contatti ---
if os.path.exists(CONTACTS_FILE):
    with open(CONTACTS_FILE, "r") as f:
        contacts = json.load(f)
else:
    contacts = {}

# --- Carica DDNS e porta propri ---
if os.path.exists(OWN_FILE):
    with open(OWN_FILE, "r") as f:
        own_data = json.load(f)
else:
    own_data = {"ddns": "", "port": fallback_port}

def save_contacts():
    with open(CONTACTS_FILE, "w") as f:
        json.dump(contacts, f, indent=4)

def save_own():
    with open(OWN_FILE, "w") as f:
        json.dump(own_data, f, indent=4)

def open_connection():
    global name, port, target_ddns, client, public_partner
    choice = input("Host (0) or Connect (1): ")

    if choice == "0":
        # HOST: scegli DDNS
        while True:
            if own_data.get("ddns"):
                print("Where do you want to host?")
                print("0 - Saved DDNS")
                print("00 - Show saved DDNS")
                print("1 - Change DDNS")
                sel = input("Enter number: ")
                if sel == '0':
                    host_ddns = own_data["ddns"]
                    break
                elif sel == '00':
                    while True:
                        print(f"Currently saved DDNS: {own_data["ddns"]}")
                        break
                elif sel == '1':
                    host_ddns = input("Enter your DDNS hostname: ")
                    own_data["ddns"] = host_ddns
                    save_own()
                    break
            else:
                host_ddns = input("Enter your DDNS hostname: ")
                own_data["ddns"] = host_ddns
                save_own()

        # HOST: scegli porta
        print(f"Current port: {own_data.get('port', fallback_port)}")
        change_port = input("Do you want to change the port? (y/n): ").lower()
        if change_port == "y":
            port = int(input("Enter new port: "))
            own_data["port"] = port
            save_own()
        else:
            port = own_data.get("port", fallback_port)

        # Avvia il server
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("0.0.0.0", port))
        server.listen()
        print(f"Hosting on {host_ddns}:{port}. Waiting for connection...")
        client, addr = server.accept()
        print(f"Connected by {addr}")
        client.send(public_key.save_pkcs1("PEM"))
        print(f"Public key sent")
        public_partner = rsa.PublicKey.load_pkcs1(client.recv(1024))
        print('Public key received')
        return True

    elif choice == "1":
        # Selezione contatti
        while True:
            print("\nSelect who you want to connect to:")
            print("0 - New connection")
            print("00 - Delete contact")
            for i, name in enumerate(contacts.keys(), start=1):
                print(f"{i} - {name}")

            sel = input("\nEnter number: ").strip()

            if sel == "0":
                # Nuova connessione
                name = input("Enter name: ")
                ddns = input("Enter DDNS hostname: ").strip()
                contacts[name] = ddns
                save_contacts()
                target_ddns = ddns
                port = own_data.get("port", fallback_port)
                break
            elif sel == "00":
                while True:
                    print("\nSelect the contact you want to delete:")
                    print("0 - Go back")
                    for i, name in enumerate(contacts.keys(), start=1):
                        print(f"{i} - {name}")

                    sel_del = input("\nEnter number: ").strip()

                    if sel_del == "0":
                        # Torna al menu principale di scelta contatto
                        break
                    else:
                        try:
                            sel_del = int(sel_del)
                            if 1 <= sel_del <= len(contacts):
                                name_to_delete = list(contacts.keys())[sel_del - 1]
                                confirm = input(
                                    f'Confirm deletion of "{name_to_delete}" by inputting "CONFIRM1234CONFIRM". '
                                    "This cannot be reversed.\n> "
                                ).strip()
                                if confirm == "CONFIRM1234CONFIRM":
                                    del contacts[name_to_delete]
                                    save_contacts()
                                    print(f'Contact "{name_to_delete}" deleted successfully!')
                                else:
                                    print("Confirmation failed. Contact not deleted.")
                            else:
                                print("Invalid selection.")
                        except ValueError:
                            print("Invalid input, enter a number.")

            else:
                sel = int(sel)
                # Selezione contatto esistente
                name = list(contacts.keys())[sel - 1]
                target_ddns = contacts[name]
                port = own_data.get("port", fallback_port)
                break

        # CLIENT: scegli porta
        print(f"Current port: {own_data.get('port', fallback_port)}")
        change_port = input("Do you want to change the port? (y/n): ").lower()
        if change_port == "y":
            port = int(input("Enter new port: "))
            own_data["port"] = port
            save_own()
        else:
            port = own_data.get("port", fallback_port)

        # Connessione al DDNS scelto
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"Connecting to {target_ddns}:{port}...")
        client.connect((target_ddns, port))
        print("Connected!")
        public_partner = rsa.PublicKey.load_pkcs1(client.recv(1024))
        print('Public key received')
        client.send(public_key.save_pkcs1("PEM"))
        print(f"Public key sent")
        return True


def sending_messages(c=None):
    while True:
        message = input('')
        message_bytes = message.encode()

        # Dividi in chunk da MAX_CHUNK
        chunks = [message_bytes[i:i + MAX_CHUNK] for i in range(0, len(message_bytes), MAX_CHUNK)]

        # Invia ogni chunk
        for chunk in chunks:
            c.send(rsa.encrypt(chunk, public_partner))

        # Stampa il messaggio nella chat
        print("\033[F\033[K", end='')  # cancella la riga precedente
        print(f"You: {message}")

def receiving_messages(c):
    while True:
        print(f"{name}: {rsa.decrypt(c.recv(1024), private_key).decode()}")

def main():
    running = True
    if open_connection():
        while running:
            threading.Thread(target=sending_messages, args=(client,)).start()
            threading.Thread(target=receiving_messages, args=(client,)).start()




if __name__=='__main__':
    main()