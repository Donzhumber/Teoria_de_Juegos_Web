import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.filters.hp_filter import hpfilter
from scipy.signal import butter, filtfilt
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

def apply_butterworth_lowpass(series, cutoff_period=5, fs=1, order=2):
    """
    Apply Butterworth Low-Pass Filter.
    cutoff_period: Period in quarters (e.g., 5 quarters).
    fs: Sampling frequency (1 per quarter).
    order: Filter order.
    """
    nyquist = 0.5 * fs
    normal_cutoff = (1 / cutoff_period) / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    smoothed = filtfilt(b, a, series)
    return smoothed

def analyze_gdp_enhanced():
    # Load the dataset
    file_path = 'PIB_Trimestral_Colombia.xlsx'
    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return

    # Check for expected columns
    if 'Quarter' not in df.columns or 'pib_cosntantes_2015' not in df.columns:
        print("Error: The expected columns 'Quarter' and 'pib_cosntantes_2015' are not present.")
        return

    # Convert Quarter to datetime
    try:
        df['Quarter'] = df['Quarter'].str.replace(r'(\d{4})q(\d)', r'\1Q\2', regex=True)
        df['Date'] = pd.PeriodIndex(df['Quarter'], freq='Q').to_timestamp()
        df.set_index('Date', inplace=True)
    except Exception as e:
        print(f"Error parsing dates: {e}")
        return

    gdp_series = df['pib_cosntantes_2015']
    
    # 1. Log Transformation (Stabilize Variance)
    log_gdp = np.log(gdp_series)

    # 2. Enhanced Smoothing: Butterworth Low-Pass Filter
    # Cutoff period = 12 quarters (3 years) to remove medium-term fluctuations
    smoothed_log_gdp = apply_butterworth_lowpass(log_gdp, cutoff_period=12)
    
    # Convert back to levels for visualization
    smoothed_gdp_levels = np.exp(smoothed_log_gdp)
    
    # 3. Cycle Extraction: HP Filter on the Smoothed Series
    # Lambda = 1600 (standard for quarterly data)
    # We apply HP to the *Smoothed Log GDP* to get the cycle in log-deviation units
    cycle_log, trend_log = hpfilter(smoothed_log_gdp, lamb=1600)
    
    # 4. Generate Plots
    
    # Plot 1: Original vs "Ultra-Smoothed" GDP (Levels)
    plt.figure(figsize=(14, 7))
    plt.plot(gdp_series, label='Original GDP (Constant 2015 prices)', color='lightgray', linewidth=2)
    plt.plot(gdp_series.index, smoothed_gdp_levels, label='Enhanced Smoothed GDP (Butterworth Low-Pass)', color='blue', linewidth=2.5)
    plt.title('Colombia Quarterly GDP: Original vs Enhanced Smoothing')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('gdp_smoothed_comparison.png')
    print("Smoothed GDP comparison plot saved to 'gdp_smoothed_comparison.png'.")

    # Plot 2: Final Cycle Component (Log-Deviation)
    # This represents the % deviation from the trend
    plt.figure(figsize=(14, 7))
    
    # Define crisis periods for shading (1977-2024)
    recessions = [
        ('1980-01-01', '1983-06-30', '1980-1983'),
        ('1991-01-01', '1991-12-31', '1991'),
        ('1996-01-01', '1997-12-31', '1996-1997'),
        ('1998-07-01', '1999-12-31', '1998-1999'),
        ('2008-10-01', '2009-06-30', '2008-2009'),
        ('2020-01-01', '2020-12-31', '2020')
    ]
    
    # Add shaded regions
    for start, end, label in recessions:
        # Check if dates are within the data range to avoid errors or empty plots
        start_date = pd.to_datetime(start)
        end_date = pd.to_datetime(end)
        if start_date >= gdp_series.index.min() and end_date <= gdp_series.index.max():
             # Shading
             plt.axvspan(start_date, end_date, color='gray', alpha=0.2)
             # Add text label centered in the band (Years)
             mid_point = start_date + (end_date - start_date) / 2
             # Place label slightly above or below to avoid clutter if needed, or just centered
             plt.text(mid_point, cycle_log.min()*0.95, label, rotation=90, verticalalignment='bottom', horizontalalignment='center', fontsize=8, color='dimgray', fontweight='bold')

    plt.plot(gdp_series.index, cycle_log, label='Cycle Component (HP on Smoothed GDP)', color='crimson', linewidth=2)
    plt.axhline(0, color='black', linewidth=0.8, linestyle='--')
    plt.title('Final Cycle Component (Log-Deviation)\nDerived from Enhanced Smoothed GDP with Crisis Periods')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('final_cycle.png')
    print("Final cycle plot saved to 'final_cycle.png'.")

if __name__ == "__main__":
    analyze_gdp_enhanced()
