# 註解: 此程式碼用於根據給定的 Air2 和 T2 值，使用預先訓練的多項式回歸模型來預測總硫含量（Total S）。程式碼從 CSV 文件中讀取回歸係數，並提供一個互動式命令行界面，允許用戶輸入 Air2 和 T2 值以獲取預測結果。
import pandas as pd

# --- Settings ---
PROJECT_NAME = 'senpai_data'
coef_file = f'csv/{PROJECT_NAME}/regression_coefficients.csv'

# Load coefficients
df_coef = pd.read_csv(coef_file)

# Extract intercept and coefficients
intercept = df_coef[df_coef['Feature'] == 'Intercept']['Coefficient'].values[0]
coef_data = df_coef[df_coef['Feature'] != 'Intercept']

def predict_totalS(air2, t2):
    """
    Predict Total S given Air2 and T2 values
    
    Parameters:
    -----------
    air2 : float
        Air2 flow rate [m³/h]
    t2 : float
        T2 temperature [°C]
    
    Returns:
    --------
    float
        Predicted Total S [%]
    """
    # Calculate polynomial features
    features = {
        'Air2': air2,
        'T2': t2,
        'Air2^2': air2**2,
        'Air2 T2': air2 * t2,
        'T2^2': t2**2,
        'Air2^3': air2**3,
        'Air2^2 T2': air2**2 * t2,
        'Air2 T2^2': air2 * t2**2,
        'T2^3': t2**3,
        'Air2^4': air2**4,
        'Air2^3 T2': air2**3 * t2,
        'Air2^2 T2^2': air2**2 * t2**2,
        'Air2 T2^3': air2 * t2**3,
        'T2^4': t2**4
    }
    
    # Calculate prediction
    total_S = intercept
    for _, row in coef_data.iterrows():
        total_S += row['Coefficient'] * features[row['Feature']]
    
    return total_S


# ========== Interactive Mode ==========
print(f"{'='*60}")
print(f"TOTAL S PREDICTOR")
print(f"{'='*60}")
print(f"Loaded regression model from: {coef_file}")
print(f"\nEnter Air2 and T2 values to predict Total S")
print(f"(Type 'quit' or 'exit' to stop)\n")

while True:
    try:
        # Get user input for Air2
        air2_input = input("Enter Air2 [m³/h]: ").strip()
        if air2_input.lower() in ['quit', 'exit', 'q']:
            print("\nExiting...")
            break
        
        air2 = float(air2_input)
        
        # Get user input for T2
        t2_input = input("Enter T2 [°C]: ").strip()
        if t2_input.lower() in ['quit', 'exit', 'q']:
            print("\nExiting...")
            break
        
        t2 = float(t2_input)
        
        # Calculate prediction
        result = predict_totalS(air2, t2)
        
        # Display result
        print(f"\n{'─'*60}")
        print(f"  Air2 = {air2} m³/h")
        print(f"  T2 = {t2} °C")
        print(f"  → Predicted Total S = {result:.6f}%")
        print(f"{'─'*60}\n")
        
    except ValueError:
        print("❌ Invalid input. Please enter numeric values.\n")
    except KeyboardInterrupt:
        print("\n\nExiting...")
        break
    except Exception as e:
        print(f"❌ Error: {e}\n")

print(f"\n{'='*60}")
print(f"Thank you for using the Total S Predictor!")
print(f"{'='*60}")
