from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import json
import threading
from agent_warehouse import WarehouseModel

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
    parameters = {
        'M': data.get('M', 20),
        'N': data.get('N', 20),
        'drones': data.get('drones', 2),
        'drone_positions': data.get('drone_positions', [(3, 3), (4, 9)]),
        'patrol_routes': data.get('patrol_routes', [[(4, 4), (16, 16)], [(3, 1), (5, 4)]]),
        'cameras': data.get('cameras', 2),
        'guards': data.get('guards', 1),
        'obstacles': data.get('obstacles', [((5, 5), (15, 15))]),
    }
    try:
        simulation_state = WarehouseModel(parameters)
        simulation_state.setup()
    except Exception as e:
        return {"error": str(e)}
    return {"message": "Simulation initialized"}


def put_response(data):
    global simulation_state
    response_data = get_response(
        data.get('drone_positions', None),
        data.get('alert', False),
        data.get('target', None))
    return response_data


def get_response(drone_locations=None, alert=False, target=None):
    global simulation_state
    if simulation_state is None:
        return {"error": "Simulation not initialized. Send a POST request to initialize."}

    step_result = simulation_state.step(
        drone_locations, target=target, alert=alert)
    if step_result is None:
        return {"message": "Simulation complete"}
    else:
        path = [{'x': x[0], 'z': x[1]} for x in step_result[0]]
        print({
            "positions": path
        }
        )
        return {
            "positions": path
        }


if __name__ == '__main__':
    from sys import argv
    run()
