"""Main entry point."""

import logging
from default_argparse import parser
from app import app
import pages

if __name__ == '__main__':
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=80,
        help='The port to run the server from'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='The host to run the server on'
    )
    args = parser.parse_args()
    logging.basicConfig(
        stream=args.log_file,
        level=args.log_level,
        format=args.log_format
    )
    logging.info('Serving pages from %r.', pages)
    app.run(
        port=args.port,
        host=args.host,
        debug=args.debug
    )
