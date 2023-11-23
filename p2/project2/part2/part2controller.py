# Part 2 of UWCSE's Project 3
#
# based on Lab 4 from UCSC's Networking Class
# which is based on of_tutorial by James McCauley

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.ipv4 import ipv4

log = core.getLogger()


class Firewall(object):
    """
    A Firewall object is created for each switch that connects.
    A Connection object for that switch is passed to the __init__ function.
    """

    def __init__(self, connection):
        # Keep track of the connection to the switch so that we can
        # send it messages!
        self.connection = connection

        # This binds our PacketIn event listener
        connection.addListeners(self)

        # add switch rules here
        self.setup_firewall()
    
    def setup_firewall(self):
        """
        Create firewall rules to allow ICMP and ARP traffic and block all other types.
        """
        # Rule to allow ICMP traffic
        icmp_rule = of.ofp_flow_mod()
        icmp_rule.match.dl_type = ethernet.IP_TYPE
        icmp_rule.match.nw_proto = ipv4.ICMP_PROTOCOL
        icmp_rule.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
        self.connection.send(icmp_rule)

        # Rule to allow ARP traffic
        arp_rule = of.ofp_flow_mod()
        arp_rule.match.dl_type = ethernet.ARP_TYPE
        arp_rule.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
        self.connection.send(arp_rule)

        # Rule to drop all other traffic
        drop_rule = of.ofp_flow_mod()
        drop_rule.priority = 1 
        drop_rule.actions = [] # drop
        self.connection.send(drop_rule)

    def _handle_PacketIn(self, event):
        """
        Packets not handled by the router rules will be
        forwarded to this method to be handled by the controller
        """

        packet = event.parsed  # This is the parsed packet data.
        if not packet.parsed:
            log.warning("Ignoring incomplete packet")
            return

        packet_in = event.ofp  # The actual ofp_packet_in message.
        print("Unhandled packet :" + str(packet.dump()))


def launch():
    """
    Starts the component
    """

    def start_switch(event):
        log.debug("Controlling %s" % (event.connection,))
        Firewall(event.connection)

    core.openflow.addListenerByName("ConnectionUp", start_switch)
