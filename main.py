if __name__ == "__main__":
    import uvicorn

    uvicorn.run("slidegen.server:app", host="127.0.0.1", port=10003, reload=True)
