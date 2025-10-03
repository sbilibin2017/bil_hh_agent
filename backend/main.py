from backend.app.app import App


def main():
    app = App()
    app.parse_args()
    app.parse_config()
    app.configure_logging()
    app.create_app()
    app.run_uvicorn()


if __name__ == "__main__":
    main()
