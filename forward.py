import select,socket,socketserver,sys
upstream_port=int(sys.argv[1]);listen=int(sys.argv[2])
class Forward(socketserver.BaseRequestHandler):
    def handle(self):
        with socket.create_connection(('127.0.0.1',upstream_port)) as u:
            peers=[self.request,u]
            while True:
                ready,_,_=select.select(peers,[],[],300)
                if not ready:return
                for p in ready:
                    d=p.recv(65536)
                    if not d:return
                    (u if p is self.request else self.request).sendall(d)
socketserver.ThreadingTCPServer.allow_reuse_address=True
socketserver.ThreadingTCPServer(('0.0.0.0',listen),Forward).serve_forever()
