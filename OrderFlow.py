import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class OrderFlow():
    def __init__(self, volume_bucket=10000, rolling_window=20):
        self.li_dfs = []
        self.li_nps = []
        # ts_event :: time of event nanosecond
        # action :: (A or C or T) Add or Cancel or Trade
        # side :: (A or B) Ask or Bid
        self.cols = ['action', 'side', 'price', 'size', 'bid_px_00', 'ask_px_00']
        self.volume_bucket = volume_bucket  # Volume threshold per VPIN calculation
        self.rolling_window = rolling_window  # Number of VPIN values to average


    def load_data_file(self, file_path):
        df = pd.read_csv(file_path)
        self.li_dfs.append(df)


    def populate_nps(self):
        li_temp = []
        for df in self.li_dfs:
            df1 = df[self.cols]
            li_temp.append(df1)

        for df in li_temp:
            arr = df.to_numpy()
            self.li_nps.append(arr)


    def vpin(self, buy_volume, sell_volume):
        return abs(buy_volume - sell_volume) / (buy_volume + sell_volume)


    def midPoint_orderflow(self):
        data = self.li_nps[0]
        cum_buy = 0
        cum_sell = 0
        volume_counter = 0  # Tracks total volume in the bucket
        last_trade_price = 0

        visulizer = np.zeros((data.shape[0], 4))
        vpin_values = []

        for i in range(data.shape[0]):
            if data[i, 0] == "T" and data[i, 3] >= 100:  # Process only trades
                bid_price = data[i, 4]
                ask_price = data[i, 5]
                trade_price = data[i, 2]
                trade_size = data[i, 3]

                # Correct midpoint calculation
                mid_point = (bid_price + ask_price) / 2

                # Classify trade using tick rule
                if trade_price > mid_point:
                    cum_buy += trade_size
                elif trade_price < mid_point:
                    cum_sell += trade_size
                elif last_trade_price != 0:
                    if trade_price > last_trade_price:
                        cum_buy += trade_size
                    elif trade_price < last_trade_price:
                        cum_sell += trade_size

                last_trade_price = trade_price
                volume_counter += trade_size

                # Compute VPIN when volume bucket is filled
                if volume_counter >= self.volume_bucket:
                    current_vpin = self.vpin(cum_buy, cum_sell)
                    vpin_values.append(current_vpin)

                    # Reset for next bucket
                    cum_buy = 0
                    cum_sell = 0
                    volume_counter = 0  # Reset volume counter

                # Rolling average of VPIN
                if len(vpin_values) >= self.rolling_window:
                    rolling_vpin = np.mean(vpin_values[-self.rolling_window:])
                else:
                    rolling_vpin = np.mean(vpin_values)

                visulizer[i, 0] = rolling_vpin
                visulizer[i, 1] = trade_price
                visulizer[i, 2] = bid_price
                visulizer[i, 3] = ask_price
            else:
                visulizer[i, 0] = visulizer[i - 1, 0] if i > 0 else 0
                visulizer[i, 1] = 0
                visulizer[i, 2] = data[i, 4]  # bid
                visulizer[i, 3] = data[i, 5]  # ask

        return visulizer


    def lastTrade_orderflow(self):
        pass


    def bidAsk_orderflow(self):
        pass


if __name__ == "__main__":
    of = OrderFlow(volume_bucket=10000, rolling_window=20)
    
    of.load_data_file("C:\\Projects\\SecData\\TSLA-24_1_1-24_11_22\\xnas-itch-20240108.mbp-1.csv")
    of.populate_nps()
    visual = of.midPoint_orderflow()


    visual = np.ma.masked_where(visual == 0, visual)
    plt.plot(np.zeros(visual.shape[0]), color="red")
    plt.plot(np.ones(visual.shape[0]), color="pink")
    plt.plot(np.zeros(visual.shape[0]) + 0.5, color="grey")
    plt.plot(visual[:, 0], label="VPIN")
    plt.plot(visual[:, 1] - 240, marker="x")
    plt.plot(visual[:, 2:4] - 240)
    plt.xlabel("Trade Index")
    plt.ylabel("VPIN")
    plt.title("VPIN Over Time")
    plt.legend()
    plt.show()
