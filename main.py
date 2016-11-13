"""Main entry point."""

if __name__ == '__main__':
    from default_argparse import parser
    args = parser.parse_args()
    import logging
    logging.basicConfig(stream = args.log_file, level = args.log_level, format = args.log_format)
    from pyjay import application, config
    from pyjay.ui import MainFrame
    frame = MainFrame(None, title = application.app.GetAppName())
    application.app.MainLoop()
    import os, os.path
    if not os.path.isdir(application.config_dir):
        logging.info('Creating config directory: %s.', application.config_dir)
        os.makedirs(application.config_dir)
    config.config.write(indent = 1)
    logging.info('Main loop finished.')
