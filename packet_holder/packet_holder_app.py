import PySimpleGUI as sg
import packet_holder

# Define the GUI layout
layout = [
    [sg.Text('Proxy  IP Address:', size=(14, 1)), sg.InputText('localhost', key='client_ip'), sg.Text('Port:', size=(4, 1)), sg.InputText('16000', key='client_port',size=(10, 1))],
    [sg.Text('Server IP Address:', size=(14, 1)), sg.InputText('localhost', key='server_ip'), sg.Text('Port:', size=(4, 1)), sg.InputText('6000', key='server_port',size=(10, 1))],
    [sg.Text('Keyword:', size=(14, 1)), sg.InputText('333', key='keyword', enable_events=True), sg.Checkbox('Enable packet holding', key='enable_packet_holding', default=False, enable_events=True)],
    [sg.Button('Start'), sg.Button('Stop'), sg.Button('Send Pending Packets')],
    [sg.Text('Log:', size=(14, 1)), sg.Checkbox('Outputs only held packets or those sent after being released from hold.', key='log_only_pending_packets', default=False, enable_events=True)],
    [sg.Output(size=(160, 32), key='output',font='System 10')]
]

# Create the window
window = sg.Window('Packet Holder [Not Running]', layout)

# Initialize packet holder
packet_holder = packet_holder.PacketHolder()

# Event loop
while True:
    event, values = window.read()
    if event == sg.WINDOW_CLOSED:
        break
    elif event == 'Start':
        packet_holder_ip = values['client_ip']
        packet_holder_port = int(values['client_port'])
        server_ip = values['server_ip']
        server_port = int(values['server_port'])
        keyword = values['keyword']
        
        # Start packet holder with the provided values
        packet_holder.register_pending_keyword(keyword)
        packet_holder.start(packet_holder_ip, packet_holder_port, server_ip, server_port)
        window.set_title('Packet Holder [Running]')
    elif event == 'Stop':
        # Stop packet holder
        packet_holder.stop()
        window.set_title('Packet Holder [Not Running]')
    elif event == 'Send Pending Packets':
        # Send pending packets
        packet_holder.send_pending_packets()
    elif event == 'keyword':
        # Register pending keyword
        packet_holder.clear_pending_keywords()
        if values['keyword']:
            packet_holder.register_pending_keyword(values['keyword'])
    elif event == 'log_only_pending_packets':
        # Set output only pending packets
        packet_holder.set_output_only_pending_packets(values['log_only_pending_packets'])
    elif event == 'enable_packet_holding':
        # Set packet hold status
        packet_holder.set_packet_hold_status(values['enable_packet_holding'])

# Close the window
window.close()