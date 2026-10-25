import select
import socket
import socketserver
class Forward(socketserver.BaseRequestHandler):
    def handle(self):
        with socket.create_connection(('127.0.0.1',18823)) as upstream:
            peers=[self.request,upstream]
            while True:
                readable,_,_=select.select(peers,[],[],300)
                if not readable:return
                for peer in readable:
                    data=peer.recv(65536)
                    if not data:return
                    (upstream if peer is self.request else self.request).sendall(data)
socketserver.ThreadingTCPServer.allow_reuse_address=True
socketserver.ThreadingTCPServer(('0.0.0.0',18833),Forward).serve_forever()
