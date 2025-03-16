import alphalens
print(alphalens.__version__)


print("Factor Values Data Types:")
print(factor_values.dtypes)
print("\nAligned Prices Data Types:")
print(aligned_prices.dtypes)



import yfinance as yf
import pandas as pd
import numpy as np
import alphalens as al

def fetch_data(tickers, start_date, end_date):
    try:
        data = yf.download(tickers, start=start_date, end=end_date)
        return data
    except Exception as e:
        print(f"Error fetching data: {e}")
        raise

def calculate_momentum(prices, window):
    try:
        momentum = prices.pct_change(periods=window).shift(-window)
        return momentum
    except Exception as e:
        print(f"Error calculating momentum: {e}")
        raise

def main(tickers, start_date, end_date, momentum_window):
    try:
        data = fetch_data(tickers, start_date, end_date)

        # Consolidating 'Adj Close' prices into a DataFrame
        prices = pd.concat([data[ticker]['Adj Close'].ffill() if 'Adj Close' in data[ticker].columns else pd.Series() for ticker in tickers], axis=1, keys=tickers)

        # Check for missing values in the prices DataFrame
        if prices.isnull().values.any():
            print("Warning: Missing values found in the prices DataFrame.")

        momentum = calculate_momentum(prices, momentum_window)

        if momentum.isnull().all().all():
            raise ValueError("All momentum calculations resulted in NaNs.")

        # Creating a MultiIndex for factor values
        factor_index = pd.MultiIndex.from_product([momentum.index, momentum.columns], names=['date', 'asset'])
        factor_values = pd.Series(momentum.stack(), index=factor_index, name='momentum').to_frame()

        # Aligning price data
        aligned_prices = prices.stack().reindex(factor_index).unstack()

        # Check index alignment
        if not factor_values.index.equals(aligned_prices.index.get_level_values(0)):
            print("Mismatch in indices detected:")
            print("Factor Index Sample:", factor_values.index[:5])
            print("Price Data Index Sample:", aligned_prices.index.get_level_values(0)[:5])
            raise ValueError("Indices of factor data and price data do not match.")

        # Print intermediate variables for debugging
        print("Factor Values:")
        print(factor_values.head())
        print("\nAligned Prices:")
        print(aligned_prices.head())

        # Get clean factor and forward returns
        factor_data = al.utils.get_clean_factor_and_forward_returns(
            factor_data=factor_values['momentum'],
            prices=aligned_prices,
            periods=[1, 5, 10],
            max_loss=0.5
        )

        # Create full tear sheet
        al.tears.create_full_tear_sheet(factor_data)

    except Exception as e:
        print(f"Error in analysis: {e}")

# Parameters and function call
tickers = ["AAPL"]
start_date = "2020-01-01"
end_date = "2023-01-01"
momentum_window = 90

# Run the analysis
main(tickers, start_date, end_date, momentum_window)