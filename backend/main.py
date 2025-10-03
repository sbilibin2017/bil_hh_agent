from backend.app.app import App


if __name__ == "__main__":
    application = App()
    args = application.parse_args()
    application.parse_envs(args.env_file)
    application.configure_logging()
    application.configure_app()
    application.run_uvicorn()
