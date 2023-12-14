Name: Adrien Delepine
UWNetID: adriende

Name: Sebastian Liu
UWNetID: ll57

Name: Andrew Wu
UWNetID: andrew64

Instructions to reproduce the results:
Run 'sudo ./run.sh' to run using TCP Reno and output the graphs and webpage fetch time info.
Likewise, for TCP BBR run 'sudo ./run_bbr.sh'.

Answers to the questions:

Part 2

1. When q=20, the average webpage fetch time was 0.496 seconds with a standard deviation 
   of 0.596 seconds. When q=100, the average fetch time was 1.283 seconds with a standard 
   deviation of 0.244 seconds.

2. This occurs because of Bufferbloat, a phenomenon where buffers are too large, e.g. q=100
   versus a size of q=20 and this leads to packets building up within the
   buffers instead of being dropped, and this messes up TCP's congestion detection mechanism 
   and makes them not trigger. All the client sees is high latency from its perspective as 
   the packets slowly drain from the buffer and are delivered at higher latencies.

3. The maximum possible transmit queue length is 1000 packets, the value of txqueuelen when
   ifconfig is run. Assuming the queue drains is 100Mb/s and with an MTU of 1500 bytes, we
   can find the maximum time a packet might wait in the queue before it leaves the NIC by
   doing (queue length * packet size) / transmission rate. We get 
   (1000 * 1500 bytes) / 100 Mb/s = 12,000,000 bits / 100,000,000 bits/s = 0.2 seconds.

4. The RTT reported by ping grows proportionally to the queue size. As queue size gets
   bigger, the RTT times increase.

5. The problem of bufferbloat could be solved either by reducing buffer sizes all around,
   which would require a concerted effort in multiple places such as OS etc. NIC cards 
   routers or have an approach where whenever you have a big queue, you notify
   one or more of the endpoints so they can decrease their window size.


Part 3

1. When q=20, the average webpage fetch time was 0.403 seconds with a standard deviation of
   0.619 seconds. When q=100, the average fetch time was 0.307 seconds with a standard
   deviation of 0.696 seconds.

2. The queue length of 100 gives a lower fetch time, very different from Part 2 where
   because of the TCP protocol we used the bigger the queue length the higher the latency.

3. Yes, the TCP-BBR protocol is vastly better at keeping queues as empty as possible
   throughout the sending of packets. It does this by actively adjusting the rate at
   which it sends packets based on what it knows the RTT and bandwidth are at the moment,
   keeping queues as empty as possible.

4. I'd say bufferbloat is mostly mitigated for now, but this doesn't mean that it can't
   pop up in the future, especially since networking is such a constantly changing and 
   decentralized field. The TCP BBR developed by google effectively mitigates the problem
   is what I would say.
