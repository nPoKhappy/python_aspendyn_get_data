# 註解: 此程式碼用於從指定的 CSV 文件中讀取數據，並使用多項式回歸模型來擬合 Total S 與 Air2 和 T2 之間的關係。程式碼包括模型訓練、性能評估、3D 可視化以及將回歸係數保存到 CSV 文件中的功能。
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import r2_score, mean_squared_error
import os

# --- Settings ---
PROJECT_NAME = 'senpai_data'
csv_file = os.path.join('csv', PROJECT_NAME, 'fig_8.csv')

# Check if file exists
if not os.path.exists(csv_file):
    print(f"Error: Cannot find file '{csv_file}'")
    print("Please confirm the file path is correct.")
else:
    print(f"Reading file: {csv_file}")
    
    # Read CSV file
    df = pd.read_csv(csv_file)
    
    # Extract data
    X_air2 = df['Air2 [m³/h]'].values
    X_t2 = df['T2 [℃]'].values
    y_totalS = df['total S[%]'].values
    
    # Combine into feature matrix
    X = np.column_stack([X_air2, X_t2])
    
    print(f"\n{'='*60}")
    print(f"DATA SUMMARY")
    print(f"{'='*60}")
    print(f"Number of samples: {len(X)}")
    print(f"Air2 range: {X_air2.min():.2f} - {X_air2.max():.2f} m³/h")
    print(f"T2 range: {X_t2.min():.2f} - {X_t2.max():.2f} °C")
    print(f"Total S range: {y_totalS.min():.6f} - {y_totalS.max():.6f} %")
    
    # ========== Polynomial Regression ==========
    print(f"\n{'='*60}")
    print(f"TRAINING POLYNOMIAL REGRESSION MODELS")
    print(f"{'='*60}")
    
    models = {}
    predictions = {}
    scores = {}
    
    # Try different polynomial degrees
    degrees = [1, 2, 3, 4]
    
    for degree in degrees:
        print(f"\nDegree {degree}:")
        
        # Create polynomial features
        poly = PolynomialFeatures(degree=degree, include_bias=False)
        X_poly = poly.fit_transform(X)
        
        print(f"  Number of features: {X_poly.shape[1]}")
        print(f"  Feature names: {poly.get_feature_names_out(['Air2', 'T2'])[:10]}...")
        
        # Train model
        model = Ridge(alpha=0.1)  # Use Ridge to prevent overfitting
        model.fit(X_poly, y_totalS)
        
        # Make predictions
        y_pred = model.predict(X_poly)
        
        # Calculate metrics
        r2 = r2_score(y_totalS, y_pred)
        rmse = np.sqrt(mean_squared_error(y_totalS, y_pred))
        
        print(f"  R² score: {r2:.6f}")
        print(f"  RMSE: {rmse:.8f}")
        
        # Store results
        models[degree] = (poly, model)
        predictions[degree] = y_pred
        scores[degree] = r2
    
    # ========== Select Best Model ==========
    best_degree = max(scores, key=scores.get)
    best_poly, best_model = models[best_degree]
    
    print(f"\n{'='*60}")
    print(f"BEST MODEL: Degree {best_degree} (R² = {scores[best_degree]:.6f})")
    print(f"{'='*60}")
    
    # ========== Visualization ==========
    
    # Create a fine grid for smooth surface
    air2_range = np.linspace(X_air2.min(), X_air2.max(), 100)
    t2_range = np.linspace(X_t2.min(), X_t2.max(), 100)
    Air2_grid, T2_grid = np.meshgrid(air2_range, t2_range)
    
    # Prepare grid for prediction
    grid_points = np.column_stack([Air2_grid.ravel(), T2_grid.ravel()])
    grid_poly = best_poly.transform(grid_points)
    TotalS_pred = best_model.predict(grid_poly).reshape(Air2_grid.shape)
    
    # ========== 3D Plot: Actual Data Points and Fitted Surface ==========
    fig1 = plt.figure(figsize=(16, 6))
    
    # Left: Fitted surface with data points
    ax1 = fig1.add_subplot(1, 2, 1, projection='3d')
    
    # Plot fitted surface
    surf = ax1.plot_surface(Air2_grid, T2_grid, TotalS_pred, cmap='RdYlGn_r', 
                           alpha=0.7, linewidth=0, antialiased=True)
    
    # Plot actual data points
    scatter = ax1.scatter(X_air2, X_t2, y_totalS, c='blue', s=50, 
                         edgecolors='black', linewidth=1, label='Actual Data')
    
    ax1.set_xlabel('Air2 [m³/h]', fontsize=11, labelpad=8)
    ax1.set_ylabel('T2 [°C]', fontsize=11, labelpad=8)
    ax1.set_zlabel('Total S [%]', fontsize=11, labelpad=8)
    ax1.set_title(f'Polynomial Regression (Degree {best_degree})\nFitted Surface with Data Points', 
                 fontsize=13, fontweight='bold')
    ax1.view_init(elev=25, azim=45)
    ax1.legend()
    
    cbar1 = fig1.colorbar(surf, ax=ax1, shrink=0.5)
    cbar1.set_label('Predicted Total S [%]', fontsize=10)
    
    # Right: Residuals visualization
    ax2 = fig1.add_subplot(1, 2, 2, projection='3d')
    
    # Calculate residuals
    y_pred_best = predictions[best_degree]
    residuals = y_totalS - y_pred_best
    
    # Plot residuals as vertical lines
    for i in range(len(X_air2)):
        ax2.plot([X_air2[i], X_air2[i]], [X_t2[i], X_t2[i]], 
                [y_totalS[i], y_pred_best[i]], 'r-', alpha=0.3)
    
    # Plot predicted surface
    ax2.plot_surface(Air2_grid, T2_grid, TotalS_pred, cmap='RdYlGn_r', 
                    alpha=0.5, linewidth=0)
    
    # Plot actual points
    ax2.scatter(X_air2, X_t2, y_totalS, c='blue', s=50, 
               edgecolors='black', linewidth=1, label='Actual')
    ax2.scatter(X_air2, X_t2, y_pred_best, c='red', s=30, 
               marker='x', linewidth=2, label='Predicted')
    
    ax2.set_xlabel('Air2 [m³/h]', fontsize=11, labelpad=8)
    ax2.set_ylabel('T2 [°C]', fontsize=11, labelpad=8)
    ax2.set_zlabel('Total S [%]', fontsize=11, labelpad=8)
    ax2.set_title(f'Residuals Visualization\nRMSE = {np.sqrt(mean_squared_error(y_totalS, y_pred_best)):.8f}', 
                 fontsize=13, fontweight='bold')
    ax2.view_init(elev=25, azim=45)
    ax2.legend()
    
    plt.tight_layout()
    save_path_3d = os.path.join('csv', PROJECT_NAME, 'regression_totalS_3D.png')
    plt.savefig(save_path_3d, dpi=300, bbox_inches='tight')
    print(f"\nSaved: {save_path_3d}")
    plt.show()
    
    # ========== Model Coefficients ==========
    print(f"\n{'='*60}")
    print(f"MODEL COEFFICIENTS (Degree {best_degree})")
    print(f"{'='*60}")
    feature_names = best_poly.get_feature_names_out(['Air2', 'T2'])
    coefficients = best_model.coef_
    
    print(f"Intercept: {best_model.intercept_:.10f}")
    print(f"\nCoefficients:")
    for name, coef in zip(feature_names, coefficients):
        print(f"  {name:15s}: {coef:15.10f}")
    
    # ========== Equation Display ==========
    print(f"\n{'='*60}")
    print(f"REGRESSION EQUATION")
    print(f"{'='*60}")
    equation = f"Total S = {best_model.intercept_:.16f}"
    for name, coef in zip(feature_names, coefficients):
        if coef >= 0:
            equation += f"\n        + {coef:.8f} * {name}"
        else:
            equation += f"\n        - {abs(coef):.8f} * {name}"
    print(equation)
    
    # ========== Save Coefficients to CSV ==========
    print(f"\n{'='*60}")
    print(f"SAVING COEFFICIENTS")
    print(f"{'='*60}")
    
    coef_save_path = os.path.join('csv', PROJECT_NAME, 'regression_coefficients.csv')
    coef_df = pd.DataFrame({
        'Feature': ['Intercept'] + list(feature_names),
        'Coefficient': [best_model.intercept_] + list(coefficients)
    })
    coef_df.to_csv(coef_save_path, index=False)
    print(f"✓ Saved coefficients: {coef_save_path}")
    
    print(f"\n{'='*60}")
    print(f"REGRESSION COMPLETE!")
    print(f"{'='*60}")
