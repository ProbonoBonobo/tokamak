print(__name__)
if __name__ == '__main__':
    with open("demo.py", "r") as f:
        exec(f.read(), globals())
