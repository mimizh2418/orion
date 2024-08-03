import logging
import time

import ntcore

from .config import *
from .output import NTOutputPublisher, StreamServer
from .pipeline import *


NETWORK_CONFIG_FILE = 'network_config.json'
CALIBRATION_FILE = 'calibration.json'


def run_pipeline():
    logging.basicConfig(level=logging.DEBUG)

    config = Config()
    config.refresh_local(NETWORK_CONFIG_FILE, CALIBRATION_FILE)

    ntcore.NetworkTableInstance.getDefault().startClient4(config.network.device_id)
    ntcore.NetworkTableInstance.getDefault().setServer(config.network.server_ip)

    config.refresh_nt()

    capture = DefaultCapture(config)
    pipeline = Pipeline(config)
    output = NTOutputPublisher(config)
    stream = StreamServer(config)

    stream.start()

    last_fps_time = time.perf_counter_ns()
    fps = 0
    frame_count = 0
    heartbeat = 0

    while True:
        config.refresh_nt()

        ret, frame = capture.get_frame()
        if not ret:
            time.sleep(0.2)
            continue

        result = pipeline.process_frame(frame)

        heartbeat += 1
        frame_count += 1
        current_time = time.perf_counter_ns()
        if current_time - last_fps_time > 1e9:
            fps = frame_count / ((current_time - last_fps_time) * 1e-9)
            last_fps_time = current_time
            frame_count = 0

        output.publish(result, fps, heartbeat)
        stream.set_frame(frame.image)
