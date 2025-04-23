from src.globe_sim import GlobeSim

if __name__ == "__main__":
    app = GlobeSim()
    base.setFrameRateMeter(True)
    app.run()