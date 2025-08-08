import tkinter as tk
from tkinter import scrolledtext, messagebox
import time
import threading

# --- Packet Representation ---
class Packet:
    """
    Represents a data packet moving through the OSI layers.
    It stores the original data and headers/footers added by each layer.
    """
    def __init__(self, data):
        self.original_data = data
        self.application_data = data
        self.presentation_header = ""
        self.session_header = ""
        self.transport_header = ""
        self.network_header = ""
        self.data_link_header = ""
        self.data_link_footer = ""
        self.physical_bits = "" # Represents the raw bits on the physical medium
        self.is_ack = False # Flag to indicate if this packet is an acknowledgment

    def __str__(self):
        # A simplified string representation for logging
        if self.is_ack:
            return f"ACK Packet (for: '{self.original_data[:15]}...')"
        return f"Data Packet (Data: '{self.original_data[:15]}...', App: '{self.application_data[:15]}...', " \
               f"Pres: '{self.presentation_header[:10]}...', Sess: '{self.session_header[:10]}...', " \
               f"Trans: '{self.transport_header[:10]}...', Net: '{self.network_header[:10]}...', " \
               f"DL Hdr: '{self.data_link_header[:10]}...', DL Ftr: '{self.data_link_footer[:10]}...')"

    def get_current_payload(self):
        """
        Returns the current representation of the payload as it would appear
        at a specific layer. This is a conceptual representation for the GUI.
        """
        payload = self.application_data
        if self.presentation_header:
            payload = self.presentation_header + payload
        if self.session_header:
            payload = self.session_header + payload
        if self.transport_header:
            payload = self.transport_header + payload
        if self.network_header:
            payload = self.network_header + payload
        if self.data_link_header:
            payload = self.data_link_header + payload
        if self.data_link_footer:
            payload = payload + self.data_link_footer
        return payload

# --- GUI Application ---
class OSISimulator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OSI Model Simulation")
        self.geometry("1200x800")
        self.configure(bg="#f0f0f0")

        self.create_widgets()
        self.reset_gui_labels() # Initialize labels with default text

    def create_widgets(self):
        # --- Styles ---
        self.layer_font = ("Inter", 10, "bold")
        self.data_font = ("Inter", 9)
        self.header_font = ("Inter", 8, "italic")
        self.log_font = ("Inter", 9)
        self.button_font = ("Inter", 10, "bold")

        # --- Main Frames ---
        self.top_frame = tk.Frame(self, bg="#e0e0e0", bd=2, relief="raised", padx=10, pady=10)
        self.top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.middle_frame = tk.Frame(self, bg="#f8f8f8", bd=2, relief="groove", padx=10, pady=10)
        self.middle_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.bottom_frame = tk.Frame(self, bg="#e0e0e0", bd=2, relief="raised", padx=10, pady=10)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        # --- Top Frame: Input and Control ---
        tk.Label(self.top_frame, text="Enter Data to Send:", font=("Inter", 12, "bold"), bg="#e0e0e0").pack(side=tk.LEFT, padx=5)
        self.data_input = tk.Entry(self.top_frame, width=60, font=("Inter", 10), bd=2, relief="sunken")
        self.data_input.insert(0, "Hello OSI World!")
        self.data_input.pack(side=tk.LEFT, padx=10, pady=5)

        self.send_button = tk.Button(self.top_frame, text="Simulate Send", command=self.start_simulation_thread,
                                     font=self.button_font, bg="#4CAF50", fg="white",
                                     activebackground="#45a049", activeforeground="white",
                                     bd=3, relief="raised", padx=10, pady=5, cursor="hand2")
        self.send_button.pack(side=tk.LEFT, padx=10)

        self.reset_button = tk.Button(self.top_frame, text="Reset", command=self.reset_simulation,
                                      font=self.button_font, bg="#f44336", fg="white",
                                      activebackground="#da190b", activeforeground="white",
                                      bd=3, relief="raised", padx=10, pady=5, cursor="hand2")
        self.reset_button.pack(side=tk.LEFT, padx=10)

        # --- Middle Frame: Sender, Network, Receiver ---
        self.sender_frame = tk.LabelFrame(self.middle_frame, text="Sender (Encapsulation)", font=("Inter", 12, "bold"),
                                          bg="#f8f8f8", bd=2, relief="groove", padx=10, pady=10)
        self.sender_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.network_frame = tk.LabelFrame(self.middle_frame, text="Network Medium", font=("Inter", 12, "bold"),
                                           bg="#f0f0f0", bd=2, relief="groove", padx=10, pady=10)
        self.network_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.receiver_frame = tk.LabelFrame(self.middle_frame, text="Receiver (Decapsulation)", font=("Inter", 12, "bold"),
                                            bg="#f8f8f8", bd=2, relief="groove", padx=10, pady=10)
        self.receiver_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.create_layer_display(self.sender_frame, "sender")
        self.create_network_display(self.network_frame)
        self.create_layer_display(self.receiver_frame, "receiver")

        # --- Bottom Frame: Log Console ---
        tk.Label(self.bottom_frame, text="Simulation Log:", font=("Inter", 12, "bold"), bg="#e0e0e0").pack(anchor=tk.NW, pady=5)
        self.log_console = scrolledtext.ScrolledText(self.bottom_frame, width=120, height=10, font=self.log_font,
                                                     bg="#ffffff", fg="#333333", bd=2, relief="sunken", wrap=tk.WORD)
        self.log_console.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_console.config(state=tk.DISABLED) # Make it read-only

    def create_layer_display(self, parent_frame, side):
        """
        Creates the display for each OSI layer within a sender or receiver frame.
        """
        layers = ["Application", "Presentation", "Session", "Transport", "Network", "Data Link", "Physical"]
        self.labels = getattr(self, 'labels', {}) # Initialize if not exists
        self.header_labels = getattr(self, 'header_labels', {})
        self.data_labels = getattr(self, 'data_labels', {})

        for i, layer_name in enumerate(layers):
            frame = tk.Frame(parent_frame, bg="#f0f0f0", bd=1, relief="solid", padx=5, pady=5)
            frame.pack(fill=tk.X, pady=2)

            tk.Label(frame, text=f"{i+7-len(layers)+1}. {layer_name} Layer", font=self.layer_font, bg="#f0f0f0", fg="#0056b3").pack(anchor=tk.W)

            header_label = tk.Label(frame, text="Header: N/A", font=self.header_font, bg="#f0f0f0", fg="#555555", anchor=tk.W)
            header_label.pack(fill=tk.X)
            self.header_labels[f"{side}_{layer_name.replace(' ', '_').lower()}"] = header_label

            data_label = tk.Label(frame, text="Data: N/A", font=self.data_font, bg="#f0f0f0", fg="#333333", anchor=tk.W)
            data_label.pack(fill=tk.X)
            self.data_labels[f"{side}_{layer_name.replace(' ', '_').lower()}"] = data_label

            # Store the frame itself to change background color during simulation
            self.labels[f"{side}_{layer_name.replace(' ', '_').lower()}_frame"] = frame

    def create_network_display(self, parent_frame):
        """
        Creates the display for the network medium.
        """
        tk.Label(parent_frame, text="Packet in Transit:", font=self.layer_font, bg="#f0f0f0", fg="#0056b3").pack(pady=10)
        self.network_packet_label = tk.Label(parent_frame, text="No packet in transit.", font=self.data_font,
                                             bg="#ffffff", fg="#333333", wraplength=300, bd=2, relief="sunken", padx=5, pady=5)
        self.network_packet_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.network_status_label = tk.Label(parent_frame, text="Status: Idle", font=self.header_font,
                                             bg="#f0f0f0", fg="#555555")
        self.network_status_label.pack(pady=5)

    def log_message(self, message, color="black"):
        """Appends a message to the log console."""
        self.log_console.config(state=tk.NORMAL)
        self.log_console.insert(tk.END, message + "\n", color)
        self.log_console.see(tk.END) # Scroll to the end
        self.log_console.config(state=tk.DISABLED)

    def update_layer_display(self, side, layer_name, header_info, data_info, highlight=False):
        """Updates the labels for a specific layer."""
        key_prefix = f"{side}_{layer_name.replace(' ', '_').lower()}"
        self.header_labels[key_prefix].config(text=f"Header: {header_info}")
        self.data_labels[key_prefix].config(text=f"Data: {data_info}")
        if highlight:
            self.labels[f"{key_prefix}_frame"].config(bg="#d4edda") # Light green for active
        else:
            self.labels[f"{key_prefix}_frame"].config(bg="#f0f0f0") # Default color

        self.update_idletasks() # Force GUI update

    def reset_gui_labels(self):
        """Resets all GUI labels to their initial state."""
        layers = ["Application", "Presentation", "Session", "Transport", "Network", "Data Link", "Physical"]
        for side in ["sender", "receiver"]:
            for layer_name in layers:
                self.update_layer_display(side, layer_name, "N/A", "N/A", highlight=False)
        self.network_packet_label.config(text="No packet in transit.")
        self.network_status_label.config(text="Status: Idle")
        self.log_console.config(state=tk.NORMAL)
        self.log_console.delete(1.0, tk.END)
        self.log_console.config(state=tk.DISABLED)
        self.send_button.config(state=tk.NORMAL)
        self.data_input.config(state=tk.NORMAL)

    def simulate_delay(self, seconds=0.5):
        """Simulates network or processing delay."""
        time.sleep(seconds)

    def start_simulation_thread(self):
        """Starts the simulation in a separate thread to keep GUI responsive."""
        self.send_button.config(state=tk.DISABLED)
        self.data_input.config(state=tk.DISABLED)
        self.reset_gui_labels() # Clear previous run
        threading.Thread(target=self.run_simulation).start()

    def run_simulation(self):
        """Main simulation logic."""
        data_to_send = self.data_input.get()
        if not data_to_send:
            messagebox.showwarning("Input Error", "Please enter some data to send.")
            self.send_button.config(state=tk.NORMAL)
            self.data_input.config(state=tk.NORMAL)
            return

        self.log_message(f"--- Starting Simulation for: '{data_to_send}' ---", "blue")
        initial_packet = Packet(data_to_send)
        self.log_message("Sender: Initializing data packet.", "green")

        # --- Sender Side (Encapsulation) ---
        self.log_message("\n--- Sender: Encapsulation Process ---", "darkblue")
        self.simulate_sender_layers(initial_packet)

        # --- Network Transfer ---
        self.log_message("\n--- Network: Transferring Packet ---", "darkgreen")
        self.network_packet_label.config(text=f"Packet in transit: {initial_packet.physical_bits}", bg="#e6ffe6")
        self.network_status_label.config(text="Status: Transmitting...")
        self.simulate_delay(1.5) # Simulate network latency

        # --- Receiver Side (Decapsulation) ---
        self.log_message("\n--- Receiver: Decapsulation Process ---", "darkblue")
        received_packet = self.simulate_receiver_layers(initial_packet)

        if received_packet and not received_packet.is_ack:
            self.log_message(f"\n--- Receiver: Data Received! Original Data: '{received_packet.original_data}' ---", "green")
            self.log_message("Receiver: Sending Acknowledgment (ACK) back to sender...", "purple")
            self.send_acknowledgment(received_packet.original_data)
        else:
            self.log_message("\n--- Simulation Finished (No ACK needed or already ACK) ---", "blue")

        self.log_message("\n--- Simulation Complete ---", "blue")
        self.send_button.config(state=tk.NORMAL)
        self.data_input.config(state=tk.NORMAL)
        self.network_packet_label.config(bg="#ffffff") # Reset network background

    def simulate_sender_layers(self, packet):
        # Application Layer (Layer 7)
        self.update_layer_display("sender", "Application", "N/A", packet.application_data, True)
        self.log_message(f"Sender (L7 Application): User data '{packet.application_data}' generated.", "green")
        self.simulate_delay()
        self.update_layer_display("sender", "Application", "N/A", packet.application_data, False)

        # Presentation Layer (Layer 6)
        packet.presentation_header = "PRES_HDR_FORMAT[UTF-8]"
        self.update_layer_display("sender", "Presentation", packet.presentation_header, packet.get_current_payload(), True)
        self.log_message(f"Sender (L6 Presentation): Encoded data (e.g., UTF-8). Added header: {packet.presentation_header}", "green")
        self.simulate_delay()
        self.update_layer_display("sender", "Presentation", packet.presentation_header, packet.get_current_payload(), False)

        # Session Layer (Layer 5)
        packet.session_header = "SESS_HDR_ID[12345]"
        self.update_layer_display("sender", "Session", packet.session_header, packet.get_current_payload(), True)
        self.log_message(f"Sender (L5 Session): Established session. Added header: {packet.session_header}", "green")
        self.simulate_delay()
        self.update_layer_display("sender", "Session", packet.session_header, packet.get_current_payload(), False)

        # Transport Layer (Layer 4)
        packet.transport_header = "TRANS_HDR_PORT[8080]_SEQ[1]"
        self.update_layer_display("sender", "Transport", packet.transport_header, packet.get_current_payload(), True)
        self.log_message(f"Sender (L4 Transport): Segmented data, added port and sequence number. Added header: {packet.transport_header}", "green")
        self.simulate_delay()
        self.update_layer_display("sender", "Transport", packet.transport_header, packet.get_current_payload(), False)

        # Network Layer (Layer 3)
        packet.network_header = "NET_HDR_SRC[192.168.1.1]_DST[192.168.1.100]"
        self.update_layer_display("sender", "Network", packet.network_header, packet.get_current_payload(), True)
        self.log_message(f"Sender (L3 Network): Added source/destination IP addresses. Added header: {packet.network_header}", "green")
        self.simulate_delay()
        self.update_layer_display("sender", "Network", packet.network_header, packet.get_current_payload(), False)

        # Data Link Layer (Layer 2)
        packet.data_link_header = "DL_HDR_MAC_SRC[AA:BB:CC]_MAC_DST[DD:EE:FF]"
        packet.data_link_footer = "_DL_FTR_CRC[0xABCD]"
        self.update_layer_display("sender", "Data Link", packet.data_link_header, packet.get_current_payload(), True)
        self.log_message(f"Sender (L2 Data Link): Added MAC addresses and CRC. Added header: {packet.data_link_header}, Footer: {packet.data_link_footer}", "green")
        self.simulate_delay()
        self.update_layer_display("sender", "Data Link", packet.data_link_header, packet.get_current_payload(), False)

        # Physical Layer (Layer 1)
        packet.physical_bits = "01010101" + packet.get_current_payload().encode('utf-8').hex() + "10101010" # Simplified bit stream
        self.update_layer_display("sender", "Physical", "N/A", f"Raw Bits: {packet.physical_bits[:30]}...", True)
        self.log_message(f"Sender (L1 Physical): Converted to raw bits for transmission. Bits: {packet.physical_bits[:30]}...", "green")
        self.simulate_delay()
        self.update_layer_display("sender", "Physical", "N/A", f"Raw Bits: {packet.physical_bits[:30]}...", False)

    def simulate_receiver_layers(self, packet):
        # Physical Layer (Layer 1)
        self.update_layer_display("receiver", "Physical", "N/A", f"Raw Bits: {packet.physical_bits[:30]}...", True)
        self.log_message(f"Receiver (L1 Physical): Received raw bits. Bits: {packet.physical_bits[:30]}...", "blue")
        self.simulate_delay()
        self.update_layer_display("receiver", "Physical", "N/A", f"Raw Bits: {packet.physical_bits[:30]}...", False)

        # Data Link Layer (Layer 2)
        # Simulate removal of Data Link header and footer
        payload_after_dl = packet.get_current_payload()
        if packet.data_link_header:
            payload_after_dl = payload_after_dl.replace(packet.data_link_header, "", 1)
        if packet.data_link_footer:
            payload_after_dl = payload_after_dl.replace(packet.data_link_footer, "", 1)
        self.update_layer_display("receiver", "Data Link", packet.data_link_header, payload_after_dl, True)
        self.log_message(f"Receiver (L2 Data Link): Verified CRC, removed header/footer. Payload: {payload_after_dl[:30]}...", "blue")
        self.simulate_delay()
        self.update_layer_display("receiver", "Data Link", packet.data_link_header, payload_after_dl, False)
        packet.data_link_header = ""
        packet.data_link_footer = ""

        # Network Layer (Layer 3)
        # Simulate removal of Network header
        payload_after_net = payload_after_dl
        if packet.network_header:
            payload_after_net = payload_after_net.replace(packet.network_header, "", 1)
        self.update_layer_display("receiver", "Network", packet.network_header, payload_after_net, True)
        self.log_message(f"Receiver (L3 Network): Routed packet, removed IP header. Payload: {payload_after_net[:30]}...", "blue")
        self.simulate_delay()
        self.update_layer_display("receiver", "Network", packet.network_header, payload_after_net, False)
        packet.network_header = ""

        # Transport Layer (Layer 4)
        # Simulate removal of Transport header
        payload_after_trans = payload_after_net
        if packet.transport_header:
            payload_after_trans = payload_after_trans.replace(packet.transport_header, "", 1)
        self.update_layer_display("receiver", "Transport", packet.transport_header, payload_after_trans, True)
        self.log_message(f"Receiver (L4 Transport): Reassembled segments, removed port/sequence. Payload: {payload_after_trans[:30]}...", "blue")
        self.simulate_delay()
        self.update_layer_display("receiver", "Transport", packet.transport_header, payload_after_trans, False)
        packet.transport_header = ""

        # Session Layer (Layer 5)
        # Simulate removal of Session header
        payload_after_sess = payload_after_trans
        if packet.session_header:
            payload_after_sess = payload_after_sess.replace(packet.session_header, "", 1)
        self.update_layer_display("receiver", "Session", packet.session_header, payload_after_sess, True)
        self.log_message(f"Receiver (L5 Session): Managed session, removed header. Payload: {payload_after_sess[:30]}...", "blue")
        self.simulate_delay()
        self.update_layer_display("receiver", "Session", packet.session_header, payload_after_sess, False)
        packet.session_header = ""

        # Presentation Layer (Layer 6)
        # Simulate removal of Presentation header
        payload_after_pres = payload_after_sess
        if packet.presentation_header:
            payload_after_pres = payload_after_pres.replace(packet.presentation_header, "", 1)
        self.update_layer_display("receiver", "Presentation", packet.presentation_header, payload_after_pres, True)
        self.log_message(f"Receiver (L6 Presentation): Decoded data. Payload: {payload_after_pres[:30]}...", "blue")
        self.simulate_delay()
        self.update_layer_display("receiver", "Presentation", packet.presentation_header, payload_after_pres, False)
        packet.presentation_header = ""

        # Application Layer (Layer 7)
        packet.application_data = payload_after_pres # The final data after decapsulation
        self.update_layer_display("receiver", "Application", "N/A", packet.application_data, True)
        self.log_message(f"Receiver (L7 Application): Delivered original data: '{packet.application_data}'", "blue")
        self.simulate_delay()
        self.update_layer_display("receiver", "Application", "N/A", packet.application_data, False)

        return packet

    def send_acknowledgment(self, original_data):
        """Simulates sending an ACK packet back to the sender."""
        ack_packet = Packet(f"ACK for '{original_data}'")
        ack_packet.is_ack = True
        self.log_message(f"\n--- Receiver: Encapsulating ACK Packet ---", "darkblue")

        # Simplified encapsulation for ACK (just enough to get it back)
        ack_packet.transport_header = "TRANS_HDR_ACK_PORT[8080]"
        ack_packet.network_header = "NET_HDR_SRC[192.168.1.100]_DST[192.168.1.1]"
        ack_packet.data_link_header = "DL_HDR_MAC_SRC[DD:EE:FF]_MAC_DST[AA:BB:CC]"
        ack_packet.data_link_footer = "_DL_FTR_ACK_CRC[0xEFGH]"
        ack_packet.physical_bits = "11110000" + ack_packet.get_current_payload().encode('utf-8').hex() + "00001111"

        # Update receiver layers for ACK sending (briefly)
        self.update_layer_display("receiver", "Application", "N/A", ack_packet.original_data, True)
        self.simulate_delay(0.2)
        self.update_layer_display("receiver", "Application", "N/A", ack_packet.original_data, False)

        self.update_layer_display("receiver", "Transport", ack_packet.transport_header, ack_packet.get_current_payload(), True)
        self.simulate_delay(0.2)
        self.update_layer_display("receiver", "Transport", ack_packet.transport_header, ack_packet.get_current_payload(), False)

        self.update_layer_display("receiver", "Network", ack_packet.network_header, ack_packet.get_current_payload(), True)
        self.simulate_delay(0.2)
        self.update_layer_display("receiver", "Network", ack_packet.network_header, ack_packet.get_current_payload(), False)

        self.update_layer_display("receiver", "Data Link", ack_packet.data_link_header, ack_packet.get_current_payload(), True)
        self.simulate_delay(0.2)
        self.update_layer_display("receiver", "Data Link", ack_packet.data_link_header, ack_packet.get_current_payload(), False)

        self.update_layer_display("receiver", "Physical", "N/A", f"Raw Bits: {ack_packet.physical_bits[:30]}...", True)
        self.simulate_delay(0.2)
        self.update_layer_display("receiver", "Physical", "N/A", f"Raw Bits: {ack_packet.physical_bits[:30]}...", False)

        self.log_message(f"\n--- Network: Transferring ACK Packet ---", "darkgreen")
        self.network_packet_label.config(text=f"ACK Packet in transit: {ack_packet.physical_bits}", bg="#e6ffe6")
        self.network_status_label.config(text="Status: Transmitting ACK...")
        self.simulate_delay(1.0) # Simulate network latency for ACK

        self.log_message(f"\n--- Sender: Decapsulating ACK Packet ---", "darkblue")
        self.network_packet_label.config(text="No packet in transit.", bg="#ffffff")
        self.network_status_label.config(text="Status: Idle")

        # Simulate decapsulation of ACK at sender side
        # Physical Layer (Layer 1)
        self.update_layer_display("sender", "Physical", "N/A", f"Raw Bits: {ack_packet.physical_bits[:30]}...", True)
        self.log_message(f"Sender (L1 Physical): Received raw bits for ACK. Bits: {ack_packet.physical_bits[:30]}...", "orange")
        self.simulate_delay(0.2)
        self.update_layer_display("sender", "Physical", "N/A", f"Raw Bits: {ack_packet.physical_bits[:30]}...", False)

        # Data Link Layer (Layer 2)
        self.update_layer_display("sender", "Data Link", ack_packet.data_link_header, ack_packet.get_current_payload(), True)
        self.log_message(f"Sender (L2 Data Link): Processed ACK frame.", "orange")
        self.simulate_delay(0.2)
        self.update_layer_display("sender", "Data Link", ack_packet.data_link_header, ack_packet.get_current_payload(), False)

        # Network Layer (Layer 3)
        self.update_layer_display("sender", "Network", ack_packet.network_header, ack_packet.get_current_payload(), True)
        self.log_message(f"Sender (L3 Network): Processed ACK IP packet.", "orange")
        self.simulate_delay(0.2)
        self.update_layer_display("sender", "Network", ack_packet.network_header, ack_packet.get_current_payload(), False)

        # Transport Layer (Layer 4)
        self.update_layer_display("sender", "Transport", ack_packet.transport_header, ack_packet.get_current_payload(), True)
        self.log_message(f"Sender (L4 Transport): Received ACK for original data. Connection confirmed!", "orange")
        self.simulate_delay(0.2)
        self.update_layer_display("sender", "Transport", ack_packet.transport_header, ack_packet.get_current_payload(), False)

        # Application Layer (Layer 7) - Acknowledgment reaches here conceptually
        self.update_layer_display("sender", "Application", "N/A", f"ACK Received: {ack_packet.original_data}", True)
        self.log_message(f"Sender (L7 Application): Acknowledgment received for: '{original_data}'", "green")
        self.simulate_delay(0.5)
        self.update_layer_display("sender", "Application", "N/A", f"ACK Received: {ack_packet.original_data}", False)


    def reset_simulation(self):
        """Resets the entire simulation to its initial state."""
        self.log_message("\n--- Resetting Simulation ---", "red")
        self.reset_gui_labels()
        self.data_input.delete(0, tk.END)
        self.data_input.insert(0, "Hello OSI World!")
        self.log_message("Simulation has been reset.", "red")

if __name__ == "__main__":
    app = OSISimulator()
    app.mainloop()
