from src import GlobeSim

if __name__ == "__main__":
    app = GlobeSim(useTk=True)
    base.setFrameRateMeter(True)
    app.run()