"""A demo which runs object classification and streams video to the browser."""

#export TEST_DATA=/usr/lib/python3.5/dist-packages/edgetpu/test_data/
#
# python3 classify_server.py \
#   --model=${TEST_DATA}/mobilenet_v1_1.0_224_quant_edgetpu.tflite \
#   --labels=${TEST_DATA}/imagenet_labels.txt

import argparse
import logging
import signal
import time

from edgetpu.classification.engine import ClassificationEngine

from . import overlays
from .camera import InferenceCamera
from .streaming.server import StreamingServer
from .utils import load_labels


def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--model', required=True,
                        help='.tflite model path.')
    parser.add_argument('--labels', required=True,
                        help='label file path.')
    parser.add_argument('--top_k', type=int, default=3,
                        help='number of classes with highest score to display.')
    parser.add_argument('--threshold', type=float, default=0.1,
                        help='class score threshold.')
    args = parser.parse_args()

    engine = ClassificationEngine(args.model)
    labels = load_labels(args.labels)

    _, h, w, _ = engine.get_input_tensor_shape()

    camera = InferenceCamera((640, 360), (w, h))
    with StreamingServer(camera) as server:
        def on_image(rgb, inference_fps, size, view_box):
            start = time.monotonic()
            results = engine.ClassifyWithInputTensor(rgb, threshold=args.threshold, top_k=args.top_k)
            inference_time = time.monotonic() - start

            results = [(labels[i], score) for i, score in results]
            server.send_overlay(overlays.classification(results, inference_time, inference_fps, size, view_box))

        camera.on_image = on_image
        signal.pause()

if __name__ == '__main__':
    main()
