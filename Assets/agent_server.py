from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import json
import threading
from Assets.agent_warehouse import WarehouseModel, WarehouseAgent, WarehouseObject, WarehouseStack

simulation_state = None


class Server(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n",
                     str(self.path), str(self.headers))
        response_data = get_response()
        self._set_response()
        self.wfile.write(json.dumps(response_data).encode('utf-8'))

    def do_PUT(self):
        content_length = int(self.headers['Content-Length'])
        put_data = json.loads(self.rfile.read(content_length))
        logging.info("PUT request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                     str(self.path), str(self.headers), json.dumps(put_data))

        response_data = put_response(put_data)

        self._set_response()
        self.wfile.write(json.dumps(response_data).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = json.loads(self.rfile.read(content_length))
        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                     str(self.path), str(self.headers), json.dumps(post_data))

        response_data = post_response(post_data)

        self._set_response()
        self.wfile.write(json.dumps(response_data).encode('utf-8'))


def run(server_class=HTTPServer, handler_class=Server, port=8585):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info("Starting httpd...\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info("Stopping httpd...\n")


def post_response(data):
    global simulation_state
    if 'init' in data and data['init']:
        parameters = {
            'M': data.get('M', 20),
            'N': data.get('N', 20),
            'drone_x': data.get('x', 10),
            'drone_y': data.get('y', 10),
            'cameras': data.get('cameras', 2),
            'patrol_route': data.get('patrol_route', [(10, 10), (10, 15), (15, 15), (15, 10)]),
        }
        simulation_state = WarehouseModel(parameters)
        simulation_state.setup()
        return {"message": "Simulation initialized"}
    return {"message": "Use GET request to step through simulation"}


def put_response(data):
    global simulation_state
    if ('step' in data and data['step']) and ('alert' in data and 'location' in data):
        response_data = get_response(data['alert'], data['location'])
        return response_data
    return {"error": "Invalid PUT request"}


def get_response(alert, location):
    global simulation_state
    if simulation_state is None:
        return {"error": "Simulation not initialized. Send a POST request to initialize."}

    step_result = simulation_state.step(alert, location)
    if step_result is None:
        return {"message": "Simulation complete"}
    else:
        return {
            "step": simulation_state.steps,
            "positions": step_result
        }


if __name__ == '__main__':
    from sys import argv
    run()
