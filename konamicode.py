import os

from tornado.websocket import WebSocketHandler
from tornado.web import RequestHandler, StaticFileHandler, Application, url
from tornado.escape import json_decode
from tornado import ioloop
from rx import operators as ops
from rx.subject import Subject

UP, DOWN, LEFT, RIGHT, B, A = 38, 40, 37, 39, 66, 65
codes = [UP, UP, DOWN, DOWN, LEFT, RIGHT, LEFT, RIGHT, B, A]


class WSHandler(WebSocketHandler):
    def open(self):
        print("WebSocket aberto")

        # Um Sujeito é observável e observador, portanto, podemos nos inscrever
        # para ele e também alimentá-lo (on_next) com novos valores
        self.subject = Subject()

        # Agora pegamos nossos óculos mágicos e projetamos o fluxo de bytes em
        query = self.subject.pipe(
            # 1. fluxo de códigos-chave
            ops.map(lambda obj: obj["keycode"]),
            # 2. fluxo de janelas (10 ints de comprimento)
            ops.window_with_count(10, 1),
            # 3. fluxo de booleanos, verdadeiro ou falso
            ops.flat_map(lambda win: win.pipe(ops.sequence_equal(codes))),
            # 4. fluxo de verdadeiras
            ops.filter(lambda equal: equal)
        )
        # 4. então, assinamos o Trues e sinalizamos para a Konami! se virmos algum
        query.subscribe(lambda x: self.write_message("Konami!"))

    def on_message(self, message):
        obj = json_decode(message)
        self.subject.on_next(obj)

    def on_close(self):
        print("WebSocket fechado")


class MainHandler(RequestHandler):
    def get(self):
        self.render("index.html")


def main():
    port = os.environ.get("PORT", 8080)
    app = Application([
        url(r"/", MainHandler),
        (r'/ws', WSHandler),
        (r'/static/(.*)', StaticFileHandler, {'path': "."})
    ])
    print("Iniciando servidor na porta: %s" % port)
    app.listen(port)
    ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()
