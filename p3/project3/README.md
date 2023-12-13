Name: Adrien Delepine
UWNetID: adriende

Name: Sebastian Liu
UWNetID: ll57

Name: Andrew Wu
UWNetID: andrew64

Instructions to reproduce the results:
Run 'sudo ./run.sh' to run using TCP Reno and output the graphs and webpage fetch time info. Likewise, for TCP BBR run 'sudo ./run_bbr.sh'.

Answers to the questions:

Part 2

1. When q=20, the average webpage fetch time was 0.496 seconds with a standard deviation of 0.596 seconds. When q=100, the average fetch time was 1.283 seconds with a standard deviation of 0.244 seconds.
2. This occurs because of Bufferbloat, a phenomenon where buffers are too large, e.g. q=100 versus a size of q=20 and this leads to packets building up within the
   buffers instead of being dropped, and this messes up TCP's congestion detection mechanism and makes them not trigger. All the client sees is high latency from its perspective as the packets slowly drain from the buffer and are delivered at higher latencies.

3. TODO

4. The RTT reported by ping grows proportionally to the queue size. As queue size gets bigger, the RTT times increase.
5. The problem of bufferbloat could be solved either by reducing buffer sizes all around, which would require a concerted effort in multiple places such as OS etc. NIC cards routers or have an approach where whenever you have a big queue, you notify
   one or more of the endpoints so they can decrease their window size.

Part 3

1. When q=20, the average webpage fetch time was 0.403 seconds with a standard deviation of 0.619 seconds. When q=100, the average fetch time was 0.307 seconds with a standard deviation of 0.696 seconds.
2. TODO
3. TODO
