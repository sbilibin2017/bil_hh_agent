from app import app

if __name__ == "__main__":
    args = app.parse_env_file_arg()
    cfg = app.load_config_from_env_file(args.env_file)
    app.configure_logging(cfg)
    server = app.create_app(cfg)
    app.run_uvicorn(server, cfg)
