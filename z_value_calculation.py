import numpy as np

# Sample data
sample_error_rates = [
    -17.37519361799218, -1.4490142578865954, -1.7573142896371712, 2.1931139601016225, 1.8985329771079242,
    1.1333191079412814, -14.52533284590007, -2.3146208277689877, -15.05293106835324, -15.627647094643605,
    6.661203826915057, -20.171773098886423, -11.255324285026028, -19.82983307489907, 0.20786835048006025,
    -7.054564328292599, -4.121429142768256, 2.470483049440303, -12.123734801724122, -5.35047044551818,
    -10.837189986998169, -18.443855562358507, -21.548589586645065, -9.394100385028402, -19.148931259423065,
    -5.052685445564199, -4.813305497439492, -3.685178500093568, -2.058374174521148, -12.863153824758523
]

# Calculate sample mean and standard deviation
sample_mean = np.mean(sample_error_rates)
sample_std = np.std(sample_error_rates, ddof=1)  # Using sample standard deviation

# Select significance level
alpha = 0.05

# Sample size
n = len(sample_error_rates)

# Calculate Z-value
Z = (sample_mean + 6) / (sample_std / np.sqrt(n))

print("Sample Mean (x̄):", sample_mean)
print("Sample Standard Deviation (s):", sample_std)
print("Z-value:", Z)