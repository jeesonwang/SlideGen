from slidegen.base import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.server:app", host="0.0.0.0", port=7860, reload=True)
