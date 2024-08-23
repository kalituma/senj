import numpy as np
import pandas as pd
from scipy.optimize import minimize
import matplotlib.pyplot as plt

def simulate_data(wavelengths, true_rsr):
    simulated_radiance = np.random.rand(len(wavelengths)) * true_rsr
    simulated_ground_reflectance = np.random.rand(len(wavelengths))
    simulated_transmission = 0.8 + 0.2 * np.random.rand(len(wavelengths))
    simulated_path_radiance = 0.1 * np.random.rand(len(wavelengths))

    return simulated_radiance, simulated_ground_reflectance, simulated_transmission, simulated_path_radiance

def rsr_model(wavelengths, params):
    center, width, amplitude = params
    return amplitude * np.exp(-((wavelengths - center) ** 2) / (2 * width ** 2))

def objective_function(params, wavelengths, observed_radiance, ground_reflectance, transmission, path_radiance):
    modeled_rsr = rsr_model(wavelengths, params)
    estimated_radiance = (ground_reflectance * transmission * modeled_rsr) + (path_radiance * modeled_rsr)
    return np.sum((observed_radiance - estimated_radiance) ** 2)

def estimate_rsr(wavelengths, observed_radiance, ground_reflectance, transmission, path_radiance):
    initial_guess = [np.mean(wavelengths), 50, 1]

    result = minimize(objective_function, initial_guess,
                      args=(wavelengths, observed_radiance, ground_reflectance, transmission, path_radiance),
                      method='Nelder-Mead')

    return result.x

def main():

    wavelengths = np.linspace(400, 1000, 100)

    true_rsr = rsr_model(wavelengths, [700, 50, 1])

    observed_radiance, ground_reflectance, transmission, path_radiance = simulate_data(wavelengths, true_rsr)

    # RSR 추정
    estimated_params = estimate_rsr(wavelengths, observed_radiance, ground_reflectance, transmission, path_radiance)
    estimated_rsr = rsr_model(wavelengths, estimated_params)

    # 결과 시각화
    plt.figure(figsize=(10, 6))
    plt.plot(wavelengths, true_rsr, label='True RSR')
    plt.plot(wavelengths, estimated_rsr, label='Estimated RSR')
    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Relative Response')
    plt.legend()
    plt.title('True vs Estimated RSR')
    plt.show()

    print(
        f"Estimated RSR parameters: Center = {estimated_params[0]:.2f}, Width = {estimated_params[1]:.2f}, Amplitude = {estimated_params[2]:.2f}")


if __name__ == "__main__":
    main()