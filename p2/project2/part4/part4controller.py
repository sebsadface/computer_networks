# Part 4 of UWCSE's Mininet-SDN project
#
# based on Lab Final from UCSC's Networking Class
# which is based on of_tutorial by James McCauley

from pox.lib.packet import ipv4, arp, ethernet
from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import IPAddr, EthAddr

log = core.getLogger()

# Convenience mappings of hostnames to ips
IPS = {
    "h10": "10.0.1.10",
    "h20": "10.0.2.20",
    "h30": "10.0.3.30",
    "serv1": "10.0.4.10",
    "hnotrust": "172.16.10.100",
}

# Convenience mappings of hostnames to subnets
SUBNETS = {
    "h10": "10.0.1.0/24",
    "h20": "10.0.2.0/24",
    "h30": "10.0.3.0/24",
    "serv1": "10.0.4.0/24",
    "hnotrust": "172.16.10.0/24",
}


class Part4Controller(object):
    """
    A Connection object for that switch is passed to the __init__ function.
    """

    def __init__(self, connection):
        print(connection.dpid)
        # Keep track of the connection to the switch so that we can
        # send it messages!
        self.connection = connection

        # This binds our PacketIn event listener
        connection.addListeners(self)
        # use the dpid to figure out what switch is being created
        if connection.dpid == 1:
            self.s1_setup()
        elif connection.dpid == 2:
            self.s2_setup()
        elif connection.dpid == 3:
            self.s3_setup()
        elif connection.dpid == 21:
            self.cores21_setup()
        elif connection.dpid == 31:
            self.dcs31_setup()
        else:
            print("UNKNOWN SWITCH")
            exit(1)

    
    def s1_setup(self):
        # Flood all traffic on this switch
        msg = of.ofp_flow_mod()
        msg.priority = 0
        msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
        self.connection.send(msg)
    
    def s2_setup(self):
        # Flood all traffic on this switch
        msg = of.ofp_flow_mod()
        msg.priority = 0
        msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
        self.connection.send(msg)
    
    def s3_setup(self):
        # Flood all traffic on this switch
        msg = of.ofp_flow_mod()
        msg.priority = 0
        msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
        self.connection.send(msg)
    
    def cores21_setup(self):
        # Block all ICMP traffic from hnotrust1 to h10, h20, h30, or serv1
        for dest_host in ['h10', 'h20', 'h30', 'serv1']:
            msg = of.ofp_flow_mod()
            msg.match.dl_type = 0x0800  # IP type
            msg.match.nw_proto = ipv4.ICMP_PROTOCOL
            msg.match.nw_src = IPAddr(IPS['hnotrust'])
            msg.match.nw_dst = IPAddr(IPS[dest_host])
            msg.priority = 2
            # No action means drop
            self.connection.send(msg)

        # Block all IP traffic from hnotrust1 to serv1
        msg = of.ofp_flow_mod()
        msg.match.dl_type = 0x0800
        msg.match.nw_src = IPAddr(IPS['hnotrust'])
        msg.match.nw_dst = IPAddr(IPS['serv1'])
        msg.priority = 2
        # No action means drop
        self.connection.send(msg)

        # Routing rules for different subnets
        # Example routing rule for traffic to h10's subnet
        msg = of.ofp_flow_mod()
        msg.match.dl_type = 0x0800
        msg.match.nw_dst = IPAddr("10.0.1.0")  
        msg.actions.append(of.ofp_action_output(port=1)) 
        msg.priority = 1
        self.connection.send(msg)

        # Routing rule for traffic to h20's subnet
        msg = of.ofp_flow_mod()
        msg.match.dl_type = 0x0800
        msg.match.nw_dst = IPAddr("10.0.2.0")  
        msg.actions.append(of.ofp_action_output(port=2))
        msg.priority = 1
        self.connection.send(msg)

        # Routing rule for traffic to h30's subnet
        msg = of.ofp_flow_mod()
        msg.match.dl_type = 0x0800
        msg.match.nw_dst = IPAddr("10.0.3.0")  
        msg.actions.append(of.ofp_action_output(port=3)) 
        msg.priority = 1
        self.connection.send(msg)

        # Routing rule for traffic to serv1's subnet
        msg = of.ofp_flow_mod()
        msg.match.dl_type = 0x0800
        msg.match.nw_dst = IPAddr("10.0.4.0") 
        msg.actions.append(of.ofp_action_output(port=4))
        msg.priority = 1
        self.connection.send(msg)
    
    def dcs31_setup(self):
        # Flood all traffic on this switch
        msg = of.ofp_flow_mod()
        msg.priority = 0
        msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
        self.connection.send(msg)
    

    # used in part 4 to handle individual ARP packets
    # not needed for part 3 (USE RULES!)
    # causes the switch to output packet_in on out_port
    def resend_packet(self, packet_in, out_port):
        msg = of.ofp_packet_out()
        msg.data = packet_in
        action = of.ofp_action_output(port=out_port)
        msg.actions.append(action)
        self.connection.send(msg)

    def _handle_PacketIn(self, event):
        """
        Handles incoming packets that are not managed by the switch's rules.
        This method processes ARP requests and dynamically routes IP packets.
        """
        packet = event.parsed  # Parse the packet data.
        if not packet.parsed:
            log.warning("Ignoring incomplete packet")
            return

        packet_in = event.ofp  # The actual OpenFlow packet in message.
        port_in = event.port  # Port from which the packet originated.
        cores21_Addr = EthAddr("01:02:03:04:05:06")  # Arbitrary MAC address for cores21.

        packetVal = packet.next
        if isinstance(packetVal, arp) and packetVal.opcode == arp.REQUEST:
            # Respond to ARP requests.
            arp_reply = self.create_arp_reply(packetVal, cores21_Addr)
            ether_reply = self.wrap_in_ethernet(arp_reply, packetVal, cores21_Addr)
            self.send_arp_reply(ether_reply, port_in)
            self.create_dynamic_flow_mod(packetVal, port_in)

    def create_arp_reply(self, arp_request, src_mac):
        """
        Creates an ARP reply packet in response to an ARP request.
        """
        reply = arp()
        reply.hwsrc = src_mac
        reply.hwdst = arp_request.hwsrc
        reply.opcode = arp.REPLY
        reply.protosrc = arp_request.protodst
        reply.protodst = arp_request.protosrc
        return reply

    def wrap_in_ethernet(self, arp_reply, arp_request, src_mac):
        """
        Wraps an ARP reply in an Ethernet frame.
        """
        ether = ethernet()
        ether.type = ethernet.ARP_TYPE
        ether.dst = arp_request.hwsrc
        ether.src = src_mac
        ether.set_payload(arp_reply)
        return ether

    def send_arp_reply(self, ether_reply, port):
        """
        Sends an ARP reply packet.
        """
        self.resend_packet(ether_reply, port)

    def create_dynamic_flow_mod(self, arp_request, port):
        """
        Creates a dynamic flow modification rule based on an ARP request.
        """
        fm = of.ofp_flow_mod()
        fm.match.dl_type = 0x0800
        fm.priority = 1  # May need adjustment
        fm.match.nw_dst = arp_request.protosrc
        fm.actions.append(of.ofp_action_dl_addr.set_dst(arp_request.hwsrc))
        fm.actions.append(of.ofp_action_output(port=port))
        self.connection.send(fm)

        


def launch():
    """
    Starts the component
    """

    def start_switch(event):
        log.debug("Controlling %s" % (event.connection,))
        Part4Controller(event.connection)

    core.openflow.addListenerByName("ConnectionUp", start_switch)
